"""
Crawler API route.

POST /api/crawler/scan
  Request body:  { "source": "...", "session_id": "..." }
  Response body: { "findings": [...] }
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.crawler.graph import graph

router = APIRouter(prefix="/api/crawler", tags=["crawler"])


class CrawlerRequest(BaseModel):
    source: str
    session_id: str = "default"


class CrawlerResponse(BaseModel):
    findings: list[dict[str, Any]]


@router.post("/scan", response_model=CrawlerResponse)
async def scan(body: CrawlerRequest) -> CrawlerResponse:
    """Scan a data source for anomalies and return structured findings."""
    config = {"configurable": {"thread_id": body.session_id}}

    result = await graph.ainvoke(
        {"messages": [], "source": body.source, "findings": []},
        config=config,
    )

    return CrawlerResponse(findings=result["findings"])
