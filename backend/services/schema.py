"""
Shared response schema for all demo panels.

Every demo surface (assistant, reports, crawler, summary) returns the same
``DemoResponse`` shape so the frontend can render any answer with one
component. Fields are intentionally generous: a given response populates only
the parts that make sense for it.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TableData(BaseModel):
    """A simple column/row table for tabular evidence."""

    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)


class Metric(BaseModel):
    """A single headline number (pre-formatted for display)."""

    label: str
    value: str
    hint: str | None = None


class AlertItem(BaseModel):
    """A crawler/anomaly alert."""

    id: str
    severity: str = "low"  # high | medium | low
    source: str = ""
    title: str = ""
    description: str = ""
    recommended_action: str = ""
    reference_id: str | None = None
    vendor_name: str | None = None
    amount: float | None = None
    currency: str | None = None
    detected_at: str | None = None


class ActionItem(BaseModel):
    """A suggested next action (non-functional in the scaffold)."""

    label: str
    kind: str = "secondary"  # primary | secondary
    hint: str | None = None


class EvidenceItem(BaseModel):
    """A supporting record backing the narrative."""

    source: str
    snippet: str
    doc_id: str | None = None
    score: float | None = None


class DemoResponse(BaseModel):
    """One response format suitable for every panel."""

    intent: str
    title: str
    narrative: str = ""
    bullets: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    table: TableData | None = None
    alerts: list[AlertItem] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_scope: list[str] = Field(default_factory=list)
    confidence: float = 0.6
