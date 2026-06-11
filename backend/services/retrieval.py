"""
Evidence retrieval with graceful fallback.

Preferred path: the existing IRIS vector seam (semantic search over indexed
invoices). If IRIS or embeddings are unavailable (no OpenAI key, instance down,
nothing indexed yet), we fall back to a dependency-free local keyword match
over the invoice rows so the scaffold always returns supporting evidence.
"""

from __future__ import annotations

import logging
import re

from backend.services.data_store import fmt_money, load_df, to_float
from backend.services.schema import EvidenceItem

logger = logging.getLogger("doxa.services.retrieval")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall(text.lower()) if len(t) > 2}


def _invoice_snippet(row) -> str:
    return (
        f"Invoice {row.get('invoice_number')} — {row.get('vendor_name')} — "
        f"{fmt_money(to_float(row.get('amount')), row.get('currency'))} — "
        f"status {row.get('status')}"
        + (f" — anomaly {row.get('anomaly_type')}" if row.get("anomaly_type") else "")
    ).strip()


def _iris_evidence(query: str, top_k: int) -> list[EvidenceItem]:
    """Try the IRIS vector seam. Raises on any unavailability (caught by caller)."""
    from backend.vector import search_procurement_context

    matches = search_procurement_context(query, top_k=top_k)
    return [
        EvidenceItem(
            source="iris-vector",
            snippet=m.content,
            doc_id=m.doc_id,
            score=round(float(m.score), 4),
        )
        for m in matches
    ]


def _local_evidence(query: str, top_k: int) -> list[EvidenceItem]:
    """Keyword-overlap match over invoice rows. No external dependencies."""
    df = load_df("invoices")
    q_tokens = _tokens(query)
    if not q_tokens:
        df_head = df.head(top_k)
        return [
            EvidenceItem(source="local-text-match", snippet=_invoice_snippet(r), doc_id=str(r.get("invoice_id")))
            for _, r in df_head.iterrows()
        ]

    scored: list[tuple[float, object]] = []
    for _, row in df.iterrows():
        haystack = " ".join(
            str(row.get(col, ""))
            for col in ("vendor_name", "status", "approval_status", "category", "anomaly_type", "risk_flag", "entity_name", "project_code")
        )
        overlap = len(q_tokens & _tokens(haystack))
        if overlap:
            scored.append((overlap, row))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        EvidenceItem(
            source="local-text-match",
            snippet=_invoice_snippet(row),
            doc_id=str(row.get("invoice_id")),
            score=float(score),
        )
        for score, row in scored[:top_k]
    ]


def get_evidence(query: str, top_k: int = 4) -> list[EvidenceItem]:
    """Return supporting evidence, preferring IRIS and falling back to local match."""
    try:
        evidence = _iris_evidence(query, top_k)
        if evidence:
            logger.info("Evidence via IRIS vector search (%d items).", len(evidence))
            return evidence
        logger.info("IRIS returned no matches; using local fallback.")
    except Exception as exc:  # noqa: BLE001 - any IRIS/embedding issue → fallback
        logger.info("IRIS unavailable (%s); using local text-match fallback.", exc)

    return _local_evidence(query, top_k)
