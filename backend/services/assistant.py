"""
Assistant Q/A synthesis.

Given a classified intent and the user's prompt, gather the right grounded
domain view, attach retrieval evidence, and shape confidence. Honest about
uncertainty: a low-confidence answer says so rather than fabricating.
"""

from __future__ import annotations

from backend.services import procurement
from backend.services.retrieval import get_evidence
from backend.services.schema import AIResponse

# intent -> domain view builder
_VIEWS = {
    "approvals": lambda p: procurement.pending_approvals_view(),
    "spend": lambda p: procurement.spend_view(p),
    "vendor_risk": lambda p: procurement.vendor_risk_view(),
    "anomaly": lambda p: procurement.anomaly_invoices_view(),
    "cash_flow": lambda p: procurement.cash_flow_view(),
    "contracts": lambda p: procurement.contracts_expiring_view(),
    "top_vendors": lambda p: procurement.top_vendors_view(),
}


def synthesize(intent: str, prompt: str) -> AIResponse:
    """Build a grounded assistant answer for a classified intent."""
    builder = _VIEWS.get(intent)
    if builder is not None:
        response = builder(prompt)
    else:
        response = procurement.overview_view()
        response.narrative = (
            "I couldn't confidently map that to a specific procurement view, so here is a "
            "general overview. " + response.narrative
        )
        response.confidence = min(response.confidence, 0.4)

    response.mode = "assistant"
    response.evidence = get_evidence(prompt)

    if response.confidence < 0.5:
        response.bullets.append(
            "Confidence is low — name a specific vendor, project, or entity to refine the answer."
        )
    return response
