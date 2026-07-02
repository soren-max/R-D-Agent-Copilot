"""Trace export helpers for persisted Agent runs."""

from __future__ import annotations

from typing import Any

from app.persistence.repositories import RunRepository


def export_run_trace(run_id: str) -> dict[str, Any] | None:
    """Return a portable trace export payload for one persisted run."""

    run = RunRepository().get_run(run_id)
    if run is None:
        return None
    return {
        "run_id": run["run_id"],
        "query": run["query"],
        "status": run["status"],
        "route_type": run["route_type"],
        "answer_source": run["answer_source"],
        "llm_used": run["llm_used"],
        "total_latency_ms": run["total_latency_ms"],
        "created_at": run["created_at"],
        "steps": run.get("steps", []),
        "tool_calls": run.get("tool_calls", []),
        "evaluation": run.get("evaluation"),
    }

