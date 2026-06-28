"""
历史 Run / Trace 查询 API。

只读查询 SQLite 中已持久化的 Agent 执行链路，不修改 run 或 trace。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.eval import RuleBasedEvaluator
from app.persistence.repositories import RunRepository

router = APIRouter(tags=["runs"])


@router.get("/runs")
def list_runs(limit: int = Query(default=20, description="返回最近 runs 数量，最大 100")) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 100))
    runs = RunRepository().list_runs(limit=safe_limit)
    return {"runs": [_format_run(run) for run in runs]}


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    run = RunRepository().get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_not_found")

    return {
        "run": _format_run(run),
        "steps": [_format_step(step) for step in run.get("steps", [])],
        "tool_calls": [_format_tool_call(tool_call) for tool_call in run.get("tool_calls", [])],
        "evaluation": _format_evaluation(run),
    }


def _format_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "query": run["query"],
        "route_type": run["route_type"],
        "answer_source": run["answer_source"],
        "llm_used": run["llm_used"],
        "status": run["status"],
        "total_latency_ms": run["total_latency_ms"],
        "evaluation_score": run.get("evaluation_score")
        if "evaluation_score" in run
        else (run.get("evaluation") or {}).get("overall_score"),
        "created_at": run["created_at"],
    }


def _format_step(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": step["stage"],
        "engine": step["engine"],
        "input": step["input_json"],
        "output": step["output_json"],
        "latency_ms": step["latency_ms"],
        "status": step["status"],
        "created_at": step["created_at"],
    }


def _format_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
    return {
        "node": tool_call["node"],
        "tool_name": tool_call["tool_name"],
        "status": tool_call["status"],
        "source": tool_call["source"],
        "confidence": tool_call["confidence"],
        "retry_count": tool_call["retry_count"],
        "error": tool_call["error"],
        "latency_ms": tool_call["latency_ms"],
        "result": tool_call["result_json"],
        "created_at": tool_call["created_at"],
    }


def _format_evaluation(run: dict[str, Any]) -> dict[str, Any] | None:
    evaluation = run.get("evaluation")
    if evaluation is None:
        return None

    data = dict(evaluation)
    if "latency_breakdown" not in data:
        data["latency_breakdown"] = RuleBasedEvaluator().build_latency_breakdown(
            {
                "total_latency_ms": run.get("total_latency_ms"),
                "steps": run.get("steps", []),
            },
            [
                {
                    "tool": tool_call.get("tool_name"),
                    "tool_name": tool_call.get("tool_name"),
                    "status": tool_call.get("status"),
                    "latency_ms": tool_call.get("latency_ms"),
                }
                for tool_call in run.get("tool_calls", [])
            ],
        ).model_dump()
    return data
