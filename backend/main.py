"""
DOXA MVP — FastAPI application entry-point.

Run with:
    poetry run uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import BACKEND_CORS_ORIGINS
from backend.routes.chat import router as chat_router
from backend.routes.crawler import router as crawler_router
from backend.routes.reports import router as reports_router

app = FastAPI(
    title="DOXA MVP API",
    version="0.1.0",
    description="LangGraph-powered backend for the DOXA MVP",
)

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(crawler_router)


@app.get("/health")
async def health() -> dict:
    """Simple liveness check."""
    return {"status": "ok"}
