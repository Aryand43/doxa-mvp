"""Date helpers for ageing/expiry logic over the mock data."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_date(value: str | None) -> datetime | None:
    """Parse the ISO-ish date strings used across the datasets, or return None."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[: len(fmt) + 2], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def days_until(value: str | None) -> int | None:
    """Whole days from today until `value` (negative if in the past)."""
    parsed = parse_date(value)
    if parsed is None:
        return None
    return (parsed - now()).days
