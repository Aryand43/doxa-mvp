"""
Report mode.

Reports are not a separate engine — they reuse the same domain views and
retrieval as the assistant, then format the result as a grounded report card.
"""

from __future__ import annotations

from backend.data_access import loader, queries
from backend.services import orchestrator, procurement
from backend.services.retrieval import get_evidence
from backend.services.schema import AIResponse, Metric, TableData
from backend.utils.text import fmt_money, fmt_pct, non_empty, to_float

REPORT_TYPES = [
    {"id": "spend_analysis", "label": "Spend Analysis"},
    {"id": "vendor_performance", "label": "Vendor Performance"},
    {"id": "cash_flow_forecast", "label": "Cash Flow Forecast"},
    {"id": "entity_summary", "label": "Entity Summary"},
    {"id": "on_demand", "label": "On-Demand Report"},
]


def _as_report(response: AIResponse, title: str, evidence_query: str) -> AIResponse:
    response.mode = "report"
    response.title = title
    response.evidence = get_evidence(evidence_query)
    return response


def spend_analysis_report(target: str | None = None) -> AIResponse:
    response = procurement.spend_view(target)
    title = response.title if target else "Spend Analysis report"
    return _as_report(response, title, target or "committed vs actual spend by project")


def cash_flow_forecast_report() -> AIResponse:
    response = procurement.cash_flow_view()
    return _as_report(response, "Cash Flow Forecast report", "cash flow outstanding invoices payments")


def vendor_performance_report(target: str | None = None) -> AIResponse:
    match = queries.find_vendor(target) if target else None
    if match is None:
        return _as_report(procurement.vendor_risk_view(), "Vendor Performance report", target or "vendor risk")

    name = match["vendor_name"]
    inv = queries.invoices_for_vendor(name)
    anomalies = inv[inv["anomaly_type"].apply(non_empty)]
    overdue = inv[inv["status"] == "OVERDUE"]
    response = AIResponse(
        mode="report",
        intent="vendor_performance",
        title=f"Vendor Performance — {name}",
        narrative=(
            f"{name} is a {match['category']} supplier with risk flag {match['risk_flag']}. "
            f"Rejection rate {fmt_pct(to_float(match['rejection_rate']))}, on-time delivery "
            f"{fmt_pct(to_float(match['on_time_delivery_rate']))}, YTD spend "
            f"{fmt_money(to_float(match['ytd_spend']), match['currency'])}."
        ),
        bullets=[
            f"Risk flag: {match['risk_flag']}",
            f"Rejection rate: {fmt_pct(to_float(match['rejection_rate']))}",
            f"On-time delivery: {fmt_pct(to_float(match['on_time_delivery_rate']))}",
            f"{len(inv)} invoices · {len(anomalies)} anomalies · {len(overdue)} overdue",
        ],
        metrics=[
            Metric(label="Risk", value=str(match["risk_flag"])),
            Metric(label="Rejection", value=fmt_pct(to_float(match["rejection_rate"]))),
            Metric(label="On-time", value=fmt_pct(to_float(match["on_time_delivery_rate"]))),
            Metric(label="YTD spend", value=fmt_money(to_float(match["ytd_spend"]), match["currency"])),
        ],
        table=TableData(
            columns=["Invoice", "Amount", "Ccy", "Status", "Anomaly"],
            rows=[
                [r["invoice_number"], fmt_money(to_float(r["amount"])), r["currency"], r["status"], r["anomaly_type"]]
                for _, r in inv.head(10).iterrows()
            ],
        ),
        data_scope=["vendors", "invoices"],
        confidence=0.85,
    )
    response.evidence = get_evidence(name)
    return response


def entity_summary_report(target: str | None = None) -> AIResponse:
    entity_name = queries.find_entity(target) or "(unknown)"
    rows = queries.invoices_for_entity(entity_name)
    pending = rows[rows["approval_status"].isin({"PENDING", "PENDING_APPROVAL"})]
    overdue = rows[rows["status"] == "OVERDUE"]
    anomalies = rows[rows["anomaly_type"].apply(non_empty)]
    top_vendors = rows["vendor_name"].value_counts().head(5)
    response = AIResponse(
        mode="report",
        intent="entity_summary",
        title=f"Entity Summary — {entity_name}",
        narrative=(
            f"{entity_name} has {len(rows)} invoices: {len(pending)} pending approval, "
            f"{len(overdue)} overdue, {len(anomalies)} with anomaly signals."
        ),
        bullets=[
            f"{len(rows)} invoices",
            f"{len(pending)} pending approval",
            f"{len(overdue)} overdue",
            f"{len(anomalies)} anomalies",
        ],
        metrics=[
            Metric(label="Invoices", value=str(len(rows))),
            Metric(label="Pending", value=str(len(pending))),
            Metric(label="Overdue", value=str(len(overdue))),
            Metric(label="Anomalies", value=str(len(anomalies))),
        ],
        table=TableData(
            columns=["Vendor", "Invoices"],
            rows=[[name, int(count)] for name, count in top_vendors.items()],
        ),
        data_scope=["entities", "invoices"],
        confidence=0.8,
    )
    response.evidence = get_evidence(entity_name)
    return response


def on_demand_report(prompt: str) -> AIResponse:
    response = orchestrator.run_query(prompt)
    response.mode = "report"
    response.title = f"On-Demand report — {prompt[:60]}"
    return response


def generate(report_type: str, target: str | None = None, prompt: str | None = None) -> AIResponse:
    if report_type == "spend_analysis":
        return spend_analysis_report(target)
    if report_type == "vendor_performance":
        return vendor_performance_report(target)
    if report_type == "cash_flow_forecast":
        return cash_flow_forecast_report()
    if report_type == "entity_summary":
        return entity_summary_report(target)
    return on_demand_report(prompt or target or "procurement overview")


def generate_from_prompt(prompt: str) -> AIResponse:
    """Infer a report type + target from free text (used when /query is a report)."""
    text = prompt.lower()
    target = prompt.split(" for ", 1)[1].strip() if " for " in text else None
    if "vendor performance" in text:
        return vendor_performance_report(target)
    if "spend analysis" in text or "committed" in text:
        return spend_analysis_report(target)
    if "cash flow" in text:
        return cash_flow_forecast_report()
    if "entity summary" in text:
        return entity_summary_report(target)
    return on_demand_report(prompt)
