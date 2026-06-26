"""
聊天 API 路由 — POST /chat。

接收用户问题，调用完整 Agent Pipeline，返回结果 + 全链路 Trace。
"""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.agent.pipeline import run_pipeline
from app.core.models import ChatRequest, ChatResponse, TraceStep
from app.eval import RuleBasedEvaluator
from app.persistence.chat_persistence import persist_chat_response

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest) -> ChatResponse:
    """
    接收用户问题，依次经过：
      Router → Planner → Executor → Synthesizer → Trace
    返回中文回答 + 全链路追踪数据。
    """
    response = run_pipeline(body)
    response.run_id = response.trace.trace_id
    evaluation_start = time.perf_counter()

    try:
        response.evaluation = RuleBasedEvaluator().evaluate(
            {
                "query": body.query,
                "route": response.route.model_dump(),
                "plan": response.plan.model_dump(),
                "tool_results": [result.model_dump() for result in response.tool_results],
                "trace": response.trace.model_dump(),
                "answer": response.answer,
            }
        )
        evaluation_latency_ms = int((time.perf_counter() - evaluation_start) * 1000)
        response.trace.steps.append(
            TraceStep(
                stage="evaluation",
                engine="rule_based",
                output=f"overall_score={response.evaluation.overall_score}",
                latency_ms=evaluation_latency_ms,
                overall_score=response.evaluation.overall_score,
            )
        )
    except Exception:
        evaluation_latency_ms = int((time.perf_counter() - evaluation_start) * 1000)
        response.evaluation = None
        response.trace.evaluation_error = "evaluation_failed"
        response.trace.steps.append(
            TraceStep(
                stage="evaluation",
                engine="rule_based",
                output="evaluation_failed",
                latency_ms=evaluation_latency_ms,
                evaluation_error="evaluation_failed",
            )
        )

    try:
        persist_chat_response(body, response)
    except Exception:
        response.trace.persistence_error = "persistence_write_failed"

    return response
