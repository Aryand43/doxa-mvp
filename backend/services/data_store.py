"""
Central access to the mock procurement CSVs.

All demo services read through here so loading/caching and small numeric
helpers live in one place. Datasets are cached in-process (the mock files do
not change at runtime).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "expanded" / "csv"

# Logical dataset name -> CSV filename (without extension).
DATASETS: dict[str, str] = {
    "invoices": "invoices",
    "payments": "payments",
    "purchase_orders": "purchase_orders",
    "vendors": "vendors",
    "contracts": "contracts",
    "approvals": "approvals",
    "projects": "projects",
    "entities": "entities",
    "alerts_seed": "alerts_seed",
}


def dataset_path(name: str) -> Path:
    filename = DATASETS.get(name, name)
    return DATA_DIR / f"{filename}.csv"


@lru_cache(maxsize=None)
def load_df(name: str) -> pd.DataFrame:
    """Load a dataset as a DataFrame (cached). Treats blanks as empty strings."""
    path = dataset_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Mock dataset not found: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df


def records(name: str) -> list[dict[str, Any]]:
    """Return a dataset as a list of plain dicts (a fresh copy each call)."""
    return load_df(name).to_dict("records")


def dataset_available(name: str) -> bool:
    return dataset_path(name).exists()


# --------------------------------------------------------------------------- #
# Small, forgiving numeric/formatting helpers (mock data is messy strings)
# --------------------------------------------------------------------------- #
def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    return int(to_float(value, default))


def fmt_money(value: float, currency: str | None = None) -> str:
    """Human-friendly money string. Currency is a label only (no FX applied).

    NOTE: the mock data mixes currencies; sums across currencies are
    indicative for the demo. TODO(prod): normalise to a base currency via FX.
    """
    rounded = f"{round(value):,}"
    return f"{currency} {rounded}".strip() if currency else rounded


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%" if value <= 1 else f"{value:.1f}%"


def non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""
