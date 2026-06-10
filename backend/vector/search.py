"""
Retrieval seam — the single function a future mock agent calls to pull
procurement context out of IRIS.

Driver-agnostic: embeds the query (embed.py) and runs the similarity search
(iris_client.py), returning a clean, typed structure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.vector.embed import embed_text
from backend.vector.iris_client import similarity_search


@dataclass
class ProcurementMatch:
    """A single retrieved record: text + metadata + similarity score."""

    doc_id: str
    source_table: str
    content: str
    metadata: dict[str, Any]
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def search_procurement_context(query: str, top_k: int = 5) -> list[ProcurementMatch]:
    """Embed `query`, retrieve the top-k most similar procurement records.

    This is the stable entry point for mock agents; callers depend only on
    the ProcurementMatch shape, not on IRIS or embedding internals.
    """
    query_embedding = embed_text(query)
    rows = similarity_search(query_embedding, top_k=top_k)
    return [
        ProcurementMatch(
            doc_id=row.doc_id,
            source_table=row.source_table,
            content=row.content,
            metadata=row.metadata,
            score=row.score,
        )
        for row in rows
    ]
