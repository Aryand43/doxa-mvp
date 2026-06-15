"""
Application configuration — loads environment variables from .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _safe_int(raw: str | None, default: int) -> int:
    """Parse an int from the environment without crashing app import.

    Invalid values fall back to `default`; the IRIS layer re-validates the
    raw value (see ``IRIS_PORT_RAW`` / ``EMBEDDING_DIM_RAW``) and fails fast
    with a clear, secret-free error message before any indexing runs.
    """
    try:
        return int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM_RAW: str = os.getenv("EMBEDDING_DIM", "1536")
EMBEDDING_DIM: int = _safe_int(EMBEDDING_DIM_RAW, 1536)

IRIS_HOST: str = os.getenv("IRIS_HOST", "localhost")
IRIS_PORT_RAW: str = os.getenv("IRIS_PORT", "1972")
IRIS_PORT: int = _safe_int(IRIS_PORT_RAW, 1972)
IRIS_NAMESPACE: str = os.getenv("IRIS_NAMESPACE", "USER")
IRIS_USERNAME: str = os.getenv("IRIS_USERNAME", "")
IRIS_PASSWORD: str = os.getenv("IRIS_PASSWORD", "")

IRIS_VECTOR_TABLE: str = os.getenv("IRIS_VECTOR_TABLE", "SQLUser.ProcurementVectors")

_cors_raw = os.getenv("BACKEND_CORS_ORIGINS", "")
BACKEND_CORS_ORIGINS: list[str] = (
    [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]
    if _cors_raw
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
)
