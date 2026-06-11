"""
Assistant Q/A synthesis.

Given a classified intent and the user's prompt, gather the right grounded
domain view, attach retrieval evidence, and shape confidence. When an LLM is
configured, the narrative is replaced with the model's raw prose grounded in
data facts; title, metrics, table, and bullets stay deterministic.
"""

from __future__ import annotations

from backend.data_access import queries
from backend.services import procurement, reports
from backend.services.retrieval import get_evidence
from backend.services.schema import AIResponse, EvidenceItem
from backend.utils.llm import compose_assistant_raw, llm_available

# intent -> domain view builder
_VIEWS = {
    "approvals": lambda p: procurement.pending_approvals_view(),
    "spend": lambda p: procurement.spend_view(p),
    "vendor_risk": lambda p: procurement.vendor_risk_view(),
    "anomaly": lambda p: procurement.anomaly_invoices_view(),
    "overdue": lambda p: procurement.overdue_invoices_view(),
    "cash_flow": lambda p: procurement.cash_flow_view(),
    "contracts": lambda p: procurement.contracts_expiring_view(),
    "top_vendors": lambda p: procurement.top_vendors_view(),
    "help": lambda p: procurement.overview_view(),
}


def _gather_view(intent: str, prompt: str) -> AIResponse:
    """Pick the most specific grounded view for the intent + prompt."""
    if intent == "vendor_risk" and queries.find_vendor(prompt) is not None:
        response = reports.vendor_performance_report(prompt)
        response.mode = "assistant"
        response.intent = "vendor_risk"
        return response

    builder = _VIEWS.get(intent)
    if builder is not None:
        response = builder(prompt)
        response.intent = intent if intent != "help" else "general"
        return response

    response = procurement.overview_view()
    response.confidence = min(response.confidence, 0.4)
    return response


def _format_grounded_facts(response: AIResponse, prompt: str, evidence: list[EvidenceItem]) -> str:
    """Raw data facts only — no template title/narrative (LLM composes those)."""
    lines = [f"User question: {prompt}", f"Analysis area: {response.intent}"]

    if response.metrics:
        lines.append("Metrics:")
        for m in response.metrics:
            lines.append(f"  - {m.label}: {m.value}")

    if response.table and response.table.rows:
        lines.append(f"Table ({len(response.table.rows)} rows):")
        lines.append("  Columns: " + ", ".join(response.table.columns))
        for row in response.table.rows[:8]:
            lines.append("  · " + " | ".join(str(c) for c in row))

    if evidence:
        lines.append("Related records:")
        for e in evidence[:5]:
            lines.append(f"  · [{e.source}] {e.snippet[:160]}")

    lines.append(f"Confidence score: {response.confidence:.0%}")
    lines.append(f"Datasets used: {', '.join(response.data_scope) or 'overview'}")
    return "\n".join(lines)


def synthesize(intent: str, prompt: str, *, explain: bool = True) -> AIResponse:
    """Build a grounded assistant answer for a classified intent."""
    response = _gather_view(intent, prompt)

    if intent == "help":
        response.title = "How I can help"
        response.confidence = 0.75
    elif intent == "general" and response.intent == "general":
        response.narrative = (
            "I couldn't confidently map that to a specific procurement view, so here is a "
            "general overview. " + response.narrative
        )

    response.mode = "assistant"
    response.evidence = get_evidence(prompt)

    if explain and llm_available():
        raw = compose_assistant_raw(
            prompt,
            _format_grounded_facts(response, prompt, response.evidence),
        )
        if raw:
            response.narrative = raw

    if response.confidence < 0.5:
        response.bullets.append(
            "Confidence is low — name a specific vendor, project, or entity to refine the answer."
        )
    return response
