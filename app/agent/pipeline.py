"""
Agent Pipeline — 全流程编排。

完整链路：Router → Planner → Executor → Synthesizer → Trace
所有 API 端点通过此入口调用 Agent 能力。
"""

from __future__ import annotations

from app.agent.executor import Executor
from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.agent.synthesizer import AnswerSynthesizer
from app.core.models import ChatRequest, ChatResponse
from app.core.trace import Tracer
from app.resume import CheckpointStore, RunCheckpoint
from apps.api.app.context import ContextManager
from apps.api.app.rag.grounding_checker import GroundingChecker
from apps.api.app.safety.prompt_injection import detect_prompt_injection
from apps.api.app.safety.tool_policy import validate_plan_tools

_DEFAULT_LLM_USAGE = {
    "provider": "deepseek",
    "model": "deepseek-v4-flash",
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "estimated_cost": 0,
    "currency": "USD",
    "latency_ms": 0,
    "source": "fallback",
}


def run_pipeline(request: ChatRequest) -> ChatResponse:
    """执行完整 Agent 链路并返回结果。"""
    tracer = Tracer()
    checkpoint_store = CheckpointStore()
    run_id = tracer.snapshot().trace_id
    checkpoint = RunCheckpoint(run_id=run_id, query=request.query, status="running")
    checkpoint_created = _safe_save_checkpoint(checkpoint_store, checkpoint)
    tracer.start_stage("safety")
    safety_check = detect_prompt_injection(request.query)
    safety_payload = safety_check.model_dump()
    tracer.end_safety_stage(safety_payload)
    if safety_check.blocked:
        checkpoint.status = "failed"
        checkpoint.last_error = "safety_blocked"
        _safe_save_checkpoint(checkpoint_store, checkpoint)
        answer = "当前请求存在高风险安全问题，已阻止执行工具。请移除越权、密钥泄露或破坏性操作后再提交排障问题。"
        tracer.set_final_answer(answer)
        snapshot = tracer.snapshot()
        return ChatResponse(
            answer=answer,
            answer_source="safety_guard",
            llm_used=False,
            llm_error="safety_blocked",
            llm_usage=_DEFAULT_LLM_USAGE,
            route={"type": "simple_qa", "intent": "safety_risk", "confidence": 1.0, "reason": "safety blocked"},
            plan={"plan_type": "safety_blocked", "task_type": "safety_risk", "steps": []},
            tool_results=[],
            trace=snapshot,
            safety=safety_payload,
        )

    # ── 1. Router ──
    tracer.start_stage("router")
    router = IntentRouter()
    route_result = router.route(request.query)
    checkpoint.route = route_result.model_dump()
    _safe_save_checkpoint(checkpoint_store, checkpoint)
    tracer.end_stage(
        "router",
        output=f"type={route_result.type}, intent={route_result.intent}, confidence={route_result.confidence}",
        prompt_name=route_result.prompt_name,
        prompt_version=route_result.prompt_version,
        model=route_result.model,
        raw_llm_output=route_result.raw_llm_output,
        parsed_output=route_result.parsed_output,
        error_message=route_result.error_message,
        fallback_used=route_result.fallback_used,
    )

    # ── 2. Planner ──
    tracer.start_stage("planner")
    planner = Planner()
    plan = planner.plan(request.query, route_result)
    checkpoint.plan = plan.model_dump()
    checkpoint.pending_steps = [step.id for step in plan.steps]
    _safe_save_checkpoint(checkpoint_store, checkpoint)
    tool_policy = validate_plan_tools(plan, safety_check)
    safety_payload = {
        **safety_payload,
        "blocked_tools": tool_policy.blocked_tools,
        "tool_policy_reasons": tool_policy.reasons,
    }
    tracer.end_stage(
        "planner",
        output=f"plan_type={plan.plan_type}, task_type={plan.task_type}, steps={len(plan.steps)}",
        prompt_name=plan.prompt_name,
        prompt_version=plan.prompt_version,
        model=plan.model,
        raw_llm_output=plan.raw_llm_output,
        parsed_output=plan.parsed_output,
        error_message=plan.error_message,
        fallback_used=plan.fallback_used,
    )
    if not tool_policy.allowed:
        checkpoint.status = "failed"
        checkpoint.last_error = "tool_policy_blocked"
        _safe_save_checkpoint(checkpoint_store, checkpoint)
        answer = "当前请求触发安全工具策略，已阻止执行操作型工具。建议仅基于知识库说明进行安全边界确认。"
        tracer.start_stage("synthesizer")
        tracer.end_synthesizer_stage(
            answer_source="safety_guard",
            llm_used=False,
            llm_error="tool_policy_blocked",
            prompt_name="safety_guard",
            prompt_version="safety_guard_v060",
            llm_usage=_DEFAULT_LLM_USAGE,
        )
        tracer.set_final_answer(answer)
        snapshot = tracer.snapshot()
        return ChatResponse(
            answer=answer,
            answer_source="safety_guard",
            llm_used=False,
            llm_error="tool_policy_blocked",
            llm_usage=_DEFAULT_LLM_USAGE,
            route=route_result,
            plan=plan,
            tool_results=[],
            trace=snapshot,
            safety=safety_payload,
        )

    # ── 3. Executor ──
    tracer.start_stage("executor")
    executor = Executor()
    tool_results = executor.execute(request.query, plan)
    for result in tool_results:
        if result.status in {"success", "partial_success"} and result.step_id not in checkpoint.completed_steps:
            checkpoint.completed_steps.append(result.step_id)
        checkpoint.pending_steps = [
            step.id for step in plan.steps if step.id not in set(checkpoint.completed_steps)
        ]
        if result.status == "failed" and result.error:
            checkpoint.last_error = result.error
            checkpoint.status = "resumable"
        _safe_save_checkpoint(checkpoint_store, checkpoint)
    tracer.end_executor_stage(
        output=f"tools_called={len([r for r in tool_results if r.tool != 'none'])}",
        tool_results=tool_results,
    )

    # ── 4. Synthesizer ──
    tracer.start_stage("synthesizer")
    trace_summary = tracer.snapshot().model_dump()
    context_package = ContextManager().build(
        query=request.query,
        route=route_result.model_dump(),
        plan=plan.model_dump(),
        tool_results=[result.model_dump() for result in tool_results],
        trace_summary=trace_summary,
    )
    checkpoint.tool_evidence_summary = _tool_evidence_summary(tool_results)
    checkpoint.rag_evidence_summary = _rag_evidence_summary(tool_results)
    checkpoint.context_metadata = context_package.metadata.model_dump()
    _safe_save_checkpoint(checkpoint_store, checkpoint)
    synthesizer = AnswerSynthesizer()
    synthesis = synthesizer.synthesize(
        request.query,
        route_result,
        plan,
        tool_results,
        trace_summary=trace_summary,
        context_package=context_package,
    )
    answer = synthesis.get("answer", "")
    llm_usage = synthesis.get("llm_usage", _DEFAULT_LLM_USAGE)
    tracer.end_synthesizer_stage(
        answer_source=synthesis.get("answer_source", "fallback"),
        llm_used=synthesis.get("llm_used", False),
        llm_error=synthesis.get("llm_error"),
        prompt_name=synthesis.get("prompt_name", ""),
        prompt_version=synthesis.get("prompt_version", "unknown"),
        model=synthesis.get("model", ""),
        raw_llm_output=synthesis.get("raw_llm_output", ""),
        parsed_output=synthesis.get("parsed_output"),
        error_message=synthesis.get("error_message", ""),
        llm_usage=llm_usage,
        context_metadata=context_package.metadata.model_dump(),
        checkpoint_created=checkpoint_created,
        checkpoint_status=checkpoint.status,
    )

    rag_evidence = next(
        (
            result.rag_metadata.get("evidence", [])
            for result in tool_results
            if result.tool == "rag_retriever" or result.tool_name == "rag_retriever"
        ),
        [],
    )
    grounding_evidence = [*rag_evidence, *_tool_results_to_grounding_evidence(tool_results)]
    tracer.start_stage("grounding_checker")
    grounding_check = GroundingChecker().check(answer, grounding_evidence).model_dump()
    tracer.end_grounding_checker_stage(grounding_check)
    tracer.set_final_answer(answer)
    checkpoint.status = "completed"
    checkpoint.pending_steps = []
    _safe_save_checkpoint(checkpoint_store, checkpoint)

    return ChatResponse(
        answer=answer,
        answer_source=synthesis.get("answer_source", "fallback"),
        llm_used=synthesis.get("llm_used", False),
        llm_error=synthesis.get("llm_error"),
        llm_usage=llm_usage,
        route=route_result,
        plan=plan,
        tool_results=tool_results,
        trace=tracer.snapshot(),
        grounded_claims=grounding_check.get("grounded_claims", []),
        unsupported_claims=grounding_check.get("unsupported_claims", []),
        grounding_check=grounding_check,
        safety=safety_payload,
    )


