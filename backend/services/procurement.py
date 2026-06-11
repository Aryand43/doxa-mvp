"""
Domain views over the procurement data.

Each function turns reusable queries (data_access.queries) into a grounded
:class:`AIResponse`. These are deterministic and offline-safe; the assistant and
report modes attach retrieval evidence on top.
"""

from __future__ import annotations

import pandas as pd

from backend.data_access import loader, queries
from backend.services.schema import ActionItem, AIResponse, Metric, TableData
from backend.utils.text import fmt_money, fmt_pct, to_float


def _table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> TableData:
    return TableData(
        columns=[header for _, header in columns],
        rows=[[row.get(col, "") for col, _ in columns] for _, row in df.iterrows()],
    )


def pending_approvals_view(limit: int = 15) -> AIResponse:
    pending = queries.pending_approvals()
    by_role = pending["approver_role"].value_counts().to_dict()
    head = pending.head(limit)
    return AIResponse(
        intent="approvals",
        title="Purchase orders & invoices pending approval",
        narrative=(
            f"{len(pending)} items are awaiting approval, sorted by due date so the "
            "most time-sensitive surface first."
        ),
        bullets=[f"{len(pending)} items pending approval"]
        + [f"{count} awaiting {role or 'unassigned'}" for role, count in list(by_role.items())[:4]],
        metrics=[
            Metric(label="Pending", value=str(len(pending))),
            Metric(label="Approver roles", value=str(len(by_role))),
        ],
        table=_table(
            head,
            [
                ("approval_id", "Approval"),
                ("po_id", "PO"),
                ("invoice_id", "Invoice"),
                ("entity_name", "Entity"),
                ("approver_role", "Approver"),
                ("amount", "Amount"),
                ("currency", "Ccy"),
                ("due_date", "Due"),
            ],
        ),
        actions=[
            ActionItem(label="Approve selected", kind="primary", hint="demo only"),
            ActionItem(label="Escalate overdue", kind="secondary"),
        ],
        data_scope=["approvals"],
        confidence=0.85,
    )


def spend_view(query: str | None = None) -> AIResponse:
    matched = queries.find_projects(query)
    if len(matched):
        return _project_spend(matched.iloc[0])
    return _portfolio_spend()


def _project_spend(row) -> AIResponse:
    budget = to_float(row["budget_amount"])
    committed = to_float(row["committed_spend"])
    actual = to_float(row["actual_spend"])
    ccy = row.get("currency") or ""
    util = (actual / budget) if budget else 0.0
    commit_ratio = (committed / budget) if budget else 0.0
    title = row.get("project_title") or row.get("project_code") or "Project"
    return AIResponse(
        intent="spend",
        title=f"Committed vs actual spend — {title}",
        narrative=(
            f"{title} ({row.get('project_code')}) has a budget of {fmt_money(budget, ccy)}. "
            f"Committed is {fmt_money(committed, ccy)} ({fmt_pct(commit_ratio)}) and actual is "
            f"{fmt_money(actual, ccy)} ({fmt_pct(util)})."
        ),
        bullets=[
            f"Budget: {fmt_money(budget, ccy)}",
            f"Committed: {fmt_money(committed, ccy)} ({fmt_pct(commit_ratio)})",
            f"Actual: {fmt_money(actual, ccy)} ({fmt_pct(util)})",
            f"Committed not yet spent: {fmt_money(committed - actual, ccy)}",
        ],
        metrics=[
            Metric(label="Budget", value=fmt_money(budget, ccy)),
            Metric(label="Committed", value=fmt_money(committed, ccy)),
            Metric(label="Actual", value=fmt_money(actual, ccy)),
            Metric(label="Budget used", value=fmt_pct(util)),
        ],
        data_scope=["projects"],
        confidence=0.82,
    )


def _portfolio_spend() -> AIResponse:
    grouped = queries.portfolio_spend_by_currency()
    rows = []
    for ccy, r in grouped.iterrows():
        util = (r["actual_spend"] / r["budget_amount"]) if r["budget_amount"] else 0.0
        rows.append([ccy, fmt_money(r["budget_amount"]), fmt_money(r["committed_spend"]), fmt_money(r["actual_spend"]), fmt_pct(util)])
    projects = loader.load("projects")
    examples = projects["project_code"].dropna().head(5).tolist()
    return AIResponse(
        intent="spend",
        title="Committed vs actual spend — portfolio",
        narrative=(
            f"Across {len(projects)} projects, here is committed vs actual spend grouped by "
            "currency (mock data spans multiple currencies, so totals are shown per currency). "
            "Ask about a specific project to drill in."
        ),
        bullets=[
            f"{len(projects)} projects across {projects['currency'].nunique()} currencies",
            "Try a project code: " + ", ".join(examples),
        ],
        metrics=[
            Metric(label="Projects", value=str(len(projects))),
            Metric(label="Currencies", value=str(projects["currency"].nunique())),
        ],
        table=TableData(columns=["Currency", "Budget", "Committed", "Actual", "Used %"], rows=rows),
        data_scope=["projects"],
        confidence=0.7,
    )


