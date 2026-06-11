"""
InterSystems IRIS vector client — the ONLY file that touches the IRIS driver
or IRIS-specific SQL. Everything else in backend/vector/ stays driver-agnostic.

All connection validation, retry/backoff, table management, and the
idempotent (doc_id-keyed) write path live here so that IRIS-specific concerns
stay isolated behind a small, typed surface.

IRIS assumptions (documented per the POC brief; confirm against your IRIS
version, validated against the syntax used in the official
intersystems-community/iris-vector-search demos):

  * Driver: `intersystems-irispython` exposes a PEP-249 DB-API via
    `iris.connect(hostname, port, namespace, username, password)`. It is
    imported lazily inside `_raw_connect()` so the rest of the backend (and
    the test suite) imports cleanly even when the driver is not installed.
  * Vector column type: `VECTOR(FLOAT, <dim>)` where <dim> == EMBEDDING_DIM.
  * Insert: embeddings are passed as a comma-separated string and converted
    with `TO_VECTOR(?, FLOAT, <dim>)`.
  * Similarity: `VECTOR_COSINE(a, b)` returns higher = more similar, so we
    `ORDER BY ... DESC`. (Cosine implicitly normalises its inputs.)
  * Existence check: `INFORMATION_SCHEMA.TABLES` is queryable.
  * Idempotency: `doc_id` is the PRIMARY KEY (the invoice identifier). The
    write path deletes any existing rows for the batch's doc_ids and then
    inserts, so re-running indexing updates rows in place instead of creating
    duplicates or failing on primary-key collisions.

If any of the above differs on the target IRIS instance, this file is the only
place that needs to change.

NOTE: credentials (username/password) are read from the environment via
backend.config and are NEVER logged. Only non-secret connection coordinates
(host, port, namespace) appear in logs.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from backend.config import (
    EMBEDDING_DIM,
    IRIS_HOST,
    IRIS_NAMESPACE,
    IRIS_PASSWORD,
    IRIS_PORT,
    IRIS_PORT_RAW,
    IRIS_USERNAME,
    IRIS_VECTOR_TABLE,
)

logger = logging.getLogger("doxa.vector.iris")

# Transient-connection handling. Auth/driver problems are NOT retried (they are
# not transient); only the connect step is retried with linear backoff.
_CONNECT_RETRIES = 3
_CONNECT_BACKOFF_SECONDS = 1.5

# Default rows per DELETE+INSERT transaction. Keeps each write small and
# auditable; callers can override.
DEFAULT_INSERT_BATCH = 100


class IrisConfigError(RuntimeError):
    """Raised when required IRIS settings are missing or invalid (fail fast)."""


class IrisConnectionError(RuntimeError):
    """Raised when IRIS is unreachable or the driver is unavailable."""


@dataclass
class VectorDocument:
    """One storable record: identity, retrievable text, metadata, embedding."""

    doc_id: str
    source_table: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float]


@dataclass
class SearchRow:
    """Raw row returned by a similarity search (decoded, not yet formatted)."""

    doc_id: str
    source_table: str
    content: str
    metadata: dict[str, Any]
    score: float


def _vector_to_string(embedding: list[float]) -> str:
    """IRIS TO_VECTOR input format: 'v1,v2,v3'."""
    return ",".join(repr(float(x)) for x in embedding)


# --------------------------------------------------------------------------- #
# Configuration validation (fail fast, secret-free errors)
# --------------------------------------------------------------------------- #
def validate_config() -> None:
    """Raise ``IrisConfigError`` if any required IRIS setting is missing/invalid.

    Checks presence of host/namespace/username/password/table and the validity
    of the port. Error messages reference variable *names* only and never echo
    secret values.
    """
    missing: list[str] = []
    if not str(IRIS_HOST).strip():
        missing.append("IRIS_HOST")
    if not str(IRIS_NAMESPACE).strip():
        missing.append("IRIS_NAMESPACE")
    if not str(IRIS_USERNAME).strip():
        missing.append("IRIS_USERNAME")
    if not str(IRIS_PASSWORD):
        missing.append("IRIS_PASSWORD")
    if not str(IRIS_VECTOR_TABLE).strip():
        missing.append("IRIS_VECTOR_TABLE")

    if missing:
        raise IrisConfigError(
            "Missing required IRIS settings: "
            + ", ".join(missing)
            + ". Set them in .env / environment (values are never hardcoded)."
        )

    try:
        port = int(IRIS_PORT_RAW)
    except (TypeError, ValueError):
        raise IrisConfigError(
            "IRIS_PORT must be an integer between 1 and 65535 "
            "(received a non-numeric value)."
        ) from None
    if not (0 < port <= 65535):
        raise IrisConfigError(
            f"IRIS_PORT must be between 1 and 65535 (received {port})."
        )

    if EMBEDDING_DIM <= 0:
        raise IrisConfigError("EMBEDDING_DIM must be a positive integer.")


# --------------------------------------------------------------------------- #
# Connection management (lazy driver import + transient retry)
# --------------------------------------------------------------------------- #
def _raw_connect():
    """Open a single DB-API connection. Driver import is lazy and intentional."""
    try:
        import iris
    except ImportError as exc:  # not transient — surface immediately
        raise IrisConnectionError(
            "The 'intersystems-irispython' driver is not installed. "
            "Install it (see README / instructions.md, POC 1) before "
            "indexing or querying IRIS."
        ) from exc

    return iris.connect(
        hostname=IRIS_HOST,
        port=int(IRIS_PORT_RAW),
        namespace=IRIS_NAMESPACE,
        username=IRIS_USERNAME,
        password=IRIS_PASSWORD,
    )


def _connect():
    """Validate config, then connect with linear backoff on transient failures."""
    validate_config()

    last_exc: Exception | None = None
    for attempt in range(1, _CONNECT_RETRIES + 1):
        logger.info(
            "Connecting to IRIS at %s:%s (namespace=%s) [attempt %d/%d]",
            IRIS_HOST,
            IRIS_PORT,
            IRIS_NAMESPACE,
            attempt,
            _CONNECT_RETRIES,
        )
        try:
            conn = _raw_connect()
            logger.info("Connected to IRIS.")
            return conn
        except IrisConnectionError:
            # Driver missing — not transient, do not retry.
            raise
        except Exception as exc:  # noqa: BLE001 - driver raises varied types
            last_exc = exc
            logger.warning(
                "IRIS connection attempt %d/%d failed: %s",
                attempt,
                _CONNECT_RETRIES,
                exc,
            )
            if attempt < _CONNECT_RETRIES:
                time.sleep(_CONNECT_BACKOFF_SECONDS * attempt)

    raise IrisConnectionError(
        f"Could not connect to IRIS at {IRIS_HOST}:{IRIS_PORT} "
        f"(namespace={IRIS_NAMESPACE}) after {_CONNECT_RETRIES} attempts. "
        f"Last error: {last_exc}"
    ) from last_exc


@contextmanager
def _cursor() -> Iterator[Any]:
    """Yield a cursor, committing on success and always cleaning up."""
    conn = _connect()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()


def check_connection() -> None:
    """Validate config and prove the instance is reachable (runs ``SELECT 1``).

    Raises ``IrisConfigError`` / ``IrisConnectionError`` with a clear message.
    Use this before embedding so indexing fails fast (and before spending any
    OpenAI tokens) when IRIS is misconfigured or down.
    """
    with _cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    logger.info("IRIS connectivity check passed (SELECT 1).")


def _split_schema_table() -> tuple[str, str]:
    schema, _, table = IRIS_VECTOR_TABLE.partition(".")
    return (schema, table) if table else ("SQLUser", schema)


def table_exists() -> bool:
    """True if the configured vector table already exists."""
    schema, table = _split_schema_table()
    with _cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
            [schema, table],
        )
        (count,) = cur.fetchone()
        return int(count) > 0


def count_documents() -> int:
    """Return the number of rows currently stored in the vector table."""
    with _cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {IRIS_VECTOR_TABLE}")
        (count,) = cur.fetchone()
        return int(count)


def ensure_table(reset: bool = False) -> str:
    """Create the vector table if missing (idempotent).

    Returns a status string: ``"created"``, ``"recreated"`` (when ``reset`` is
    True), or ``"exists"``. Logged so the indexing pipeline is auditable.
    """
    exists_before = table_exists()

    if reset and exists_before:
        with _cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {IRIS_VECTOR_TABLE}")
        logger.info("Dropped existing vector table %s (reset).", IRIS_VECTOR_TABLE)
        exists_before = False

    if not exists_before:
        with _cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE {IRIS_VECTOR_TABLE} (
                    doc_id VARCHAR(128) NOT NULL PRIMARY KEY,
                    source_table VARCHAR(64),
                    content VARCHAR(4000),
                    metadata VARCHAR(4000),
                    embedding VECTOR(FLOAT, {EMBEDDING_DIM})
                )
                """
            )
        status = "recreated" if reset else "created"
        logger.info(
            "Vector table %s %s (embedding dim=%d).",
            IRIS_VECTOR_TABLE,
            status,
            EMBEDDING_DIM,
        )
        return status

    logger.info("Vector table %s already exists.", IRIS_VECTOR_TABLE)
    return "exists"


