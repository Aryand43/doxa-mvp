"""
Text + number helpers.

Kept deliberately boring: tokenisation for the local vector store, forgiving
numeric coercion for messy CSV strings, and display formatting for money/%.
"""

from __future__ import annotations

import re
from typing import Any

_WORD_RE = re.compile(r"[a-z0-9]+")

# Common words that add noise to keyword/vector matching.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "is", "are",
    "me", "my", "show", "give", "what", "which", "this", "that", "with", "by",
    "today", "month", "please", "list", "get", "summarize", "summary",
}


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens (len > 2), stopwords removed."""
    return [t for t in _WORD_RE.findall((text or "").lower()) if len(t) > 2 and t not in _STOPWORDS]


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    return int(to_float(value, default))


def non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def fmt_money(value: float, currency: str | None = None) -> str:
    """Human-friendly money. Currency is a label only — no FX is applied.

    NOTE: the mock data mixes currencies, so cross-currency sums are
    indicative. TODO(prod): normalise to a base currency via an FX table.
    """
    rounded = f"{round(value):,}"
    return f"{currency} {rounded}".strip() if currency else rounded


def fmt_pct(value: float) -> str:
    """Format a ratio (0–1) or an already-scaled percentage."""
    return f"{value * 100:.1f}%" if abs(value) <= 1 else f"{value:.1f}%"