def vendor_risk_view(limit: int = 12) -> AIResponse:
    ranked = queries.vendors_ranked_by_risk()
    high = queries.high_risk_vendors()
    head = ranked.head(limit)
    avg_reject = ranked["_reject"].mean()
    return AIResponse(
        intent="vendor_risk",
        title="Suppliers with the highest rejection / risk signals",
        narrative=(
            f"{len(high)} vendors are flagged HIGH risk. The table ranks suppliers by risk flag "
            "then rejection rate, so the riskiest relationships are at the top."
        ),
        bullets=[
            f"{len(high)} HIGH-risk vendors",
            f"Average rejection rate: {fmt_pct(avg_reject)}",
            f"{int((ranked['_ontime'] < 0.8).sum())} vendors below 80% on-time delivery",
        ],
        metrics=[
            Metric(label="HIGH risk", value=str(len(high))),
            Metric(label="Avg rejection", value=fmt_pct(avg_reject)),
            Metric(label="Vendors", value=str(len(ranked))),
        ],
        table=_table(
            head,
            [
                ("vendor_name", "Vendor"),
                ("category", "Category"),
                ("risk_flag", "Risk"),
                ("rejection_rate", "Rejection"),
                ("on_time_delivery_rate", "On-time"),
                ("ytd_spend", "YTD spend"),
                ("currency", "Ccy"),
            ],
        ),
        actions=[ActionItem(label="Open vendor scorecards", kind="secondary")],
        data_scope=["vendors"],
        confidence=0.85,
    )


def anomaly_invoices_view(limit: int = 15) -> AIResponse:
    flagged = queries.anomalous_invoices()
    by_type = flagged["anomaly_type"].value_counts().to_dict()
    head = flagged.head(limit)
    return AIResponse(
        intent="anomaly",
        title="Invoices with duplicate / fraud / anomaly risk",
        narrative=(
            f"{len(flagged)} invoices carry an anomaly signal. The most common patterns are "
            "duplicate invoices, price-variance outliers, and below-threshold splits."
        ),
        bullets=[f"{len(flagged)} anomalous invoices"]
        + [f"{count} × {atype.replace('_', ' ')}" for atype, count in list(by_type.items())[:6]],
        metrics=[
            Metric(label="Anomalies", value=str(len(flagged))),
            Metric(label="Types", value=str(len(by_type))),
            Metric(label="HIGH risk", value=str(int((flagged["risk_flag"] == "HIGH").sum()))),
        ],
        table=_table(
            head,
            [
                ("invoice_number", "Invoice"),
                ("vendor_name", "Vendor"),
                ("amount", "Amount"),
                ("currency", "Ccy"),
                ("anomaly_type", "Anomaly"),
                ("risk_flag", "Risk"),
                ("status", "Status"),
            ],
        ),
        actions=[ActionItem(label="Hold flagged payments", kind="primary", hint="demo only")],
        data_scope=["invoices"],
        confidence=0.85,
    )


def cash_flow_view() -> AIResponse:
    buckets = queries.cash_flow_buckets()
    invoices = loader.load("invoices")
    paid = int((invoices["status"] == "PAID").sum())
    outstanding = int((invoices["status"] != "PAID").sum())
    near_term = next((count for bucket, count, _ in buckets if bucket == "0-30d"), 0)
    payments = loader.load("payments")
    return AIResponse(
        intent="cash_flow",
        title="Cash flow summary (invoices & payments)",
        narrative=(
            f"{outstanding} invoices are outstanding and {paid} are paid. {near_term} fall in the "
            "0–30 day window and need cash soonest. Amounts are indicative (mixed currencies)."
        ),
        bullets=[
            f"{outstanding} outstanding invoices",
            f"{near_term} due within 30 days",
            f"{paid} invoices already paid",
            f"{len(payments)} payment records on file",
        ],
        metrics=[
            Metric(label="Outstanding", value=str(outstanding)),
            Metric(label="Due ≤30d", value=str(near_term)),
            Metric(label="Paid", value=str(paid)),
        ],
        table=TableData(
            columns=["Ageing bucket", "Outstanding invoices", "Indicative amount"],
            rows=[[bucket, count, fmt_money(amount)] for bucket, count, amount in buckets],
        ),
        actions=[ActionItem(label="Export cash flow forecast", kind="secondary")],
        data_scope=["invoices", "payments"],
        confidence=0.8,
    )


