"""
Lightweight IRIS connectivity preflight check.

Runnable before full indexing to confirm, in order:
  1. required env vars are present (and the OpenAI key needed for embedding),
  2. the IRIS instance is reachable (validates config + ``SELECT 1``),
  3. the target vector table can be checked / created.

Returns a structured, secret-free result so callers (CLI, tests, future
health checks) can branch on it. No credential values are ever returned or
logged — only variable names and non-secret coordinates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.config import OPENAI_API_KEY
from backend.vector.iris_client import (
    IrisConfigError,
    IrisConnectionError,
    check_connection,
    count_documents,
    ensure_table,
    table_exists,
    validate_config,
)

logger = logging.getLogger("doxa.vector.preflight")


@dataclass
class PreflightResult:
    """Outcome of the IRIS preflight check (no secret values included)."""

    config_ok: bool = False
    openai_key_present: bool = False
    connection_ok: bool = False
    table_ok: bool = False
    table_status: str | None = None
    document_count: int | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.config_ok and self.connection_ok and self.table_ok


def run_preflight(create_table: bool = True) -> PreflightResult:
    """Run the connectivity preflight and return a structured result.

    Stops at the first failing stage (later checks would be meaningless) and
    records a clear, secret-free error message.

    Args:
        create_table: when True, create the vector table if it is missing;
            when False, only report whether it already exists.
    """
    result = PreflightResult()
    result.openai_key_present = bool(OPENAI_API_KEY)

    # 1) Config presence / validity.
    try:
        validate_config()
        result.config_ok = True
        logger.info("Preflight: IRIS configuration is present and valid.")
    except IrisConfigError as exc:
        result.errors.append(str(exc))
        logger.error("Preflight: configuration error: %s", exc)
        return result

    if not result.openai_key_present:
        # Not fatal for IRIS connectivity, but indexing will fail without it.
        result.errors.append(
            "OPENAI_API_KEY is not set — connectivity is fine, but embedding "
            "(indexing/query) will fail until it is configured."
        )
        logger.warning("Preflight: OPENAI_API_KEY is not set.")

    # 2) Reachability.
    try:
        check_connection()
        result.connection_ok = True
    except (IrisConnectionError, IrisConfigError) as exc:
        result.errors.append(str(exc))
        logger.error("Preflight: connection error: %s", exc)
        return result
    except Exception as exc:  # noqa: BLE001 - driver raises varied types
        result.errors.append(f"Unexpected IRIS connection failure: {exc}")
        logger.error("Preflight: unexpected connection failure: %s", exc)
        return result

    # 3) Table check / creation.
    try:
        if create_table:
            result.table_status = ensure_table(reset=False)
            result.table_ok = True
        else:
            present = table_exists()
            result.table_status = "exists" if present else "missing"
            result.table_ok = present

        if result.table_ok:
            result.document_count = count_documents()
    except Exception as exc:  # noqa: BLE001 - driver raises varied types
        result.errors.append(f"Vector table check failed: {exc}")
        logger.error("Preflight: table check failed: %s", exc)
        return result

    logger.info(
        "Preflight complete: config=%s connection=%s table=%s (status=%s, rows=%s).",
        result.config_ok,
        result.connection_ok,
        result.table_ok,
        result.table_status,
        result.document_count,
    )
    return result
