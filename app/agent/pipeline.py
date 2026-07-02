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
    tracer.start_stage("safety")
    safety_check = detect_prompt_injection(request.query)
    safety_payload = safety_check.model_dump()
    tracer.end_safety_stage(safety_payload)
    if safety_check.blocked:
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
    tracer.end_executor_stage(
        output=f"tools_called={len([r for r in tool_results if r.tool != 'none'])}",
        tool_results=tool_results,
    )

    # ── 4. Synthesizer ──
    tracer.start_stage("synthesizer")
    trace_summary = tracer.snapshot().model_dump()
    synthesizer = AnswerSynthesizer()
    synthesis = synthesizer.synthesize(
        request.query,
        route_result,
        plan,
        tool_results,
        trace_summary=trace_summary,
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
