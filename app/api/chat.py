"""
聊天 API 路由 — POST /chat。

接收用户问题，调用完整 Agent Pipeline，返回结果 + 全链路 Trace。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from app.agent.pipeline import run_pipeline
from app.core.logging import get_request_id, log_event
from app.core.models import ChatRequest, ChatResponse, TraceStep
from app.eval import RuleBasedEvaluator
from app.evidence import EvidenceChainBuilder
from app.memory import MemoryStore, build_memory_from_payload
from app.persistence.chat_persistence import persist_chat_response
from app.resume import ResumeService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint_http(body: ChatRequest, request: Request) -> ChatResponse:
    return chat_endpoint(body, request_id=request.state.request_id)


def chat_endpoint(body: ChatRequest, request_id: str | None = None) -> ChatResponse:
    """
    接收用户问题，依次经过：
      Router → Planner → Executor → Synthesizer → Trace
    返回中文回答 + 全链路追踪数据。
    """
    response = run_pipeline(body)
    response.run_id = response.trace.trace_id
    response.request_id = request_id or get_request_id()
    response.trace.request_id = response.request_id
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
        response.evaluation.latency_breakdown.evaluation_ms = evaluation_latency_ms
        response.evaluation.latency_breakdown.total_ms += evaluation_latency_ms
        current_bottleneck = response.evaluation.latency_breakdown.bottleneck_ms
        if evaluation_latency_ms > current_bottleneck:
            response.evaluation.latency_breakdown.bottleneck_stage = "evaluation"
            response.evaluation.latency_breakdown.bottleneck_ms = evaluation_latency_ms
        response.trace.steps.append(
            TraceStep(
                stage="evaluation",
                engine="rule_based",
                output=f"overall_score={response.evaluation.overall_score}",
                latency_ms=evaluation_latency_ms,
                overall_score=response.evaluation.overall_score,
            )
        )
        log_event(
            event="evaluation_completed",
            stage="evaluation",
            run_id=response.run_id,
            latency_ms=evaluation_latency_ms,
            message=f"overall={response.evaluation.overall_score}",
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
        log_event(
            event="evaluation_failed",
            stage="evaluation",
            level="ERROR",
            run_id=response.run_id,
            latency_ms=evaluation_latency_ms,
            error_code="evaluation_failed",
            message="Evaluation failed",
        )

    evidence_start = time.perf_counter()
    try:
        response.evidence_chain = EvidenceChainBuilder().build(
            {
                "query": body.query,
                "route": response.route.model_dump(),
                "plan": response.plan.model_dump(),
                "tool_results": [result.model_dump() for result in response.tool_results],
                "trace": response.trace.model_dump(),
                "answer": response.answer,
                "evaluation": response.evaluation.model_dump() if response.evaluation else None,
            }
        )
        if response.evaluation is not None:
            response.evaluation.metrics.evidence_confidence_score = response.evidence_chain.overall_confidence
        evidence_latency_ms = int((time.perf_counter() - evidence_start) * 1000)
        response.trace.steps.append(
            TraceStep(
                stage="evidence",
                engine="rule_based",
                output=f"overall_confidence={response.evidence_chain.overall_confidence}",
                latency_ms=evidence_latency_ms,
                overall_confidence=response.evidence_chain.overall_confidence,
                evidence_count=len(response.evidence_chain.evidence_items),
            )
        )
    except Exception:
        evidence_latency_ms = int((time.perf_counter() - evidence_start) * 1000)
        response.evidence_chain = None
        response.trace.steps.append(
            TraceStep(
                stage="evidence",
                engine="rule_based",
                output="evidence_failed",
                latency_ms=evidence_latency_ms,
                overall_confidence=0.0,
                evidence_count=0,
            )
        )

    if response.answer_source != "safety_guard":
        memory_start = time.perf_counter()
        try:
            memory = build_memory_from_payload({
                "query": body.query,
                "answer": response.answer,
                "source_run_id": response.trace.trace_id,
                "tool_results": [result.model_dump() for result in response.tool_results],
                "evaluation": response.evaluation.model_dump() if response.evaluation else None,
                "evidence_chain": response.evidence_chain.model_dump() if response.evidence_chain else None,
            })
            if memory is None:
                response.trace.steps.append(
                    TraceStep(
                        stage="memory",
                        engine="rule_based",
                        output="memory_created=false",
                        latency_ms=int((time.perf_counter() - memory_start) * 1000),
                        memory_created=False,
                    )
                )
                log_event(event="incident_memory_skipped", stage="incident_memory", run_id=response.run_id, message="memory_created=false")
            else:
                created = MemoryStore().add(memory)
                response.trace.steps.append(
                    TraceStep(
                        stage="memory",
                        engine="rule_based",
                        output="memory_created=true",
                        latency_ms=int((time.perf_counter() - memory_start) * 1000),
                        memory_created=True,
                        memory_id=created.memory_id,
                    )
                )
                log_event(event="incident_memory_created", stage="incident_memory", run_id=response.run_id, message=created.memory_id)
        except Exception:
            response.trace.steps.append(
                TraceStep(
                    stage="memory",
                    engine="rule_based",
                    output="memory_created=false",
                    latency_ms=int((time.perf_counter() - memory_start) * 1000),
                    memory_created=False,
                    error_message="memory_write_failed",
                )
            )
            log_event(
                event="incident_memory_failed",
                stage="incident_memory",
                level="ERROR",
                run_id=response.run_id,
                error_code="memory_write_failed",
                message="Memory write failed",
            )

    try:
        persist_chat_response(body, response)
    except Exception:
        response.trace.persistence_error = "persistence_write_failed"

    return response


@router.post("/chat/resume")
def chat_resume_endpoint() -> dict[str, object]:
    """Continue the latest resumable checkpoint."""

    return ResumeService().resume_latest()
