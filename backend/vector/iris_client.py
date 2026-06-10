"""
InterSystems IRIS vector client — the ONLY file that touches the IRIS driver
or IRIS-specific SQL. Everything else in backend/vector/ stays driver-agnostic.

IRIS assumptions (documented per the POC brief; confirm against your IRIS
version, validated against the syntax used in the official
intersystems-community/iris-vector-search demos):

  * Driver: `intersystems-irispython` exposes a PEP-249 DB-API via
    `iris.connect(hostname, port, namespace, username, password)`. It is
    imported lazily inside `_connect()` so the rest of the backend (and the
    test suite) imports cleanly even when the driver is not installed.
  * Vector column type: `VECTOR(FLOAT, <dim>)` where <dim> == EMBEDDING_DIM.
  * Insert: embeddings are passed as a comma-separated string and converted
    with `TO_VECTOR(?, FLOAT, <dim>)`.
  * Similarity: `VECTOR_COSINE(a, b)` returns higher = more similar, so we
    `ORDER BY ... DESC`. (Cosine implicitly normalises its inputs.)
  * Existence check: `INFORMATION_SCHEMA.TABLES` is queryable.

If any of the above differs on the target IRIS instance, this file is the only
place that needs to change.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from backend.config import (
    EMBEDDING_DIM,
    IRIS_HOST,
    IRIS_NAMESPACE,
    IRIS_PASSWORD,
    IRIS_PORT,
    IRIS_USERNAME,
    IRIS_VECTOR_TABLE,
)


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


def _connect():
    """Open a DB-API connection. Driver import is lazy and intentional."""
    try:
        import iris
    except ImportError as exc:
        raise RuntimeError(
            "The 'intersystems-irispython' driver is not installed. "
            "Install it (see README, POC 1) before indexing or querying IRIS."
        ) from exc

    if not IRIS_USERNAME or not IRIS_PASSWORD:
        raise RuntimeError(
            "IRIS_USERNAME / IRIS_PASSWORD are not set. Configure them in .env "
            "(credentials are never hardcoded)."
        )

    return iris.connect(
        hostname=IRIS_HOST,
        port=IRIS_PORT,
        namespace=IRIS_NAMESPACE,
        username=IRIS_USERNAME,
        password=IRIS_PASSWORD,
    )


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


def create_schema(reset: bool = False) -> None:
    """Create the vector table if missing. `reset=True` drops it first."""
    with _cursor() as cur:
        if reset:
            cur.execute(f"DROP TABLE IF EXISTS {IRIS_VECTOR_TABLE}")

    if reset or not table_exists():
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


def insert_documents(documents: list[VectorDocument]) -> int:
    """Insert embedded documents. Returns the number of rows written."""
    if not documents:
        return 0

    sql = (
        f"INSERT INTO {IRIS_VECTOR_TABLE} "
        "(doc_id, source_table, content, metadata, embedding) "
        f"VALUES (?, ?, ?, ?, TO_VECTOR(?, FLOAT, {EMBEDDING_DIM}))"
    )
    params = [
        [
            doc.doc_id,
            doc.source_table,
            doc.content,
            json.dumps(doc.metadata),
            _vector_to_string(doc.embedding),
        ]
        for doc in documents
    ]

    with _cursor() as cur:
        cur.executemany(sql, params)
    return len(documents)


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
