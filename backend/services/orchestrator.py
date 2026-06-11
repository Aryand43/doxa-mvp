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
from backend.data_access import queries
from backend.utils.llm import classify_label

logger = logging.getLogger("doxa.services.orchestrator")

# domain intent -> trigger keywords (substring match, lowercased).
_KEYWORDS: dict[str, list[str]] = {
    "approvals": [
        "approval", "approve", "pending", "awaiting", "sign off", "sign-off",
        "purchase order", " po ", "pos pending", "my approval", "need approval",
    ],
    "spend": [
        "committed", "actual spend", "budget", "spend for", "spend on", "burn",
        "project spend", "variance", "committed vs", "budget vs",
    ],
    "vendor_risk": [
        "rejection", "risky", "risk signal", "vendor risk", "supplier risk",
        "high risk", "performance", "scorecard", "underperform",
    ],
    "anomaly": [
        "anomal", "fraud", "duplicate", "suspicious", "irregular", "outlier",
        "flagged invoice", "suspicious invoice",
    ],
    "overdue": ["overdue", "past due", "late invoice", "late payment", "past-due"],
    "cash_flow": [
        "cash flow", "cashflow", "liquidity", "outstanding", "payment status",
        "ageing", "aging", "paid vs", "payment exposure", "payment", "exposure",
    ],
    "contracts": ["contract", "expiry", "expir", "renew", "renewal", "lapse"],
    "top_vendors": [
        "top vendor", "top supplier", "biggest vendor", "largest supplier",
        "biggest supplier", "biggest suppliers", "by spend", "who spends", "most spend",
    ],
    "help": [
        "hello", "hi ", "hey ", "help", "what can you", "how do i", "what do you",
        "capabilities", "get started",
    ],
}

_DOMAIN_INTENTS = [k for k in _KEYWORDS if k != "help"]
_REPORT_HINT = "report"


def classify(prompt: str) -> tuple[str, int]:
    """Return the best-matching domain intent and its keyword hit count."""
    text = f" {prompt.lower()} "
    best, best_score = "general", 0
    for intent, keywords in _KEYWORDS.items():
        if intent == "help":
            continue
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best, best_score = intent, score
    return best, best_score


def _is_help_request(prompt: str) -> bool:
    text = f" {prompt.lower()} "
    return any(kw in text for kw in _KEYWORDS["help"]) and len(prompt.split()) <= 12


def resolve_intent(prompt: str) -> str:
    """Keyword match first; LLM disambiguation when the signal is weak."""
    if _is_help_request(prompt):
        return "help"

    intent, score = classify(prompt)
    if score >= 2:
        return intent

    if score == 0 or intent == "general":
        llm_intent = classify_label(prompt, _DOMAIN_INTENTS)
        if llm_intent:
            logger.info("LLM intent=%s (keyword score=%s)", llm_intent, score)
            return llm_intent
        if queries.find_vendor(prompt) is not None:
            return "vendor_risk"
        if len(queries.find_projects(prompt)):
            return "spend"

    return intent if score > 0 else "general"


def is_report_request(prompt: str) -> bool:
    return _REPORT_HINT in prompt.lower()


def run_query(prompt: str, *, explain: bool = True) -> AIResponse:
    """Assistant entry: classify the prompt and synthesize a grounded answer."""
    intent = resolve_intent(prompt)
    logger.info("query intent=%s", intent)
    return assistant.synthesize(intent, prompt, explain=explain)
