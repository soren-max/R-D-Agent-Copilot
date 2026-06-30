from typing import Any

from app.core.models import ChatRequest, ChatResponse, ToolCallRecord, TraceStep
from app.persistence.repositories import RunRepository


def persist_chat_response(
    request: ChatRequest,
    response: ChatResponse,
    repository: RunRepository | None = None,
) -> None:
    repo = repository or RunRepository()
    run_id = response.trace.trace_id

    step_by_stage: dict[str, dict[str, Any]] = {}
    total_latency_ms = sum(step.latency_ms for step in response.trace.steps)

    repo.create_run(
        run_id=run_id,
        query=request.query,
        route_type=response.route.type,
        answer_source=response.answer_source,
        llm_used=response.llm_used,
        status="success",
        total_latency_ms=total_latency_ms,
    )

    for trace_step in response.trace.steps:
        step = repo.create_step(
            run_id=run_id,
            stage=trace_step.stage,
            engine=trace_step.engine or None,
            input_json=_stage_input_json(trace_step.stage, request, response),
            output_json=_stage_output_json(trace_step, response),
            latency_ms=trace_step.latency_ms,
            status="success",
        )
        step_by_stage[trace_step.stage] = step

    executor_step_id = step_by_stage.get("executor", {}).get("id")
    for tool_result in response.tool_results:
        if tool_result.tool == "none":
            continue

        repo.create_tool_call(
            run_id=run_id,
            step_id=executor_step_id,
            node=tool_result.node,
            tool_name=tool_result.tool_name or tool_result.tool,
            status=tool_result.status,
            source=tool_result.source,
            confidence=tool_result.confidence,
            retry_count=tool_result.retry_count,
            error=tool_result.error or None,
            latency_ms=tool_result.latency_ms,
            result_json=_tool_result_json(tool_result),
        )

    if response.evaluation is not None:
        repo.create_evaluation(
            run_id=run_id,
            overall_score=response.evaluation.overall_score,
            metrics_json=response.evaluation.metrics.model_dump(),
            issues_json=response.evaluation.issues,
            suggestions_json=response.evaluation.suggestions,
        )


def _stage_input_json(
    stage: str,
    request: ChatRequest,
    response: ChatResponse,
) -> dict[str, Any]:
    if stage == "router":
        return {"query": request.query}
    if stage == "planner":
        return {"query": request.query, "route": response.route.model_dump()}
    if stage == "executor":
        return {"query": request.query, "plan": response.plan.model_dump()}
    if stage == "synthesizer":
        return {
            "query": request.query,
            "route": response.route.model_dump(),
            "plan": response.plan.model_dump(),
            "tool_results": [result.model_dump() for result in response.tool_results],
        }
    if stage == "evaluation":
        return {
            "query": request.query,
            "route": response.route.model_dump(),
            "plan": response.plan.model_dump(),
            "tool_results": [result.model_dump() for result in response.tool_results],
            "answer": response.answer,
        }
    if stage == "evidence":
        return {
            "query": request.query,
            "route": response.route.model_dump(),
            "plan": response.plan.model_dump(),
            "tool_results": [result.model_dump() for result in response.tool_results],
            "answer": response.answer,
            "evaluation": response.evaluation.model_dump() if response.evaluation else None,
        }
    return {"query": request.query}


def _stage_output_json(trace_step: TraceStep, response: ChatResponse) -> dict[str, Any]:
    data: dict[str, Any] = {
        "output": trace_step.output,
        "graph_name": trace_step.graph_name,
        "fallback_used": trace_step.fallback_used,
        "llm_used": trace_step.llm_used,
        "llm_error": trace_step.llm_error,
        "prompt_version": trace_step.prompt_version,
        "llm_usage": trace_step.llm_usage,
    }
    if trace_step.stage == "router":
        data["route"] = response.route.model_dump()
    elif trace_step.stage == "planner":
        data["plan"] = response.plan.model_dump()
    elif trace_step.stage == "executor":
        data["tool_results"] = [result.model_dump() for result in response.tool_results]
        data["tool_calls"] = [tool_call.model_dump() for tool_call in trace_step.tool_calls]
        data["skipped_nodes"] = [node.model_dump() for node in trace_step.skipped_nodes]
    elif trace_step.stage == "synthesizer":
        data["answer_source"] = response.answer_source
        data["llm_used"] = response.llm_used
        data["llm_error"] = response.llm_error
        data["llm_usage"] = response.llm_usage
    elif trace_step.stage == "evaluation":
        data["overall_score"] = trace_step.overall_score
        data["evaluation_error"] = trace_step.evaluation_error
        data["evaluation"] = response.evaluation.model_dump() if response.evaluation else None
    elif trace_step.stage == "evidence":
        data["overall_confidence"] = trace_step.overall_confidence
        data["evidence_count"] = trace_step.evidence_count
        data["evidence_chain"] = response.evidence_chain.model_dump() if response.evidence_chain else None
    return data


def _tool_result_json(tool_result: ToolCallRecord) -> dict[str, Any]:
    return {
        "step_id": tool_result.step_id,
        "action": tool_result.action,
        "description": tool_result.description,
        "result": tool_result.result,
        "documents": tool_result.documents,
    }
