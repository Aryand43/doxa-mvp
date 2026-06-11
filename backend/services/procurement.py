"""
Grounded procurement service layer.

Each public function reads the mock CSVs (via data_store) and returns a fully
formed :class:`DemoResponse`. These are deterministic and require neither IRIS
nor an OpenAI key, so the demo is reliable offline. The orchestrator and report
builders compose these views.
"""

from __future__ import annotations

import pandas as pd

from backend.services.data_store import (
    fmt_money,
    fmt_pct,
    load_df,
    non_empty,
    to_float,
    to_int,
)
from backend.services.schema import (
    ActionItem,
    AlertItem,
    DemoResponse,
    Metric,
    TableData,
)

_PENDING = {"PENDING", "PENDING_APPROVAL", "SUBMITTED"}
_CASH_BUCKET_ORDER = ["0-30d", "31-60d", "61-90d", "90d+"]


def _table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> TableData:
    """Build a TableData from (source_col, header) pairs."""
    headers = [header for _, header in columns]
    rows: list[list] = []
    for _, row in df.iterrows():
        rows.append([row.get(col, "") for col, _ in columns])
    return TableData(columns=headers, rows=rows)


# --------------------------------------------------------------------------- #
# Approvals
# --------------------------------------------------------------------------- #
def pending_approvals_view(limit: int = 15) -> DemoResponse:
    df = load_df("approvals")
    pending = df[df["approval_status"].isin(_PENDING) | df["status"].isin(_PENDING)].copy()
    pending = pending.sort_values("due_date")

    total = len(pending)
    by_role = pending["approver_role"].value_counts().to_dict()
    role_bullets = [f"{count} awaiting {role or 'unassigned'}" for role, count in by_role.items()]

    head = pending.head(limit)
    table = _table(
        head,
        [
            ("approval_id", "Approval"),
            ("po_id", "PO"),
            ("invoice_id", "Invoice"),
            ("entity_name", "Entity"),
            ("approver_role", "Approver role"),
            ("amount", "Amount"),
            ("currency", "Ccy"),
            ("due_date", "Due"),
        ],
    )

    return DemoResponse(
        intent="approvals",
        title="Purchase orders & invoices pending approval",
        narrative=(
            f"There are {total} items currently awaiting approval across all "
            "entities. The queue is sorted by due date so the most time-sensitive "
            "approvals surface first."
        ),
        bullets=[f"{total} items pending approval"] + role_bullets[:4],
        metrics=[
            Metric(label="Pending approvals", value=str(total)),
            Metric(label="Approver roles", value=str(len(by_role))),
            Metric(label="Showing", value=str(len(head)), hint="top by due date"),
        ],
        table=table,
        actions=[
            ActionItem(label="Approve selected", kind="primary", hint="demo only"),
            ActionItem(label="Escalate overdue", kind="secondary"),
        ],
        data_scope=["approvals"],
        confidence=0.85,
    )


# --------------------------------------------------------------------------- #
# Spend (committed vs actual)
# --------------------------------------------------------------------------- #
def _match_projects(df: pd.DataFrame, query: str | None) -> pd.DataFrame:
    if not query:
        return df.iloc[0:0]
    tokens = [t for t in query.lower().replace("-", " ").split() if len(t) > 2]
    skip = {"project", "spend", "committed", "actual", "this", "month", "summarize", "summary", "for"}
    tokens = [t for t in tokens if t not in skip]
    if not tokens:
        return df.iloc[0:0]
    code = (df["project_code"].fillna("") + " " + df["project_title"].fillna("")).str.lower()
    mask = code.apply(lambda text: any(tok in text for tok in tokens))
    return df[mask]


def spend_view(query: str | None = None) -> DemoResponse:
    df = load_df("projects")
    matched = _match_projects(df, query)

    if len(matched) >= 1:
        return _project_spend(matched)
    return _portfolio_spend(df)


