"""
CSV loader for the normalised procurement datasets.

The cleaned domain datasets live in ``data/expanded/csv`` (the source of truth
for the product). The original, messy source exports under ``data/raw`` are not
used at runtime. Datasets are cached in-process; the mock files do not change.
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
    return DATA_DIR / f"{DATASETS.get(name, name)}.csv"


def dataset_available(name: str) -> bool:
    return dataset_path(name).exists()


@lru_cache(maxsize=None)
def load(name: str) -> pd.DataFrame:
    """Load a dataset as a DataFrame (cached). Blanks become empty strings."""
    path = dataset_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def records(name: str) -> list[dict[str, Any]]:
    """Return a dataset as a list of dicts."""
    return load(name).to_dict("records")


def counts() -> dict[str, int]:
    """Row count per available dataset (used by scan stats / health)."""
    result: dict[str, int] = {}
    for name in DATASETS:
        if dataset_available(name):
            result[name] = len(load(name))
    return result
