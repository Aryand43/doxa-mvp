"""
Demo scaffold API — one coherent surface for the MVP v1 panels.

  POST /api/demo/query    -> orchestrated, grounded answer (AI Assistant)
  POST /api/demo/report   -> structured report card (AI Reports)
  GET  /api/demo/alerts   -> crawler alerts digest (AI Data Crawler)
  GET  /api/demo/summary  -> dashboard KPI snapshot

All responses use the shared DemoResponse schema. These endpoints are grounded
in the mock CSVs and run without IRIS or an OpenAI key (evidence retrieval
falls back to local text matching).
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.services import procurement, reports
from backend.services.alerts import alerts_digest
from backend.services.orchestrator import handle_query
from backend.services.reports import REPORT_TYPES
from backend.services.schema import DemoResponse

router = APIRouter(prefix="/api/demo", tags=["demo"])


class QueryRequest(BaseModel):
    prompt: str
    session_id: str = "default"


class ReportRequest(BaseModel):
    report_type: str = "on_demand"
    target: str | None = None
    prompt: str | None = None
    session_id: str = "default"


@router.post("/query", response_model=DemoResponse)
async def demo_query(body: QueryRequest) -> DemoResponse:
    """Route a free-text prompt to the best grounded view (AI Assistant)."""
    return handle_query(body.prompt)


@router.post("/report", response_model=DemoResponse)
async def demo_report(body: ReportRequest) -> DemoResponse:
    """Generate a structured report card for the requested report type."""
    return reports.generate_report(
        report_type=body.report_type,
        target=body.target,
        prompt=body.prompt,
    )


@router.get("/report-types")
async def demo_report_types() -> dict[str, list[str]]:
    """List the supported report types (used to render report buttons)."""
    return {"report_types": REPORT_TYPES}


@router.get("/alerts", response_model=DemoResponse)
async def demo_alerts(
    limit: int = Query(12, ge=1, le=50),
    severity: str | None = Query(None),
) -> DemoResponse:
    """Return the prioritised crawler alerts digest."""
    return alerts_digest(limit=limit, severity=severity)


@router.get("/summary", response_model=DemoResponse)
async def demo_summary() -> DemoResponse:
    """Return a compact KPI snapshot for the dashboard header."""
    return procurement.summary_view()