def _project_spend(matched: pd.DataFrame) -> DemoResponse:
    row = matched.iloc[0]
    budget = to_float(row["budget_amount"])
    committed = to_float(row["committed_spend"])
    actual = to_float(row["actual_spend"])
    ccy = row.get("currency") or ""
    util = (actual / budget) if budget else 0.0
    commit_ratio = (committed / budget) if budget else 0.0

    title = row.get("project_title") or row.get("project_code") or "Project"
    return DemoResponse(
        intent="spend",
        title=f"Committed vs actual spend — {title}",
        narrative=(
            f"{title} ({row.get('project_code')}) has a budget of "
            f"{fmt_money(budget, ccy)}. Committed spend is {fmt_money(committed, ccy)} "
            f"({fmt_pct(commit_ratio)} of budget) and actual spend is "
            f"{fmt_money(actual, ccy)} ({fmt_pct(util)} of budget)."
        ),
        bullets=[
            f"Budget: {fmt_money(budget, ccy)}",
            f"Committed: {fmt_money(committed, ccy)} ({fmt_pct(commit_ratio)})",
            f"Actual: {fmt_money(actual, ccy)} ({fmt_pct(util)})",
            f"Remaining vs committed: {fmt_money(committed - actual, ccy)}",
        ],
        metrics=[
            Metric(label="Budget", value=fmt_money(budget, ccy)),
            Metric(label="Committed", value=fmt_money(committed, ccy)),
            Metric(label="Actual", value=fmt_money(actual, ccy)),
            Metric(label="Budget used", value=fmt_pct(util)),
        ],
        data_scope=["projects"],
        confidence=0.8,
    )


def _portfolio_spend(df: pd.DataFrame) -> DemoResponse:
    work = df.copy()
    for col in ("budget_amount", "committed_spend", "actual_spend"):
        work[col] = work[col].apply(to_float)

    grouped = (
        work.groupby("currency")[["budget_amount", "committed_spend", "actual_spend"]]
        .sum()
        .sort_values("actual_spend", ascending=False)
        .head(8)
    )

    rows: list[list] = []
    for ccy, r in grouped.iterrows():
        util = (r["actual_spend"] / r["budget_amount"]) if r["budget_amount"] else 0.0
        rows.append(
            [
                ccy,
                fmt_money(r["budget_amount"]),
                fmt_money(r["committed_spend"]),
                fmt_money(r["actual_spend"]),
                fmt_pct(util),
            ]
        )

    examples = df["project_code"].dropna().head(5).tolist()
    return DemoResponse(
        intent="spend",
        title="Committed vs actual spend — portfolio",
        narrative=(
            f"Across {len(df)} projects, here is committed vs actual spend grouped "
            "by currency (mock data spans multiple currencies, so totals are shown "
            "per currency rather than summed). Ask about a specific project to drill in."
        ),
        bullets=[
            f"{len(df)} projects across {df['currency'].nunique()} currencies",
            "Try a project code: " + ", ".join(examples),
        ],
        metrics=[
            Metric(label="Projects", value=str(len(df))),
            Metric(label="Currencies", value=str(df["currency"].nunique())),
        ],
        table=TableData(
            columns=["Currency", "Budget", "Committed", "Actual", "Used %"],
            rows=rows,
        ),
        data_scope=["projects"],
        confidence=0.7,
    )


# --------------------------------------------------------------------------- #
# Vendor risk
# --------------------------------------------------------------------------- #
def vendor_risk_view(limit: int = 12) -> DemoResponse:
    df = load_df("vendors").copy()
    df["rejection_rate_f"] = df["rejection_rate"].apply(to_float)
    df["on_time_f"] = df["on_time_delivery_rate"].apply(to_float)

    high = df[df["risk_flag"] == "HIGH"]
    risk_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["_rank"] = df["risk_flag"].map(risk_rank).fillna(3)
    ranked = df.sort_values(["_rank", "rejection_rate_f"], ascending=[True, False]).head(limit)

    table = _table(
        ranked,
        [
            ("vendor_name", "Vendor"),
            ("category", "Category"),
            ("risk_flag", "Risk"),
            ("rejection_rate", "Rejection"),
            ("on_time_delivery_rate", "On-time"),
            ("ytd_spend", "YTD spend"),
            ("currency", "Ccy"),
        ],
    )

    avg_reject = df["rejection_rate_f"].mean()
    return DemoResponse(
        intent="vendor_risk",
        title="Suppliers with high rejection or risk signals",
        narrative=(
            f"{len(high)} vendors are flagged HIGH risk. The table ranks suppliers "
            "by risk flag and rejection rate so the riskiest relationships are at the top."
        ),
        bullets=[
            f"{len(high)} HIGH-risk vendors",
            f"Average rejection rate: {fmt_pct(avg_reject)}",
            f"{(df['on_time_f'] < 0.8).sum()} vendors below 80% on-time delivery",
        ],
        metrics=[
            Metric(label="HIGH-risk vendors", value=str(len(high))),
            Metric(label="Avg rejection", value=fmt_pct(avg_reject)),
            Metric(label="Vendors", value=str(len(df))),
        ],
        table=table,
        actions=[ActionItem(label="Open vendor scorecards", kind="secondary")],
        data_scope=["vendors"],
        confidence=0.85,
    )