def _tool_results_to_grounding_evidence(tool_results) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for result in tool_results:
        if result.tool in {"rag_retriever", "none"}:
            continue
        if result.status != "success" or not result.result:
            continue
        evidence.append({
            "source": result.source,
            "chunk_id": f"{result.tool}:{result.step_id}",
            "content_excerpt": result.result[:500],
            "score": result.confidence,
        })
    return evidence


def _safe_save_checkpoint(store: CheckpointStore, checkpoint: RunCheckpoint) -> bool:
    try:
        store.save(checkpoint)
        return True
    except Exception as exc:
        checkpoint.last_error = type(exc).__name__
        return False


def _tool_evidence_summary(tool_results) -> str:
    summaries = []
    for result in tool_results:
        if result.tool == "rag_retriever":
            continue
        if result.result:
            summaries.append(f"{result.tool_name or result.tool}:{result.result[:160]}")
        elif result.error:
            summaries.append(f"{result.tool_name or result.tool}:error={result.error}")
    return "\n".join(summaries)[:1200]


def _rag_evidence_summary(tool_results) -> str:
    rag_result = next((result for result in tool_results if result.tool == "rag_retriever"), None)
    if rag_result is None:
        return ""
    sources = ",".join(dict.fromkeys(str(doc.get("source", "")) for doc in rag_result.documents if doc.get("source")))
    return f"documents={len(rag_result.documents)} sources={sources} status={rag_result.rag_metadata.get('grounding_status', '')}"[:1200]
