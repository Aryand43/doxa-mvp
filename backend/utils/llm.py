"""
Optional LLM explanation layer.

The product is fully functional without an LLM: all answers, reports, and
alerts are computed deterministically from data. When an OpenAI key is
configured, callers receive the model's raw text — no parsing, reformatting,
or truncation.
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


def invoke_raw(system: str, user: str) -> str | None:
    """Return the model's text exactly as generated — no post-processing."""
    if not llm_available():
        return None
    try:
        response = _client().invoke([("system", system), ("user", user)])
        text = (response.content or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001
        logger.info("LLM invoke unavailable (%s).", exc)
        return None


def maybe_explain(system: str, context: str, max_chars: int | None = None) -> str | None:
    """Return an LLM explanation. Pass ``max_chars=None`` for the full raw reply."""
    text = invoke_raw(system, context)
    if text is None:
        return None
    if max_chars is not None:
        return text[:max_chars] or None
    return text


def compose_assistant_raw(prompt: str, context: str) -> str | None:
    """Raw assistant prose grounded in ``context``."""
    return invoke_raw(
        (
            "You are Doxa Connex AI, a procurement intelligence assistant. "
            "Answer the user's question in clear plain language using ONLY the data provided. "
            "Do not invent numbers, vendors, invoice IDs, or amounts."
        ),
        f"Question: {prompt}\n\nData:\n{context}",
    )


def compose_crawler_digest(context: str) -> str | None:
    """Raw executive scan summary grounded in ``context``."""
    return invoke_raw(
        (
            "You are a procurement risk analyst. Summarise this data-crawler scan in 2–4 "
            "sentences for an executive. Highlight severity mix, top signal types, and what "
            "to review first. Use ONLY facts from the data."
        ),
        context,
    )


def classify_label(prompt: str, labels: list[str]) -> str | None:
    """Pick the best label for a prompt using the LLM. Returns None on failure."""
    if not llm_available() or not labels:
        return None
    allowed = ", ".join(labels)
    raw = invoke_raw(
        (
            "You classify procurement finance questions. "
            f"Reply with exactly one label from this list and nothing else: {allowed}."
        ),
        prompt,
    )
    if not raw:
        return None
    label = raw.strip().lower().replace(" ", "_")
    return label if label in labels else None
