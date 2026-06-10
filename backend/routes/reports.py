"""
Reports API route.

POST /api/reports/generate
  Request body:  { "prompt": "...", "session_id": "..." }
  Response body: { "report": "..." }
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.reporter.graph import graph

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    prompt: str
    session_id: str = "default"


class ReportResponse(BaseModel):
    report: str


@router.post("/generate", response_model=ReportResponse)
async def generate_report(body: ReportRequest) -> ReportResponse:
    """Generate a structured report from a user prompt."""
    config = {"configurable": {"thread_id": body.session_id}}

    result = await graph.ainvoke(
        {"messages": [("user", body.prompt)]},
        config=config,
    )

    return ReportResponse(report=result["report"])
