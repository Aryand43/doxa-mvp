"""
Embedding helper — the single boundary that turns text into vectors.

Reuses the existing OpenAI config seam (the same OPENAI_API_KEY used by the
chat/report graphs) so the POC adds no new credential surface. Swapping the
embedding provider later means changing only this file.
"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from backend.config import EMBEDDING_MODEL, OPENAI_API_KEY


@lru_cache(maxsize=1)
def get_embedder() -> OpenAIEmbeddings:
    """Lazily construct the embedding client on first use (not at import)."""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )


def embed_text(text: str) -> list[float]:
    """Embed a single query string."""
    return get_embedder().embed_query(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of documents (order is preserved)."""
    return get_embedder().embed_documents(texts)
