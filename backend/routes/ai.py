"""
Primary product API for Doxa Connex AI.

Thin routes — all logic lives in services.

  POST /api/ai/query    -> assistant (or report mode if the prompt asks for one)
  POST /api/ai/report   -> structured report card
  GET  /api/ai/report-types
  POST /api/ai/crawl    -> data crawler scan (digest + alerts)
  GET  /api/ai/summary  -> KPI snapshot for the dashboard header
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services import crawler, orchestrator, procurement, reports
from backend.services.schema import AIResponse, CrawlResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])


class QueryRequest(BaseModel):
    prompt: str
    session_id: str = "default"


class ReportRequest(BaseModel):
    report_type: str = "on_demand"
    target: str | None = None
    prompt: str | None = None
    session_id: str = "default"


class CrawlRequest(BaseModel):
    window_days: int = 60
    explain: bool = False
    session_id: str = "default"


@router.post("/query", response_model=AIResponse)
async def query(body: QueryRequest) -> AIResponse:
    if orchestrator.is_report_request(body.prompt):
        return reports.generate_from_prompt(body.prompt)
    return orchestrator.run_query(body.prompt)


@router.post("/report", response_model=AIResponse)
async def report(body: ReportRequest) -> AIResponse:
    return reports.generate(body.report_type, target=body.target, prompt=body.prompt)


@router.get("/report-types")
async def report_types() -> dict:
    return {"report_types": reports.REPORT_TYPES}


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(body: CrawlRequest) -> CrawlResponse:
    return crawler.scan(window_days=body.window_days, explain=body.explain)


@router.get("/summary", response_model=AIResponse)
async def summary() -> AIResponse:
    return AIResponse(
        intent="summary",
        title="Doxa Connex AI — live snapshot",
        narrative="Live procurement KPIs computed from the operational datasets.",
        metrics=procurement.summary_metrics(),
        data_scope=["invoices", "vendors", "contracts", "approvals"],
        confidence=0.9,
    )
