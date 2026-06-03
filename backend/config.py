"""
Application configuration — loads environment variables from .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ── OpenAI ──────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── Server ──────────────────────────────────────────────────────────
BACKEND_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
]
