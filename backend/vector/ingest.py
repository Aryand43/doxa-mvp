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
from pathlib import Path

from backend.vector.embed import embed_texts
from backend.vector.iris_client import (
    VectorDocument,
    create_schema,
    insert_documents,
)

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


def build_documents(limit: int | None = None) -> list[VectorDocument]:
    """Read CSV rows, embed their text, and return VectorDocuments."""
    rows = _read_rows(limit)
    documents: list[VectorDocument] = []

    for start in range(0, len(rows), _EMBED_BATCH):
        batch = rows[start : start + _EMBED_BATCH]
        contents = [row_to_content(r) for r in batch]
        embeddings = embed_texts(contents)
        for row, content, embedding in zip(batch, contents, embeddings):
            doc_id = _clean(row.get("invoice_id")) or _clean(row.get("invoice_number"))
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


def ingest(limit: int | None = None, reset: bool = False) -> int:
    """End-to-end: ensure schema, build embedded docs, insert. Returns count."""
    documents = build_documents(limit=limit)
    create_schema(reset=reset)
    return insert_documents(documents)
