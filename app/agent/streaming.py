from __future__ import annotations

import time
from collections.abc import Iterator

from app.agent.executor import Executor
from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.agent.synthesizer import AnswerSynthesizer
from app.core.events import sse_event
from app.core.models import ChatRequest, ChatResponse, TraceStep
from app.core.trace import Tracer
from app.eval import RuleBasedEvaluator
from app.evidence import EvidenceChainBuilder
from app.persistence.chat_persistence import persist_chat_response


def stream_pipeline(request: ChatRequest) -> Iterator[str]:
    """Run the Agent chain and yield SSE execution-status events."""
    tracer = Tracer()
    try:
        yield sse_event("router_started", {"message": "Router 正在判断问题类型"})
        tracer.start_stage("router")
        route_result = IntentRouter().route(request.query)
        tracer.end_stage("router", output=f"type={route_result.type}, confidence={route_result.confidence}")
        yield sse_event(
            "router_completed",
            {
                "message": "Router 已完成问题分流",
                "route": route_result.model_dump(),
            },
        )

        yield sse_event("planner_started", {"message": "Planner 正在生成执行计划"})
        tracer.start_stage("planner")
        plan = Planner().plan(request.query, route_result)
        tracer.end_stage("planner", output=f"plan_type={plan.plan_type}, steps={len(plan.steps)}")
        yield sse_event(
            "planner_completed",
            {
                "message": "Planner 已完成执行计划",
                "plan": plan.model_dump(),
            },
        )

        yield sse_event("executor_started", {"message": "LangGraph 正在执行工具节点"})
        for step in plan.steps:
            if step.tool == "none":
                continue
            yield sse_event(
                "tool_started",
                {
                    "message": f"{step.tool} 正在执行",
                    "step_id": step.id,
                    "action": step.action,
                    "tool_name": step.tool,
                },
            )

        tracer.start_stage("executor")
        tool_results = Executor().execute(request.query, plan)
        tracer.end_executor_stage(
            output=f"tools_called={len([r for r in tool_results if r.tool != 'none'])}",
            tool_results=tool_results,
        )
        for result in tool_results:
            if result.tool == "none":
                continue
            event_data = {
                "message": f"{result.tool_name or result.tool} 执行完成",
                "tool_name": result.tool_name or result.tool,
                "status": result.status,
                "latency_ms": result.latency_ms,
                "retry_count": result.retry_count,
                "source": result.source,
            }
            if result.error:
                event_data["error"] = "tool_failed"
            yield sse_event("tool_completed", event_data)

        yield sse_event("synthesizer_started", {"message": "Synthesizer 正在生成回答"})
        tracer.start_stage("synthesizer")
        trace_summary = tracer.snapshot().model_dump()
        synthesis = AnswerSynthesizer().synthesize(
            request.query,
            route_result,
            plan,
            tool_results,
            trace_summary=trace_summary,
        )
        answer = synthesis["answer"]
        tracer.end_synthesizer_stage(
            answer_source=synthesis["answer_source"],
            llm_used=synthesis["llm_used"],
            llm_error=synthesis["llm_error"],
            prompt_version=synthesis["prompt_version"],
        )
        tracer.set_final_answer(answer)
        yield sse_event(
            "synthesizer_completed",
            {
                "message": "Synthesizer 已生成回答",
                "answer_source": synthesis["answer_source"],
                "llm_used": synthesis["llm_used"],
                "llm_error": synthesis["llm_error"],
            },
        )

        response = ChatResponse(
            answer=answer,
            answer_source=synthesis["answer_source"],
            llm_used=synthesis["llm_used"],
            llm_error=synthesis["llm_error"],
            route=route_result,
            plan=plan,
            tool_results=tool_results,
            trace=tracer.snapshot(),
        )
        response.run_id = response.trace.trace_id

        yield sse_event("evaluation_started", {"message": "Evaluation 正在评估质量"})
        evaluation_start = time.perf_counter()
        try:
            response.evaluation = RuleBasedEvaluator().evaluate(
                {
                    "query": request.query,
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
            yield sse_event(
                "evaluation_completed",
                {
                    "message": "Evaluation 已完成质量评估",
                    "overall_score": response.evaluation.overall_score,
                },
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
            yield sse_event(
                "evaluation_completed",
                {
                    "message": "Evaluation 执行失败",
                    "status": "failed",
                    "error": "evaluation_failed",
                },
            )

        evidence_start = time.perf_counter()
        try:
            response.evidence_chain = EvidenceChainBuilder().build(
                {
                    "query": request.query,
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

        try:
            persist_chat_response(request, response)
        except Exception:
            response.trace.persistence_error = "persistence_write_failed"

        yield sse_event(
            "completed",
            {
                "message": "Agent 执行完成",
                "run_id": response.run_id,
                "answer": response.answer,
                "evaluation": response.evaluation.model_dump() if response.evaluation else None,
                "response": response.model_dump(),
            },
        )
    except Exception:
        yield sse_event(
            "error",
            {
                "message": "Agent 流式执行失败",
                "error": "stream_failed",
            },
        )
