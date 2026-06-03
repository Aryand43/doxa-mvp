"""
Shared LLM factory.

All agent graphs import the LLM from here so we maintain a single
client instance across the application.
"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from backend.config import OPENAI_API_KEY, OPENAI_MODEL


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """Lazily initialise the LLM client on first use (not at import time).

    This allows the FastAPI app to boot and serve /health even when
    OPENAI_API_KEY is not yet configured.
    """
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,  # type: ignore[arg-type]
    )