def create_schema(reset: bool = False) -> None:
    """Backwards-compatible alias for :func:`ensure_table`."""
    ensure_table(reset=reset)


# --------------------------------------------------------------------------- #
# Write path (idempotent, doc_id-keyed, batched + auditable)
# --------------------------------------------------------------------------- #
def _insert_sql() -> str:
    return (
        f"INSERT INTO {IRIS_VECTOR_TABLE} "
        "(doc_id, source_table, content, metadata, embedding) "
        f"VALUES (?, ?, ?, ?, TO_VECTOR(?, FLOAT, {EMBEDDING_DIM}))"
    )


def _params_for(documents: list[VectorDocument]) -> list[list[Any]]:
    return [
        [
            doc.doc_id,
            doc.source_table,
            doc.content,
            json.dumps(doc.metadata),
            _vector_to_string(doc.embedding),
        ]
        for doc in documents
    ]


def _upsert_chunk(chunk: list[VectorDocument]) -> None:
    """Delete-then-insert one chunk inside a single transaction (idempotent)."""
    doc_ids = [doc.doc_id for doc in chunk]
    placeholders = ",".join(["?"] * len(doc_ids))
    with _cursor() as cur:
        cur.execute(
            f"DELETE FROM {IRIS_VECTOR_TABLE} WHERE doc_id IN ({placeholders})",
            doc_ids,
        )
        cur.executemany(_insert_sql(), _params_for(chunk))


