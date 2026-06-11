"""
Shared semantic retrieval.

Used by the assistant, reports, and crawler to ground answers in real records.

Backends:
  * "local" (default): an in-process TF-IDF vector store built from textual
    procurement records (invoices, contracts, vendors). Cosine similarity over
    sparse vectors. No external services, works fully offline.
  * "iris" (opt-in via RETRIEVAL_BACKEND=iris): uses the InterSystems IRIS
    vector seam in backend/vector. Falls back to local on any failure.

Either way, ``search`` returns ranked records and ``get_evidence`` returns
EvidenceItem snippets for the response schema.
"""

from __future__ import annotations

import logging
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from backend.data_access import loader
from backend.services.schema import EvidenceItem
from backend.utils.text import fmt_money, to_float, tokenize

logger = logging.getLogger("doxa.services.retrieval")


@dataclass
class Hit:
    dataset: str
    doc_id: str
    text: str
    score: float
    record: dict[str, Any]


# --------------------------------------------------------------------------- #
# Record -> text rendering
# --------------------------------------------------------------------------- #
def _invoice_text(r: dict[str, Any]) -> str:
    parts = [
        f"Invoice {r.get('invoice_number')} from vendor {r.get('vendor_name')}",
        f"for {fmt_money(to_float(r.get('amount')), r.get('currency'))}",
        f"status {r.get('status')} approval {r.get('approval_status')}",
        f"category {r.get('category')} risk {r.get('risk_flag')}",
        f"project {r.get('project_code')} entity {r.get('entity_name')}",
    ]
    if r.get("anomaly_type"):
        parts.append(f"anomaly {r.get('anomaly_type')}")
    return ". ".join(p for p in parts if p)


def _contract_text(r: dict[str, Any]) -> str:
    return (
        f"Contract {r.get('contract_id')} with {r.get('vendor_name')} "
        f"({r.get('entity_name')}) category {r.get('category')} status {r.get('status')} "
        f"expires {r.get('end_date')} risk {r.get('risk_flag')}"
    )


def _vendor_text(r: dict[str, Any]) -> str:
    return (
        f"Vendor {r.get('vendor_name')} category {r.get('category')} risk {r.get('risk_flag')} "
        f"rejection {r.get('rejection_rate')} on-time {r.get('on_time_delivery_rate')} "
        f"ytd spend {fmt_money(to_float(r.get('ytd_spend')), r.get('currency'))}"
    )


_RENDERERS = {
    "invoices": ("invoice_id", _invoice_text),
    "contracts": ("contract_id", _contract_text),
    "vendors": ("vendor_id", _vendor_text),
}


# --------------------------------------------------------------------------- #
# Local TF-IDF vector store
# --------------------------------------------------------------------------- #
class _LocalVectorStore:
    def __init__(self) -> None:
        self.docs: list[Hit] = []
        self.vectors: list[dict[str, float]] = []
        self.inverted: dict[str, list[tuple[int, float]]] = defaultdict(list)
        self._build()

    def _build(self) -> None:
        raw_docs: list[tuple[str, str, str, dict]] = []
        for dataset, (id_field, render) in _RENDERERS.items():
            if not loader.dataset_available(dataset):
                continue
            for record in loader.records(dataset):
                text = render(record)
                raw_docs.append((dataset, str(record.get(id_field, "")), text, record))

        token_lists = [tokenize(text) for _, _, text, _ in raw_docs]
        n = len(raw_docs)
        df: dict[str, int] = defaultdict(int)
        for tokens in token_lists:
            for tok in set(tokens):
                df[tok] += 1
        idf = {tok: math.log((n + 1) / (count + 1)) + 1.0 for tok, count in df.items()}

        for idx, ((dataset, doc_id, text, record), tokens) in enumerate(zip(raw_docs, token_lists)):
            tf: dict[str, int] = defaultdict(int)
            for tok in tokens:
                tf[tok] += 1
            vec = {tok: count * idf.get(tok, 0.0) for tok, count in tf.items()}
            norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
            vec = {tok: w / norm for tok, w in vec.items()}

            self.docs.append(Hit(dataset=dataset, doc_id=doc_id, text=text, score=0.0, record=record))
            self.vectors.append(vec)
            for tok, w in vec.items():
                self.inverted[tok].append((idx, w))

        self.idf = idf
        logger.info("Local vector store built: %d documents.", n)

    def search(self, query: str, top_k: int, datasets: set[str] | None) -> list[Hit]:
        tokens = tokenize(query)
        if not tokens:
            return []
        q_tf: dict[str, int] = defaultdict(int)
        for tok in tokens:
            q_tf[tok] += 1
        q_vec = {tok: count * self.idf.get(tok, 0.0) for tok, count in q_tf.items()}
        norm = math.sqrt(sum(w * w for w in q_vec.values())) or 1.0
        q_vec = {tok: w / norm for tok, w in q_vec.items()}

        scores: dict[int, float] = defaultdict(float)
        for tok, qw in q_vec.items():
            for idx, dw in self.inverted.get(tok, ()):  # cosine: sum of shared weights
                scores[idx] += qw * dw

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        hits: list[Hit] = []
        for idx, score in ranked:
            doc = self.docs[idx]
            if datasets and doc.dataset not in datasets:
                continue
            hits.append(Hit(doc.dataset, doc.doc_id, doc.text, round(score, 4), doc.record))
            if len(hits) >= top_k:
                break
        return hits


@lru_cache(maxsize=1)
def _store() -> _LocalVectorStore:
    return _LocalVectorStore()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def retrieval_backend() -> str:
    return os.getenv("RETRIEVAL_BACKEND", "local").lower()


def _iris_hits(query: str, top_k: int) -> list[Hit]:
    from backend.vector import search_procurement_context

    matches = search_procurement_context(query, top_k=top_k)
    return [
        Hit(dataset="invoices", doc_id=m.doc_id, text=m.content, score=round(float(m.score), 4), record=m.metadata)
        for m in matches
    ]


def search(query: str, top_k: int = 5, datasets: set[str] | None = None) -> list[Hit]:
    """Return the top-k most relevant records for `query`."""
    if retrieval_backend() == "iris":
        try:
            hits = _iris_hits(query, top_k)
            if hits:
                return hits
        except Exception as exc:  # noqa: BLE001 - IRIS optional → fall back
            logger.info("IRIS retrieval unavailable (%s); using local store.", exc)
    return _store().search(query, top_k, datasets)


def get_evidence(query: str, top_k: int = 4, datasets: set[str] | None = None) -> list[EvidenceItem]:
    """Return supporting evidence snippets for the response schema."""
    backend = "iris" if retrieval_backend() == "iris" else "local-vector"
    return [
        EvidenceItem(
            source=f"{hit.dataset} ({backend})",
            snippet=hit.text,
            doc_id=hit.doc_id,
            score=hit.score,
        )
        for hit in search(query, top_k=top_k, datasets=datasets)
    ]