# --------------------------------------------------------------------------- #
# Anomalous / risky invoices
# --------------------------------------------------------------------------- #
def anomaly_invoices_view(limit: int = 15) -> DemoResponse:
    df = load_df("invoices")
    flagged = df[df["anomaly_type"].apply(non_empty)].copy()

    by_type = flagged["anomaly_type"].value_counts().to_dict()
    type_bullets = [f"{count} × {atype.replace('_', ' ')}" for atype, count in by_type.items()]

    head = flagged.head(limit)
    table = _table(
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
    )

    alerts = [
        AlertItem(
            id=str(r["invoice_id"]),
            severity="high" if r["risk_flag"] == "HIGH" else "medium",
            source="invoices",
            title=f"{str(r['anomaly_type']).replace('_', ' ').title()} — {r['invoice_number']}",
            description=(
                f"Invoice {r['invoice_number']} from {r['vendor_name']} for "
                f"{fmt_money(to_float(r['amount']), r['currency'])} flagged "
                f"'{r['anomaly_type']}'."
            ),
            recommended_action="Review invoice and confirm with vendor before payment.",
            reference_id=str(r["invoice_id"]),
            vendor_name=r["vendor_name"],
            amount=to_float(r["amount"]),
            currency=r["currency"],
        )
        for _, r in flagged.head(6).iterrows()
    ]

    return DemoResponse(
        intent="anomaly",
        title="Invoices with duplicate / fraud / anomaly risk",
        narrative=(
            f"{len(flagged)} invoices carry an anomaly signal. The most common "
            "patterns are duplicate invoices, price-variance outliers, and "
            "below-threshold splits. Highest-risk items are listed first."
        ),
        bullets=[f"{len(flagged)} anomalous invoices"] + type_bullets[:6],
        metrics=[
            Metric(label="Anomalous invoices", value=str(len(flagged))),
            Metric(label="Anomaly types", value=str(len(by_type))),
            Metric(label="HIGH risk", value=str(int((flagged["risk_flag"] == "HIGH").sum()))),
        ],
        table=table,
        alerts=alerts,
        actions=[
            ActionItem(label="Hold flagged payments", kind="primary", hint="demo only"),
            ActionItem(label="Assign to investigations", kind="secondary"),
        ],
        data_scope=["invoices"],
        confidence=0.85,
    )


# --------------------------------------------------------------------------- #
# Cash flow
# --------------------------------------------------------------------------- #
def cash_flow_view() -> DemoResponse:
    inv = load_df("invoices").copy()
    inv["amount_f"] = inv["amount"].apply(to_float)
    outstanding = inv[inv["status"] != "PAID"]

    rows: list[list] = []
    for bucket in _CASH_BUCKET_ORDER:
        sub = outstanding[outstanding["cash_flow_bucket"] == bucket]
        rows.append([bucket, len(sub), fmt_money(sub["amount_f"].sum())])

    paid = inv[inv["status"] == "PAID"]
    payments = load_df("payments")
    near_term = outstanding[outstanding["cash_flow_bucket"] == "0-30d"]

    return DemoResponse(
        intent="cash_flow",
        title="Cash flow summary (invoices & payments)",
        narrative=(
            f"{len(outstanding)} invoices are outstanding and {len(paid)} are paid. "
            f"{len(near_term)} invoices fall in the 0–30 day window and need cash "
            "soonest. Amounts are indicative (mock data mixes currencies)."
        ),
        bullets=[
            f"{len(outstanding)} outstanding invoices",
            f"{len(near_term)} due within 30 days",
            f"{len(paid)} invoices already paid",
            f"{len(payments)} payment records on file",
        ],
        metrics=[
            Metric(label="Outstanding", value=str(len(outstanding))),
            Metric(label="Due ≤30d", value=str(len(near_term))),
            Metric(label="Paid", value=str(len(paid))),
        ],
        table=TableData(
            columns=["Ageing bucket", "Outstanding invoices", "Indicative amount"],
            rows=rows,
        ),
        actions=[ActionItem(label="Export cash flow forecast", kind="secondary")],
        data_scope=["invoices", "payments"],
        confidence=0.8,
    )