def upsert_documents(
    documents: list[VectorDocument],
    batch_size: int = DEFAULT_INSERT_BATCH,
) -> int:
    """Idempotently write documents keyed on ``doc_id`` (the invoice id).

    Existing rows with the same ``doc_id`` are replaced, so re-running indexing
    updates in place instead of creating duplicates or hitting primary-key
    errors. Writes happen in explicit, logged batches for auditability.
    Returns the number of documents written.
    """
    if not documents:
        return 0

    size = max(1, int(batch_size))
    written = 0
    for start in range(0, len(documents), size):
        chunk = documents[start : start + size]
        _upsert_chunk(chunk)
        written += len(chunk)
        logger.info(
            "IRIS upsert: %d/%d documents written (batch of %d).",
            written,
            len(documents),
            len(chunk),
        )
    return written


def insert_documents(documents: list[VectorDocument]) -> int:
    """Plain insert (no idempotency). Prefer :func:`upsert_documents`.

    Kept for backwards compatibility; delegates to the idempotent upsert path
    so repeated runs never produce duplicate primary keys.
    """
    return upsert_documents(documents)


# --------------------------------------------------------------------------- #
# Read path
# --------------------------------------------------------------------------- #
def similarity_search(query_embedding: list[float], top_k: int = 5) -> list[SearchRow]:
    """Top-k cosine-similarity search against the vector table."""
    k = max(1, int(top_k))
    sql = (
        f"SELECT TOP {k} doc_id, source_table, content, metadata, "
        f"VECTOR_COSINE(embedding, TO_VECTOR(?, FLOAT, {EMBEDDING_DIM})) AS score "
        f"FROM {IRIS_VECTOR_TABLE} "
        "ORDER BY score DESC"
    )

    with _cursor() as cur:
        cur.execute(sql, [_vector_to_string(query_embedding)])
        rows = cur.fetchall()

    results: list[SearchRow] = []
    for doc_id, source_table, content, metadata_json, score in rows:
        results.append(
            SearchRow(
                doc_id=doc_id,
                source_table=source_table,
                content=content,
                metadata=json.loads(metadata_json) if metadata_json else {},
                score=float(score),
            )
        )
    return results