def contracts_expiring_view(days: int = 90, limit: int = 15) -> AIResponse:
    soon = queries.expiring_contracts(days)
    head = soon.head(limit)
    soonest = head.iloc[0] if len(head) else None
    return AIResponse(
        intent="contracts",
        title=f"Contracts approaching expiry (≤ {days} days)",
        narrative=(
            f"{len(soon)} active contracts expire within {days} days. Renew or renegotiate the "
            "earliest first to avoid lapses."
            + (
                f" Soonest: {soonest['contract_id']} with {soonest['vendor_name']} in "
                f"{soonest['_dte']} days."
                if soonest is not None
                else ""
            )
        ),
        bullets=[
            f"{len(soon)} contracts expiring within {days} days",
            f"{int((soon['_dte'] <= 30).sum())} expiring within 30 days",
        ],
        metrics=[
            Metric(label="Expiring", value=str(len(soon))),
            Metric(label="≤30 days", value=str(int((soon["_dte"] <= 30).sum()))),
        ],
        table=_table(
            head,
            [
                ("contract_id", "Contract"),
                ("vendor_name", "Vendor"),
                ("entity_name", "Entity"),
                ("end_date", "Expires"),
                ("days_to_expiry", "Days left"),
                ("category", "Category"),
            ],
        ),
        actions=[ActionItem(label="Start renewal workflow", kind="primary", hint="demo only")],
        data_scope=["contracts"],
        confidence=0.85,
    )


def top_vendors_view(n: int = 10) -> AIResponse:
    top = queries.top_vendors_by_spend(n)
    leader = top.iloc[0] if len(top) else None
    return AIResponse(
        intent="top_vendors",
        title=f"Top {n} vendors by spend",
        narrative=(
            "Vendors ranked by year-to-date spend (shown in each vendor's own currency, no FX)."
            + (
                f" {leader['vendor_name']} leads with {fmt_money(to_float(leader['ytd_spend']), leader['currency'])}."
                if leader is not None
                else ""
            )
        ),
        bullets=[f"Top vendor: {leader['vendor_name']}"] if leader is not None else [],
        metrics=[Metric(label="Vendors ranked", value=str(len(top)))],
        table=_table(
            top,
            [
                ("vendor_name", "Vendor"),
                ("category", "Category"),
                ("ytd_spend", "YTD spend"),
                ("currency", "Ccy"),
                ("risk_flag", "Risk"),
                ("on_time_delivery_rate", "On-time"),
            ],
        ),
        data_scope=["vendors"],
        confidence=0.8,
    )


def overview_view() -> AIResponse:
    pending = queries.pending_approvals()
    overdue = queries.overdue_invoices()
    anomalies = queries.anomalous_invoices()
    high_risk = queries.high_risk_vendors()
    return AIResponse(
        intent="general",
        title="Procurement overview",
        narrative=(
            "A quick read across the procurement estate. Ask about approvals, spend, vendor risk, "
            "anomalies, cash flow, or contracts to drill in."
        ),
        bullets=[
            f"{len(pending)} items pending approval",
            f"{len(overdue)} overdue invoices",
            f"{len(anomalies)} invoices with anomaly signals",
            f"{len(high_risk)} HIGH-risk vendors",
        ],
        metrics=summary_metrics(),
        data_scope=["invoices", "vendors", "contracts", "approvals"],
        confidence=0.55,
    )


def summary_metrics() -> list[Metric]:
    pending = queries.pending_approvals()
    overdue = queries.overdue_invoices()
    anomalies = queries.anomalous_invoices()
    high_risk = queries.high_risk_vendors()
    expiring = queries.expiring_contracts(90)
    return [
        Metric(label="Pending approvals", value=str(len(pending))),
        Metric(label="Overdue invoices", value=str(len(overdue))),
        Metric(label="Anomalies", value=str(len(anomalies))),
        Metric(label="HIGH-risk vendors", value=str(len(high_risk))),
        Metric(label="Contracts ≤90d", value=str(len(expiring))),
    ]
