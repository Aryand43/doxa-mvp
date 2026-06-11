"""
Intent classification + routing.

One place decides what a prompt is about. ``run_query`` is the assistant entry
used by POST /api/ai/query. Report and crawl modes have their own endpoints but
share the same classifier for on-demand routing.
"""

from __future__ import annotations

import logging

from backend.services import assistant
from backend.services.schema import AIResponse

logger = logging.getLogger("doxa.services.orchestrator")

# domain intent -> trigger keywords (substring match, lowercased).
_KEYWORDS: dict[str, list[str]] = {
    "approvals": ["approval", "approve", "pending", "awaiting", "sign off", "sign-off"],
    "spend": ["committed", "actual spend", "budget", "spend for", "spend on", "burn"],
    "vendor_risk": ["rejection", "risky", "risk signal", "vendor risk", "supplier risk", "high risk", "performance"],
    "anomaly": ["anomal", "fraud", "duplicate", "suspicious", "irregular", "outlier"],
    "cash_flow": ["cash flow", "cashflow", "liquidity"],
    "contracts": ["contract", "expiry", "expir", "renew"],
    "top_vendors": ["top vendor", "top supplier", "biggest vendor", "largest supplier", "by spend"],
}

_REPORT_HINT = "report"


def classify(prompt: str) -> str:
    """Return the best-matching domain intent, or 'general'."""
    text = prompt.lower()
    best, best_score = "general", 0
    for intent, keywords in _KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best, best_score = intent, score
    return best


def is_report_request(prompt: str) -> bool:
    return _REPORT_HINT in prompt.lower()


def run_query(prompt: str) -> AIResponse:
    """Assistant entry: classify the prompt and synthesize a grounded answer."""
    intent = classify(prompt)
    logger.info("query intent=%s", intent)
    return assistant.synthesize(intent, prompt)
