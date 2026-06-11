"""
Ingestion pipeline — turns the mock `invoices` CSV into embedded
VectorDocuments and loads them into IRIS.

Dataset choice: invoices. `data/expanded/csv/invoices.csv` has 30 dense,
well-defined columns rich in procurement / financial-intelligence signal
(status, approval_status, amount, currency, vendor, category, risk_flag,
anomaly_type, cash-flow bucket). It is the cleanest first slice; the
purchase_orders table is 90+ mostly-empty columns and noisier.

This module is driver-agnostic: it builds documents and delegates embedding
to embed.py and storage to iris_client.py.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from backend.vector.embed import embed_texts
from backend.vector.iris_client import (
    VectorDocument,
    check_connection,
    count_documents,
    ensure_table,
    upsert_documents,
)

logger = logging.getLogger("doxa.vector.ingest")

SOURCE_TABLE = "invoices"
INVOICES_CSV = (
    Path(__file__).resolve().parents[2] / "data" / "expanded" / "csv" / "invoices.csv"
)

_EMBED_BATCH = 100

_METADATA_FIELDS = [
    "invoice_number",
    "po_number",
    "entity_name",
    "project_code",
    "vendor_name",
    "status",
    "approval_status",
    "currency",
    "amount",
    "category",
    "risk_flag",
    "anomaly_type",
    "due_date",
    "cash_flow_bucket",
]


def _clean(value: str | None) -> str:
    return (value or "").strip()


def row_to_content(row: dict[str, str]) -> str:
    """Render one invoice row as a retrieval-friendly sentence."""
    g = lambda k: _clean(row.get(k))
    parts = [
        f"Invoice {g('invoice_number') or g('invoice_id')}",
        f"from vendor {g('vendor_name')}" if g("vendor_name") else "",
        f"for project {g('project_code')}" if g("project_code") else "",
        f"(entity {g('entity_name')})" if g("entity_name") else "",
        f"linked to purchase order {g('po_number')}" if g("po_number") else "",
        f"with status {g('status')}" if g("status") else "",
        f"and approval status {g('approval_status')}" if g("approval_status") else "",
        f"for an amount of {g('amount')} {g('currency')}".strip()
        if g("amount")
        else "",
        f"in category {g('category')}" if g("category") else "",
        f"with risk flag {g('risk_flag')}" if g("risk_flag") else "",
        f"flagged as anomaly '{g('anomaly_type')}'" if g("anomaly_type") else "",
        f"created on {g('created_at')}" if g("created_at") else "",
        f"due on {g('due_date')}" if g("due_date") else "",
        f"paid on {g('payment_date')}" if g("payment_date") else "",
        f"cash-flow bucket {g('cash_flow_bucket')}" if g("cash_flow_bucket") else "",
    ]
    return ". ".join(p for p in parts if p).strip() + "."


def row_to_metadata(row: dict[str, str]) -> dict[str, str]:
    """Pick a stable, useful subset of columns as metadata."""
    return {field: _clean(row.get(field)) for field in _METADATA_FIELDS}


def _read_rows(limit: int | None) -> list[dict[str, str]]:
    if not INVOICES_CSV.exists():
        raise FileNotFoundError(f"Mock data not found: {INVOICES_CSV}")
    with INVOICES_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    return rows[:limit] if limit else rows


def _row_doc_id(row: dict[str, str]) -> str:
    """Stable per-invoice identifier used as the IRIS primary key."""
    return _clean(row.get("invoice_id")) or _clean(row.get("invoice_number"))


def _batch_to_documents(
    batch: list[dict[str, str]],
    contents: list[str],
    embeddings: list[list[float]],
) -> list[VectorDocument]:
    documents: list[VectorDocument] = []
    for row, content, embedding in zip(batch, contents, embeddings):
        doc_id = _row_doc_id(row)
        if not doc_id:
            logger.warning("Skipping invoice row with no invoice_id/invoice_number.")
            continue
        documents.append(
            VectorDocument(
                doc_id=doc_id,
                source_table=SOURCE_TABLE,
                content=content,
                metadata=row_to_metadata(row),
                embedding=embedding,
            )
        )
    return documents


def build_documents(limit: int | None = None) -> list[VectorDocument]:
    """Read CSV rows, embed their text, and return VectorDocuments."""
    rows = _read_rows(limit)
    documents: list[VectorDocument] = []
    for start in range(0, len(rows), _EMBED_BATCH):
        batch = rows[start : start + _EMBED_BATCH]
        contents = [row_to_content(r) for r in batch]
        embeddings = embed_texts(contents)
        documents.extend(_batch_to_documents(batch, contents, embeddings))
    return documents


def ingest(
    limit: int | None = None,
    reset: bool = False,
    batch_size: int = _EMBED_BATCH,
) -> int:
    """End-to-end indexing of the mock invoices dataset into IRIS.

    Order of operations is deliberate so the pipeline fails fast and cheaply:
      1. Validate IRIS config + connectivity (before any OpenAI spend).
      2. Ensure the vector table exists (optionally reset it).
      3. Read mock invoice rows.
      4. For each batch: embed, then idempotently upsert (keyed on invoice id).
      5. Report the final indexed count read back from IRIS.

    Returns the number of documents written this run.
    """
    size = max(1, int(batch_size))

    logger.info("Step 1/4: validating IRIS configuration and connectivity...")
    check_connection()

    logger.info("Step 2/4: ensuring vector table exists...")
    status = ensure_table(reset=reset)
    logger.info("Vector table status: %s", status)

    logger.info("Step 3/4: reading mock invoice rows...")
    rows = _read_rows(limit)
    logger.info("Read %d invoice rows from %s.", len(rows), INVOICES_CSV.name)
    if not rows:
        logger.warning("No invoice rows to index; nothing to do.")
        return 0

    total_batches = (len(rows) + size - 1) // size
    logger.info(
        "Step 4/4: embedding + upserting %d rows in %d batch(es) of up to %d.",
        len(rows),
        total_batches,
        size,
    )

    written = 0
    for batch_no, start in enumerate(range(0, len(rows), size), start=1):
        batch = rows[start : start + size]
        contents = [row_to_content(r) for r in batch]

        logger.info(
            "Batch %d/%d: embedding %d rows...", batch_no, total_batches, len(batch)
        )
        embeddings = embed_texts(contents)

        documents = _batch_to_documents(batch, contents, embeddings)
        logger.info(
            "Batch %d/%d: upserting %d documents into IRIS...",
            batch_no,
            total_batches,
            len(documents),
        )
        written += upsert_documents(documents, batch_size=size)

    final_count = count_documents()
    logger.info(
        "Indexing complete: wrote %d document(s) this run; table now holds %d row(s).",
        written,
        final_count,
    )
    return written
