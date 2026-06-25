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


def run_pipeline(request: ChatRequest) -> ChatResponse:
    """执行完整 Agent 链路并返回结果。"""
    tracer = Tracer()

    # ── 1. Router ──
    tracer.start_stage("router")
    router = IntentRouter()
    route_result = router.route(request.query)
    tracer.end_stage("router", output=f"type={route_result.type}, confidence={route_result.confidence}")

    # ── 2. Planner ──
    tracer.start_stage("planner")
    planner = Planner()
    plan = planner.plan(request.query, route_result)
    tracer.end_stage("planner", output=f"plan_type={plan.plan_type}, steps={len(plan.steps)}")

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
    answer = synthesis["answer"]
    tracer.end_synthesizer_stage(
        answer_source=synthesis["answer_source"],
        llm_used=synthesis["llm_used"],
        llm_error=synthesis["llm_error"],
    )
    tracer.set_final_answer(answer)

    return ChatResponse(
        answer=answer,
        answer_source=synthesis["answer_source"],
        llm_used=synthesis["llm_used"],
        llm_error=synthesis["llm_error"],
        route=route_result,
        plan=plan,
        tool_results=tool_results,
        trace=tracer.snapshot(),
    )
