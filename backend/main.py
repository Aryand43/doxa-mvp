"""
Doxa Connex AI — FastAPI application entry-point.

Run with:
    poetry run uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from backend.config import BACKEND_CORS_ORIGINS
from backend.routes.ai import router as ai_router
from backend.routes.auth import router as auth_router
from backend.routes.health import router as health_router

app = FastAPI(
    title="Doxa Connex AI",
    version="1.0.0",
    description="Procurement intelligence copilot — assistant, reports & data crawler.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ai_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Service index — confirms the API is live and points operators to key surfaces."""
    return {
        "service": "Doxa Connex AI API",
        "status": "ok",
        "docs": "/scalar",
        "health": "/health",
    }


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(openapi_url="/openapi.json", title="Doxa Connex AI API")
