"""
AI Data Crawler.

A real scan over the procurement datasets, not an LLM toy:
  1. load records,
  2. run deterministic detection heuristics,
  3. enrich with vector retrieval (related/similar records),
  4. optionally add a plain-language digest via the LLM,
  5. return a digest + prioritised alert list + scan stats + processing phases.
"""

from __future__ import annotations

import logging

from backend.auth import scope_dataframe
from backend.data_access import loader, queries
from backend.services.retrieval import retrieval_backend, search
from backend.services.schema import AlertItem, CrawlResponse, ScanPhase, ScanStats
from backend.utils.llm import compose_crawler_digest, llm_available
from backend.utils.text import fmt_money, non_empty, to_float

logger = logging.getLogger("doxa.services.crawler")

_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}

_RECOMMENDED = {
    "duplicate_invoice": "Verify against the matching invoice(s) before releasing payment.",
    "anomalous_spend": "Confirm the spend driver and budget-owner sign-off.",
    "price_variance": "Validate the unit price against the contracted rate.",
    "vendor_risk": "Review the vendor scorecard and tighten approval controls.",
    "contract_expiry": "Initiate renewal or renegotiation before the contract lapses.",
}


def _related_ids(query: str, exclude: set[str], k: int = 3) -> list[str]:
    """Use retrieval to find related invoice records (context for an alert)."""
    return [hit.doc_id for hit in search(query, top_k=k, datasets={"invoices"}) if hit.doc_id not in exclude]


# --------------------------------------------------------------------------- #
# Detectors
# --------------------------------------------------------------------------- #
def _detect_duplicate_invoices(limit: int = 6) -> list[AlertItem]:
    inv = scope_dataframe(loader.load("invoices"))
    inv["_amt"] = inv["amount"].apply(to_float)
    alerts: list[AlertItem] = []
    grouped = inv[inv["_amt"] > 0].groupby(["vendor_name", inv["_amt"].round(0)])
    for (vendor, amount), group in grouped:
        if len(group) < 2:
            continue
        ids = group["invoice_id"].astype(str).tolist()
        currency = group.iloc[0]["currency"]
        related = _related_ids(f"invoice {vendor} {amount} {group.iloc[0]['category']}", set(ids))
        alerts.append(
            AlertItem(
                id=f"dup-{vendor}-{int(amount)}".replace(" ", "_"),
                severity="high",
                type="duplicate_invoice",
                source="invoices",
                title=f"Possible duplicate invoices — {vendor}",
                description=(
                    f"{len(ids)} invoices from {vendor} share the same amount "
                    f"{fmt_money(amount, currency)}: {', '.join(ids)}."
                ),
                recommended_action=_RECOMMENDED["duplicate_invoice"],
                records=ids + related,
                vendor_name=vendor,
                amount=amount,
                currency=currency,
            )
        )
        if len(alerts) >= limit:
            break
    return alerts


def _detect_anomalous_spend(limit: int = 6) -> list[AlertItem]:
    inv = scope_dataframe(loader.load("invoices"))
    inv["_amt"] = inv["amount"].apply(to_float)
    alerts: list[AlertItem] = []
    for (currency, category), group in inv.groupby(["currency", "category"]):
        if len(group) < 8:
            continue
        mean = group["_amt"].mean()
        threshold = max(mean * 3, mean + 3 * (group["_amt"].std() or 0))
        for _, r in group[group["_amt"] > threshold].iterrows():
            ratio = (r["_amt"] / mean) if mean else 0
            alerts.append(
                AlertItem(
                    id=f"spend-{r['invoice_id']}",
                    severity="high" if ratio >= 5 else "medium",
                    type="anomalous_spend",
                    source="invoices",
                    title=f"Anomalous spend — {r['invoice_number']}",
                    description=(
                        f"{r['invoice_number']} from {r['vendor_name']} is "
                        f"{fmt_money(r['_amt'], currency)}, ~{ratio:.1f}× the {category} average "
                        f"for {currency}."
                    ),
                    recommended_action=_RECOMMENDED["anomalous_spend"],
                    records=[str(r["invoice_id"])],
                    vendor_name=r["vendor_name"],
                    amount=r["_amt"],
                    currency=currency,
                )
            )
            if len(alerts) >= limit:
                return alerts
    return alerts


def _detect_price_variance(limit: int = 5) -> list[AlertItem]:
    inv = scope_dataframe(loader.load("invoices"))
    inv["_unit"] = inv["unit_price"].apply(to_float)
    priced = inv[inv["_unit"] > 0]
    alerts: list[AlertItem] = []
    for category, group in priced.groupby("category"):
        if len(group) < 8:
            continue
        mean = group["_unit"].mean()
        std = group["_unit"].std() or 0
        threshold = mean + 3 * std
        for _, r in group[group["_unit"] > threshold].iterrows():
            alerts.append(
                AlertItem(
                    id=f"price-{r['invoice_id']}",
                    severity="medium",
                    type="price_variance",
                    source="invoices",
                    title=f"Unit-price outlier — {r['invoice_number']}",
                    description=(
                        f"{r['invoice_number']} ({r['vendor_name']}) has unit price "
                        f"{fmt_money(r['_unit'], r['currency'])}, well above the {category} norm."
                    ),
                    recommended_action=_RECOMMENDED["price_variance"],
                    records=[str(r["invoice_id"])],
                    vendor_name=r["vendor_name"],
                    amount=r["_unit"],
                    currency=r["currency"],
                )
            )
            if len(alerts) >= limit:
                return alerts
    return alerts


