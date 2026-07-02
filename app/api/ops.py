"""Deployment and observability API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.observability.config_check import APP_VERSION, build_config_check
from app.observability.eval_report import build_eval_report_summary
from app.observability.trace_export import export_run_trace

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict[str, Any]:
    config = build_config_check()
    return {
        "status": config["status"],
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": config["checks"],
    }


@router.get("/config/check")
def config_check() -> dict[str, Any]:
    return build_config_check()


@router.get("/trace/export/{run_id}")
def trace_export(run_id: str) -> dict[str, Any]:
    export = export_run_trace(run_id)
    if export is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    return {"trace_export": export}


@router.get("/eval/report")
def eval_report(include_content: bool = Query(default=False)) -> dict[str, Any]:
    return build_eval_report_summary(include_content=include_content)

