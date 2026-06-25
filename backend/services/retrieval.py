"""
Shared semantic retrieval.

Used by the assistant, reports, and crawler to ground answers in real records.

All retrieval goes through the InterSystems IRIS vector seam in
``backend.vector.search_procurement_context``. ``search`` returns ranked records
and ``get_evidence`` returns EvidenceItem snippets for the response schema.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from backend.auth import can_access_record
from backend.services.schema import EvidenceItem
from backend.vector import ProcurementMatch, search_procurement_context

logger = logging.getLogger("doxa.services.retrieval")


@dataclass
class Hit:
    dataset: str
    doc_id: str
    text: str
    score: float
    record: dict[str, Any]


def _match_to_hit(match: ProcurementMatch) -> Hit:
    return Hit(
        dataset=match.source_table,
        doc_id=match.doc_id,
        text=match.content,
        score=round(float(match.score), 4),
        record=match.metadata,
    )


def retrieval_backend() -> str:
    return "iris"


def search(query: str, top_k: int = 5, datasets: set[str] | None = None) -> list[Hit]:
    """Return the top-k most relevant records for `query`."""
    matches = search_procurement_context(query, top_k=top_k)

    hits: list[Hit] = []
    for match in matches:
        if datasets and match.source_table not in datasets:
            continue
        if not can_access_record(match.metadata):
            continue
        hits.append(_match_to_hit(match))
        if len(hits) >= top_k:
            break

    if not hits:
        logger.warning("IRIS search returned zero hits for query=%r.", query)

    return hits


def get_evidence(query: str, top_k: int = 4, datasets: set[str] | None = None) -> list[EvidenceItem]:
    """Return supporting evidence snippets for the response schema."""
    return [
        EvidenceItem(
            source=f"{hit.dataset} (iris)",
            snippet=hit.text,
            doc_id=hit.doc_id,
            score=hit.score,
        )
        for hit in search(query, top_k=top_k, datasets=datasets)
    ]
