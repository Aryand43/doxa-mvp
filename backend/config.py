"""
Application configuration — loads environment variables from .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1536"))

IRIS_HOST: str = os.getenv("IRIS_HOST", "localhost")
IRIS_PORT: int = int(os.getenv("IRIS_PORT", "1972"))
IRIS_NAMESPACE: str = os.getenv("IRIS_NAMESPACE", "USER")
IRIS_USERNAME: str = os.getenv("IRIS_USERNAME", "")
IRIS_PASSWORD: str = os.getenv("IRIS_PASSWORD", "")

IRIS_VECTOR_TABLE: str = os.getenv("IRIS_VECTOR_TABLE", "SQLUser.ProcurementVectors")

BACKEND_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
