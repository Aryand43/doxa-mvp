"""
AI Data Crawler — alerts digest.

Reads the seeded alerts (and could be extended to derive more from invoices)
and returns a prioritised digest using the shared response schema.
"""

from __future__ import annotations

from backend.services.data_store import fmt_money, load_df, to_float
from backend.services.schema import ActionItem, AlertItem, DemoResponse, Metric

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

_RECOMMENDED_ACTION = {
    "unusual_spend_spike": "Review the spend driver and confirm budget-owner sign-off.",
    "overdue_approval": "Escalate to the approver — approval SLA has been breached.",
    "duplicate_invoice": "Verify against the prior invoice before releasing payment.",
    "price_variance_outlier": "Validate unit price against the contracted rate.",
    "split_below_threshold": "Check for PO splitting to avoid approval thresholds.",
    "contract_expiring_soon": "Initiate renewal or renegotiation with the vendor.",
    "spend_analysis_watch": "Monitor — informational, no action required.",
}


def _action_for(alert_type: str) -> str:
    return _RECOMMENDED_ACTION.get(alert_type, "Review and triage.")


def _to_alert_item(row) -> AlertItem:
    severity = str(row.get("severity", "LOW")).lower()
    alert_type = str(row.get("alert_type", ""))
    return AlertItem(
        id=str(row.get("alert_id")),
        severity=severity,
        source=str(row.get("source_domain") or "crawler"),
        title=str(row.get("message") or alert_type.replace("_", " ").title()),
        description=(
            f"{alert_type.replace('_', ' ').title()} on {row.get('reference_id')}"
            + (f" ({row.get('vendor_name')})" if row.get("vendor_name") else "")
            + (
                f" — {fmt_money(to_float(row.get('amount')), row.get('currency'))}"
                if row.get("amount")
                else ""
            )
        ),
        recommended_action=_action_for(alert_type),
        reference_id=str(row.get("reference_id") or ""),
        vendor_name=row.get("vendor_name") or None,
        amount=to_float(row.get("amount")) or None,
        currency=row.get("currency") or None,
        detected_at=row.get("detected_at") or None,
    )


def alerts_digest(limit: int = 12, severity: str | None = None) -> DemoResponse:
    df = load_df("alerts_seed").copy()
    if severity:
        df = df[df["severity"].str.upper() == severity.upper()]

    df["_rank"] = df["severity"].str.upper().map(_SEVERITY_RANK).fillna(3)
    df = df.sort_values(["_rank", "detected_at"], ascending=[True, False])

    open_alerts = df[df["status"].str.upper() == "OPEN"] if "status" in df else df
    counts = {sev: int((df["severity"].str.upper() == sev).sum()) for sev in ("HIGH", "MEDIUM", "LOW")}

    # Prefer actionable alerts (exclude the noisy watch type) for the headline list.
    actionable = df[df["alert_type"] != "spend_analysis_watch"]
    headline = actionable if len(actionable) else df
    alerts = [_to_alert_item(r) for _, r in headline.head(limit).iterrows()]

    top_types = df["alert_type"].value_counts().head(4).to_dict()
    type_bullets = [f"{count} × {atype.replace('_', ' ')}" for atype, count in top_types.items()]

    return DemoResponse(
        intent="crawler",
        title="AI Data Crawler — alerts digest",
        narrative=(
            f"The crawler is tracking {len(df)} alerts ({len(open_alerts)} open). "
            f"{counts['HIGH']} are high severity and need attention first. The list "
            "below prioritises actionable anomalies over routine spend-watch signals."
        ),
        bullets=[
            f"{counts['HIGH']} high · {counts['MEDIUM']} medium · {counts['LOW']} low",
            f"{len(open_alerts)} open alerts",
        ]
        + type_bullets,
        metrics=[
            Metric(label="High severity", value=str(counts["HIGH"])),
            Metric(label="Medium", value=str(counts["MEDIUM"])),
            Metric(label="Open", value=str(len(open_alerts))),
        ],
        alerts=alerts,
        actions=[
            ActionItem(label="Run new scan", kind="primary", hint="demo only"),
            ActionItem(label="Acknowledge all low", kind="secondary"),
        ],
        data_scope=["alerts_seed"],
        confidence=0.85,
    )
