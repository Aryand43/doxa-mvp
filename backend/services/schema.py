"""
Shared response contracts.

``AIResponse`` is returned by both the assistant and report modes so the
frontend renders any answer with one component. ``CrawlResponse`` is the
crawler's digest + alert payload.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TableData(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)


class Metric(BaseModel):
    label: str
    value: str
    hint: str | None = None


class AlertItem(BaseModel):
    id: str
    severity: str = "low"  # high | medium | low
    type: str = ""
    source: str = ""
    title: str = ""
    description: str = ""
    recommended_action: str = ""
    records: list[str] = Field(default_factory=list)
    vendor_name: str | None = None
    amount: float | None = None
    currency: str | None = None


class ActionItem(BaseModel):
    label: str
    kind: str = "secondary"  # primary | secondary
    hint: str | None = None


class EvidenceItem(BaseModel):
    source: str
    snippet: str
    doc_id: str | None = None
    score: float | None = None


class AIResponse(BaseModel):
    """Unified assistant / report answer."""

    mode: str = "assistant"  # assistant | report
    intent: str = "general"
    title: str = ""
    narrative: str = ""
    bullets: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    table: TableData | None = None
    alerts: list[AlertItem] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_scope: list[str] = Field(default_factory=list)
    confidence: float = 0.6


class ScanStats(BaseModel):
    records_scanned: int = 0
    alerts_found: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    retrieval_backend: str = "local"


class CrawlResponse(BaseModel):
    """Crawler digest + alerts."""

    digest: str = ""
    alerts: list[AlertItem] = Field(default_factory=list)
    scan_stats: ScanStats = Field(default_factory=ScanStats)
    confidence: float = 0.7