def _detect_vendor_risk(limit: int = 5) -> list[AlertItem]:
    ranked = queries.vendors_ranked_by_risk()
    high = ranked[ranked["risk_flag"] == "HIGH"].head(limit)
    alerts: list[AlertItem] = []
    for _, v in high.iterrows():
        vendor_invoices = queries.invoices_for_vendor(v["vendor_name"])
        anomaly_ids: list[str] = []
        if len(vendor_invoices):
            anomalies = vendor_invoices[vendor_invoices["anomaly_type"].apply(non_empty)]
            anomaly_ids = anomalies["invoice_id"].astype(str).head(3).tolist()
        alerts.append(
            AlertItem(
                id=f"vendor-{v['vendor_id']}",
                severity="high",
                type="vendor_risk",
                source="vendors",
                title=f"Elevated vendor risk — {v['vendor_name']}",
                description=(
                    f"{v['vendor_name']} is HIGH risk with rejection rate {v['rejection_rate']} "
                    f"and {len(anomaly_ids)} anomalous invoice(s) sampled."
                ),
                recommended_action=_RECOMMENDED["vendor_risk"],
                records=[str(v["vendor_id"])] + anomaly_ids,
                vendor_name=v["vendor_name"],
            )
        )
    return alerts


def _detect_contract_expiry(window_days: int, limit: int = 6) -> list[AlertItem]:
    soon = queries.expiring_contracts(window_days).head(limit)
    alerts: list[AlertItem] = []
    for _, c in soon.iterrows():
        dte = int(c["_dte"])
        alerts.append(
            AlertItem(
                id=f"contract-{c['contract_id']}",
                severity="high" if dte <= 15 else "medium" if dte <= 30 else "low",
                type="contract_expiry",
                source="contracts",
                title=f"Contract expiring — {c['contract_id']}",
                description=(
                    f"Contract {c['contract_id']} with {c['vendor_name']} ({c['entity_name']}) "
                    f"expires in {dte} days."
                ),
                recommended_action=_RECOMMENDED["contract_expiry"],
                records=[str(c["contract_id"])],
                vendor_name=c["vendor_name"],
            )
        )
    return alerts


def _format_digest_context(
    records_scanned: int,
    alerts: list[AlertItem],
    by_severity: dict[str, int],
    by_type: dict[str, int],
    window_days: int,
) -> str:
    lines = [
        f"Records scanned: {records_scanned:,}",
        f"Window: {window_days} days (contracts)",
        f"Retrieval backend: {retrieval_backend()}",
        f"Alerts found: {len(alerts)}",
        f"By severity: {by_severity}",
        f"By type: {by_type}",
        "Top alerts:",
    ]
    for a in alerts[:8]:
        lines.append(f"  · [{a.severity.upper()}] {a.type}: {a.title}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Scan
# --------------------------------------------------------------------------- #
def scan(window_days: int = 60, max_alerts: int = 25, explain: bool = True) -> CrawlResponse:
    phases: list[ScanPhase] = []

    records_scanned = sum(
        len(scope_dataframe(loader.load(name)))
        for name in ("invoices", "contracts", "vendors")
        if loader.dataset_available(name)
    )
    phases.append(
        ScanPhase(
            id="load",
            label="Loaded procurement datasets",
            detail=f"{records_scanned:,} records across invoices, contracts, vendors",
        )
    )

    dup = _detect_duplicate_invoices()
    phases.append(
        ScanPhase(id="duplicate", label="Duplicate invoice detector", detail=f"{len(dup)} signals")
    )

    spend = _detect_anomalous_spend()
    phases.append(
        ScanPhase(id="anomalous_spend", label="Anomalous spend detector", detail=f"{len(spend)} signals")
    )

    price = _detect_price_variance()
    phases.append(
        ScanPhase(id="price_variance", label="Price variance detector", detail=f"{len(price)} signals")
    )

    vendor = _detect_vendor_risk()
    phases.append(
        ScanPhase(id="vendor_risk", label="Vendor risk detector", detail=f"{len(vendor)} signals")
    )

    contract = _detect_contract_expiry(window_days)
    phases.append(
        ScanPhase(
            id="contract_expiry",
            label="Contract expiry detector",
            detail=f"{len(contract)} signals (≤{window_days}d window)",
        )
    )

    alerts = dup + spend + price + vendor + contract
    alerts.sort(key=lambda a: _SEVERITY_RANK.get(a.severity, 3))
    alerts = alerts[:max_alerts]

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for a in alerts:
        by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        by_type[a.type] = by_type.get(a.type, 0) + 1

    high = by_severity.get("high", 0)
    digest = (
        f"Scanned {records_scanned:,} records across invoices, contracts, and vendors. "
        f"Found {len(alerts)} alerts ({high} high severity). "
        f"Top signals: {', '.join(f'{count} {t.replace('_', ' ')}' for t, count in by_type.items())}."
    )

    if explain and llm_available():
        phases.append(ScanPhase(id="compose", label="Composing scan digest", detail="LLM summarising findings"))
        enhanced = compose_crawler_digest(
            _format_digest_context(records_scanned, alerts, by_severity, by_type, window_days)
        )
        if enhanced:
            digest = enhanced
    else:
        phases.append(
            ScanPhase(id="compose", label="Composed scan digest", detail="Deterministic summary")
        )

    logger.info("crawler scan: %d records, %d alerts", records_scanned, len(alerts))
    return CrawlResponse(
        digest=digest,
        alerts=alerts,
        phases=phases,
        scan_stats=ScanStats(
            records_scanned=records_scanned,
            alerts_found=len(alerts),
            by_severity=by_severity,
            by_type=by_type,
            retrieval_backend=retrieval_backend(),
        ),
        confidence=0.8,
    )