# --------------------------------------------------------------------------- #
# Contracts expiring soon
# --------------------------------------------------------------------------- #
def contracts_expiring_view(days: int = 90, limit: int = 15) -> DemoResponse:
    df = load_df("contracts").copy()
    df["dte"] = df["days_to_expiry"].apply(lambda v: to_int(v, default=10**9))
    soon = df[(df["dte"] > 0) & (df["dte"] <= days)].sort_values("dte")

    head = soon.head(limit)
    table = _table(
        head,
        [
            ("contract_id", "Contract"),
            ("vendor_name", "Vendor"),
            ("entity_name", "Entity"),
            ("end_date", "Expires"),
            ("days_to_expiry", "Days left"),
            ("category", "Category"),
            ("currency", "Ccy"),
        ],
    )

    soonest = head.iloc[0] if len(head) else None
    return DemoResponse(
        intent="contracts",
        title=f"Contracts approaching expiry (≤ {days} days)",
        narrative=(
            f"{len(soon)} active contracts expire within {days} days. Renew or "
            "renegotiate the earliest first to avoid lapses in supply or pricing."
            + (
                f" The soonest is {soonest['contract_id']} with {soonest['vendor_name']} "
                f"in {soonest['days_to_expiry']} days."
                if soonest is not None
                else ""
            )
        ),
        bullets=[
            f"{len(soon)} contracts expiring within {days} days",
            f"{int((soon['dte'] <= 30).sum())} expiring within 30 days",
        ],
        metrics=[
            Metric(label="Expiring soon", value=str(len(soon))),
            Metric(label="≤30 days", value=str(int((soon["dte"] <= 30).sum()))),
        ],
        table=table,
        actions=[ActionItem(label="Start renewal workflow", kind="primary", hint="demo only")],
        data_scope=["contracts"],
        confidence=0.85,
    )


# --------------------------------------------------------------------------- #
# Top vendors by spend
# --------------------------------------------------------------------------- #
def top_vendors_view(n: int = 10) -> DemoResponse:
    df = load_df("vendors").copy()
    df["ytd_f"] = df["ytd_spend"].apply(to_float)
    top = df.sort_values("ytd_f", ascending=False).head(n)

    table = _table(
        top,
        [
            ("vendor_name", "Vendor"),
            ("category", "Category"),
            ("ytd_spend", "YTD spend"),
            ("currency", "Ccy"),
            ("risk_flag", "Risk"),
            ("on_time_delivery_rate", "On-time"),
        ],
    )
    leader = top.iloc[0] if len(top) else None
    return DemoResponse(
        intent="top_vendors",
        title=f"Top {n} vendors by spend",
        narrative=(
            "Vendors ranked by year-to-date spend. Spend is shown in each vendor's "
            "own currency (no FX conversion in the scaffold)."
            + (
                f" {leader['vendor_name']} leads with {fmt_money(to_float(leader['ytd_spend']), leader['currency'])}."
                if leader is not None
                else ""
            )
        ),
        bullets=[f"Top vendor: {leader['vendor_name']}" if leader is not None else "No vendors found"],
        metrics=[Metric(label="Vendors ranked", value=str(len(top)))],
        table=table,
        data_scope=["vendors"],
        confidence=0.8,
    )


# --------------------------------------------------------------------------- #
# Overview / fallback
# --------------------------------------------------------------------------- #
def overview_view() -> DemoResponse:
    invoices = load_df("invoices")
    vendors = load_df("vendors")
    contracts = load_df("contracts")
    approvals = load_df("approvals")

    pending = approvals[approvals["approval_status"].isin(_PENDING) | approvals["status"].isin(_PENDING)]
    overdue = invoices[invoices["status"] == "OVERDUE"]
    anomalies = invoices[invoices["anomaly_type"].apply(non_empty)]
    high_risk_vendors = vendors[vendors["risk_flag"] == "HIGH"]

    return DemoResponse(
        intent="general",
        title="Procurement overview",
        narrative=(
            "Here is a quick read across the procurement estate. Ask about "
            "approvals, spend, vendor risk, anomalies, cash flow, or contracts to drill in."
        ),
        bullets=[
            f"{len(pending)} items pending approval",
            f"{len(overdue)} overdue invoices",
            f"{len(anomalies)} invoices with anomaly signals",
            f"{len(high_risk_vendors)} HIGH-risk vendors",
        ],
        metrics=[
            Metric(label="Pending approvals", value=str(len(pending))),
            Metric(label="Overdue invoices", value=str(len(overdue))),
            Metric(label="Anomalies", value=str(len(anomalies))),
            Metric(label="HIGH-risk vendors", value=str(len(high_risk_vendors))),
        ],
        data_scope=["invoices", "vendors", "contracts", "approvals"],
        confidence=0.6,
    )


def summary_view() -> DemoResponse:
    """Compact KPI set for the dashboard top bar."""
    base = overview_view()
    contracts = load_df("contracts").copy()
    contracts["dte"] = contracts["days_to_expiry"].apply(lambda v: to_int(v, default=10**9))
    expiring = contracts[(contracts["dte"] > 0) & (contracts["dte"] <= 90)]

    base.intent = "summary"
    base.title = "Doxa Connex AI — live snapshot"
    base.metrics.append(Metric(label="Contracts ≤90d", value=str(len(expiring))))
    return base
