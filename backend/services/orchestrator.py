"""
Lightweight demo orchestrator.

Heuristic, keyword-first intent routing into the grounded procurement views and
the crawler digest. Deliberately predictable for the scripted demo prompts, and
fully deterministic (no LLM call required). Cross-domain prompts produce a
combined "mixed" response.
"""

from __future__ import annotations

import logging

from backend.services import alerts, procurement
from backend.services.retrieval import get_evidence
from backend.services.schema import DemoResponse

logger = logging.getLogger("doxa.services.orchestrator")

# domain -> trigger keywords (lowercased, substring match).
_KEYWORDS: dict[str, list[str]] = {
    "approvals": ["approval", "approve", "pending", "awaiting", "sign off", "sign-off"],
    "spend": ["committed", "actual spend", "budget", "spend for", "project spend", "burn", "spend on"],
    "vendor_risk": ["rejection", "risk signal", "risky", "vendor risk", "supplier risk", "high risk", "reliab", "performance"],
    "anomaly": ["anomal", "fraud", "duplicate", "suspicious", "irregular", "split"],
    "cash_flow": ["cash flow", "cashflow", "liquidity"],
    "contracts": ["contract", "expiry", "expir", "renew"],
    "top_vendors": ["top vendor", "top supplier", "biggest vendor", "largest supplier", "by spend"],
    "crawler": ["alert", "scan", "crawl", "monitor", "anomaly feed"],
}

_HANDLERS = {
    "approvals": lambda q: procurement.pending_approvals_view(),
    "spend": lambda q: procurement.spend_view(q),
    "vendor_risk": lambda q: procurement.vendor_risk_view(),
    "anomaly": lambda q: procurement.anomaly_invoices_view(),
    "cash_flow": lambda q: procurement.cash_flow_view(),
    "contracts": lambda q: procurement.contracts_expiring_view(),
    "top_vendors": lambda q: procurement.top_vendors_view(),
    "crawler": lambda q: alerts.alerts_digest(),
}

# Domains that benefit from supporting evidence snippets.
_EVIDENCE_DOMAINS = {"approvals", "spend", "vendor_risk", "anomaly", "cash_flow", "contracts", "top_vendors"}


def score_domains(prompt: str) -> list[tuple[str, int]]:
    """Score each domain by number of distinct keyword hits, highest first."""
    text = prompt.lower()
    scores: list[tuple[str, int]] = []
    for domain, keywords in _KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits:
            scores.append((domain, hits))
    scores.sort(key=lambda pair: pair[1], reverse=True)
    return scores


def classify(prompt: str) -> str:
    """Return the top routed domain, or 'general' when nothing matches."""
    scores = score_domains(prompt)
    return scores[0][0] if scores else "general"


def _mixed(prompt: str, primary: str, secondary: str) -> DemoResponse:
    base = _HANDLERS[primary](prompt)
    other = _HANDLERS[secondary](prompt)

    base.intent = "mixed"
    base.title = f"Cross-domain: {base.title} + {other.title.lower()}"
    base.narrative = base.narrative + " " + other.narrative
    base.bullets = base.bullets + other.bullets[:3]
    base.metrics = base.metrics + other.metrics[:2]
    base.alerts = base.alerts + other.alerts
    base.data_scope = sorted(set(base.data_scope) | set(other.data_scope))
    base.confidence = 0.6
    return base


def handle_query(prompt: str, with_evidence: bool = True) -> DemoResponse:
    """Route a free-text prompt to the best grounded view and attach evidence."""
    scores = score_domains(prompt)

    if not scores:
        logger.info("No domain matched prompt; returning overview.")
        response = procurement.overview_view()
        if with_evidence:
            response.evidence = get_evidence(prompt)
        return response

    primary, top_score = scores[0]

    # Cross-domain: a clear second domain ties the leader.
    if len(scores) > 1 and scores[1][1] == top_score:
        secondary = scores[1][0]
        logger.info("Routing prompt to mixed domains: %s + %s", primary, secondary)
        response = _mixed(prompt, primary, secondary)
    else:
        logger.info("Routing prompt to domain '%s'.", primary)
        response = _HANDLERS[primary](prompt)

    if with_evidence and response.intent in _EVIDENCE_DOMAINS:
        response.evidence = get_evidence(prompt)

    return response
