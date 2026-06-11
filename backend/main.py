"""
DOXA MVP — FastAPI application entry-point.

Run with:
    poetry run uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from backend.config import BACKEND_CORS_ORIGINS
from backend.routes.chat import router as chat_router
from backend.routes.crawler import router as crawler_router
from backend.routes.reports import router as reports_router
from backend.routes.data import router as data_router
from backend.routes.demo import router as demo_router

app = FastAPI(
    title="DOXA MVP API",
    version="0.1.0",
    description="LangGraph-powered backend for the DOXA MVP",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(crawler_router)
app.include_router(data_router)
app.include_router(demo_router)


@app.get("/health")
async def health() -> dict:
    """Simple liveness check."""
    return {"status": "ok"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Scalar API documentation."""
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="DOXA API Documentation",
    )
