"""
Reusable filters and aggregations over the procurement datasets.

These functions return plain pandas objects / primitives — no presentation or
HTTP concerns. Services compose them into responses. This keeps domain logic in
one place and avoids each service re-implementing the same filters.
"""

from __future__ import annotations

import pandas as pd

from backend.data_access import loader
from backend.utils.dates import days_until
from backend.utils.text import non_empty, to_float

PENDING_STATUSES = {"PENDING", "PENDING_APPROVAL", "SUBMITTED"}
CASH_BUCKET_ORDER = ["0-30d", "31-60d", "61-90d", "90d+"]
_RISK_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


# --------------------------------------------------------------------------- #
# Approvals
# --------------------------------------------------------------------------- #
def pending_approvals() -> pd.DataFrame:
    df = loader.load("approvals")
    mask = df["approval_status"].isin(PENDING_STATUSES) | df["status"].isin(PENDING_STATUSES)
    return df[mask].sort_values("due_date").copy()


# --------------------------------------------------------------------------- #
# Invoices
# --------------------------------------------------------------------------- #
def overdue_invoices() -> pd.DataFrame:
    df = loader.load("invoices")
    return df[df["status"] == "OVERDUE"].copy()


def anomalous_invoices() -> pd.DataFrame:
    df = loader.load("invoices")
    return df[df["anomaly_type"].apply(non_empty)].copy()


def outstanding_invoices() -> pd.DataFrame:
    df = loader.load("invoices")
    return df[df["status"] != "PAID"].copy()


def invoices_for_vendor(vendor_name: str) -> pd.DataFrame:
    df = loader.load("invoices")
    return df[df["vendor_name"] == vendor_name].copy()


def invoices_for_entity(entity_name: str) -> pd.DataFrame:
    df = loader.load("invoices")
    return df[df["entity_name"] == entity_name].copy()


def cash_flow_buckets() -> list[tuple[str, int, float]]:
    """(bucket, outstanding invoice count, indicative amount) in ageing order."""
    df = outstanding_invoices()
    df["_amt"] = df["amount"].apply(to_float)
    rows: list[tuple[str, int, float]] = []
    for bucket in CASH_BUCKET_ORDER:
        sub = df[df["cash_flow_bucket"] == bucket]
        rows.append((bucket, len(sub), float(sub["_amt"].sum())))
    return rows


# --------------------------------------------------------------------------- #
# Vendors
# --------------------------------------------------------------------------- #
def vendors_ranked_by_risk() -> pd.DataFrame:
    df = loader.load("vendors").copy()
    df["_reject"] = df["rejection_rate"].apply(to_float)
    df["_ontime"] = df["on_time_delivery_rate"].apply(to_float)
    df["_rank"] = df["risk_flag"].map(_RISK_RANK).fillna(3)
    return df.sort_values(["_rank", "_reject"], ascending=[True, False])


def high_risk_vendors() -> pd.DataFrame:
    df = loader.load("vendors")
    return df[df["risk_flag"] == "HIGH"].copy()


def top_vendors_by_spend(n: int = 10) -> pd.DataFrame:
    df = loader.load("vendors").copy()
    df["_ytd"] = df["ytd_spend"].apply(to_float)
    return df.sort_values("_ytd", ascending=False).head(n)


def find_vendor(name: str):
    """Return the first vendor row whose name contains any query token, or None."""
    df = loader.load("vendors")
    tokens = [t for t in name.lower().split() if len(t) > 2]
    if not tokens:
        return None
    mask = df["vendor_name"].str.lower().apply(lambda v: any(t in v for t in tokens))
    hits = df[mask]
    return hits.iloc[0] if len(hits) else None


# --------------------------------------------------------------------------- #
# Projects / spend
# --------------------------------------------------------------------------- #
def find_projects(query: str | None) -> pd.DataFrame:
    df = loader.load("projects")
    if not query:
        return df.iloc[0:0]
    skip = {"project", "spend", "committed", "actual", "this", "month", "for", "summarize"}
    tokens = [t for t in query.lower().replace("-", " ").split() if len(t) > 2 and t not in skip]
    if not tokens:
        return df.iloc[0:0]
    haystack = (df["project_code"].fillna("") + " " + df["project_title"].fillna("")).str.lower()
    mask = haystack.apply(lambda text: any(tok in text for tok in tokens))
    return df[mask].copy()


def portfolio_spend_by_currency(top: int = 8) -> pd.DataFrame:
    df = loader.load("projects").copy()
    for col in ("budget_amount", "committed_spend", "actual_spend"):
        df[col] = df[col].apply(to_float)
    return (
        df.groupby("currency")[["budget_amount", "committed_spend", "actual_spend"]]
        .sum()
        .sort_values("actual_spend", ascending=False)
        .head(top)
    )


# --------------------------------------------------------------------------- #
# Contracts
# --------------------------------------------------------------------------- #
def expiring_contracts(days: int = 90) -> pd.DataFrame:
    df = loader.load("contracts").copy()
    # Prefer the precomputed column; fall back to date math when absent.
    df["_dte"] = df.apply(
        lambda r: int(to_float(r.get("days_to_expiry"), default=10**9))
        if non_empty(r.get("days_to_expiry"))
        else (days_until(r.get("end_date")) if days_until(r.get("end_date")) is not None else 10**9),
        axis=1,
    )
    soon = df[(df["_dte"] > 0) & (df["_dte"] <= days)]
    return soon.sort_values("_dte").copy()


def find_entity(name: str | None) -> str | None:
    entities = loader.load("entities")
    if name:
        tokens = [t for t in name.lower().split() if len(t) > 2]
        if tokens:
            mask = entities["entity_name"].str.lower().apply(lambda v: any(t in v for t in tokens))
            hits = entities[mask]
            if len(hits):
                return hits.iloc[0]["entity_name"]
    # Default to the busiest entity by invoice volume.
    top = loader.load("invoices")["entity_name"].value_counts()
    return top.index[0] if len(top) else None
