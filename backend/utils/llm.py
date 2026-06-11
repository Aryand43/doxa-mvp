"""
Optional LLM explanation layer.

The product is fully functional without an LLM: all answers, reports, and
alerts are computed deterministically from data. When an OpenAI key is
configured, ``maybe_explain`` adds a short natural-language gloss on top. Any
failure (no key, no network) returns ``None`` so callers fall back silently.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger("doxa.utils.llm")


def llm_available() -> bool:
    return bool(OPENAI_API_KEY)


@lru_cache(maxsize=1)
def _client():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, timeout=20)


def maybe_explain(system: str, context: str, max_chars: int = 600) -> str | None:
    """Return a short LLM explanation, or None if the LLM is unavailable."""
    if not llm_available():
        return None
    try:
        response = _client().invoke(
            [("system", system), ("user", context)]
        )
        text = (response.content or "").strip()
        return text[:max_chars] or None
    except Exception as exc:  # noqa: BLE001 - any LLM failure → silent fallback
        logger.info("LLM explanation unavailable (%s); using deterministic text.", exc)
        return None
