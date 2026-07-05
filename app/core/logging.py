"""Structured JSON logging helpers."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_run_id: ContextVar[str] = ContextVar("run_id", default="")


def configure_logging() -> None:
    """Configure root logging once for JSON line output."""

    root = logging.getLogger("rd_agent_copilot")
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root.propagate = False


def set_request_context(request_id: str = "", run_id: str = "") -> None:
    if request_id:
        _request_id.set(request_id)
    if run_id:
        _run_id.set(run_id)


def get_request_id() -> str:
    return _request_id.get()


def get_run_id() -> str:
    return _run_id.get()


def log_event(
    *,
    event: str,
    message: str = "",
    level: str = "INFO",
    stage: str = "",
    latency_ms: int | None = None,
    error_code: str = "",
    request_id: str | None = None,
    run_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Emit a structured log entry and return the payload for tests."""

    configure_logging()
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "request_id": request_id if request_id is not None else get_request_id(),
        "run_id": run_id if run_id is not None else get_run_id(),
        "stage": stage,
        "event": event,
        "latency_ms": latency_ms,
        "error_code": error_code,
        "message": message,
    }
    payload.update({key: value for key, value in extra.items() if value is not None})
    logging.getLogger("rd_agent_copilot").log(
        getattr(logging, payload["level"], logging.INFO),
        json.dumps(payload, ensure_ascii=False, default=str),
    )
    return payload
