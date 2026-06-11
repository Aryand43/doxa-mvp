"""
Report builders for the AI Reports panel.

Five report types, each returning the shared ``DemoResponse`` shape so the
frontend renders them as structured report cards. All are grounded in the mock
CSVs; "On-Demand" defers to the orchestrator so any demo prompt becomes a report.
"""

from __future__ import annotations

from backend.services import procurement
from backend.services.data_store import fmt_money, fmt_pct, load_df, non_empty, to_float
from backend.services.orchestrator import handle_query
from backend.services.retrieval import get_evidence
from backend.services.schema import DemoResponse, Metric, TableData

REPORT_TYPES = [
    "spend_analysis",
    "vendor_performance",
    "cash_flow_forecast",
    "entity_summary",
    "on_demand",
]


def _as_report(response: DemoResponse, title: str) -> DemoResponse:
    response.intent = "report"
    response.title = title
    return response


def spend_analysis_report(target: str | None = None) -> DemoResponse:
    response = procurement.spend_view(target)
    response.evidence = get_evidence(target or "committed vs actual spend by project")
    return _as_report(response, response.title if target else "Spend Analysis report")


def cash_flow_forecast_report() -> DemoResponse:
    response = procurement.cash_flow_view()
    response.evidence = get_evidence("cash flow outstanding invoices payments")
    return _as_report(response, "Cash Flow Forecast report")


def vendor_performance_report(target: str | None = None) -> DemoResponse:
    df = load_df("vendors").copy()
    match = None
    if target:
        tokens = [t for t in target.lower().split() if len(t) > 2]
        mask = df["vendor_name"].str.lower().apply(lambda name: any(t in name for t in tokens))
        hits = df[mask]
        if len(hits):
            match = hits.iloc[0]

    if match is None:
        # No specific vendor → fall back to the risk-ranked overview as a report.
        response = procurement.vendor_risk_view()
        return _as_report(response, "Vendor Performance report")

    vendor_name = match["vendor_name"]
    invoices = load_df("invoices")
    vendor_invoices = invoices[invoices["vendor_name"] == vendor_name]
    anomalies = vendor_invoices[vendor_invoices["anomaly_type"].apply(non_empty)]
    overdue = vendor_invoices[vendor_invoices["status"] == "OVERDUE"]

    return _as_report(
        DemoResponse(
            intent="report",
            title=f"Vendor Performance — {vendor_name}",
            narrative=(
                f"{vendor_name} is a {match['category']} supplier with a risk flag of "
                f"{match['risk_flag']}. Rejection rate is {fmt_pct(to_float(match['rejection_rate']))} "
                f"and on-time delivery is {fmt_pct(to_float(match['on_time_delivery_rate']))}. "
                f"YTD spend is {fmt_money(to_float(match['ytd_spend']), match['currency'])}."
            ),
            bullets=[
                f"Risk flag: {match['risk_flag']}",
                f"Rejection rate: {fmt_pct(to_float(match['rejection_rate']))}",
                f"On-time delivery: {fmt_pct(to_float(match['on_time_delivery_rate']))}",
                f"Active contracts: {match['active_contracts']}",
                f"{len(vendor_invoices)} invoices · {len(anomalies)} anomalies · {len(overdue)} overdue",
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
                    for _, r in vendor_invoices.head(10).iterrows()
                ],
            ),
            evidence=get_evidence(vendor_name),
            data_scope=["vendors", "invoices"],
            confidence=0.85,
        ),
        f"Vendor Performance — {vendor_name}",
    )


def entity_summary_report(target: str | None = None) -> DemoResponse:
    entities = load_df("entities")
    invoices = load_df("invoices").copy()

    entity_name = None
    if target:
        tokens = [t for t in target.lower().split() if len(t) > 2]
        mask = entities["entity_name"].str.lower().apply(lambda name: any(t in name for t in tokens))
        hits = entities[mask]
        if len(hits):
            entity_name = hits.iloc[0]["entity_name"]

    if entity_name is None:
        top = invoices["entity_name"].value_counts()
        entity_name = top.index[0] if len(top) else "(unknown)"

    rows = invoices[invoices["entity_name"] == entity_name]
    pending = rows[rows["approval_status"].isin({"PENDING", "PENDING_APPROVAL"})]
    overdue = rows[rows["status"] == "OVERDUE"]
    anomalies = rows[rows["anomaly_type"].apply(non_empty)]
    top_vendors = rows["vendor_name"].value_counts().head(5)

    return _as_report(
        DemoResponse(
            intent="report",
            title=f"Entity Summary — {entity_name}",
            narrative=(
                f"{entity_name} has {len(rows)} invoices on file: {len(pending)} pending "
                f"approval, {len(overdue)} overdue, and {len(anomalies)} carrying anomaly signals."
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
            evidence=get_evidence(entity_name),
            data_scope=["entities", "invoices"],
            confidence=0.8,
        ),
        f"Entity Summary — {entity_name}",
    )


def on_demand_report(prompt: str) -> DemoResponse:
    response = handle_query(prompt, with_evidence=True)
    response.intent = "report"
    response.title = f"On-Demand report — {prompt[:60]}"
    return response


def generate_report(report_type: str, target: str | None = None, prompt: str | None = None) -> DemoResponse:
    """Dispatch to the requested report builder."""
    if report_type == "spend_analysis":
        return spend_analysis_report(target)
    if report_type == "vendor_performance":
        return vendor_performance_report(target)
    if report_type == "cash_flow_forecast":
        return cash_flow_forecast_report()
    if report_type == "entity_summary":
        return entity_summary_report(target)
    if report_type == "on_demand":
        return on_demand_report(prompt or target or "procurement overview")

    # Unknown type → treat the type label as a free-text prompt.
    return on_demand_report(prompt or report_type)
