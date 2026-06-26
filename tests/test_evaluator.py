import app.agent.synthesizer as synthesizer_module
from app.eval import RuleBasedEvaluator


def _payload(**overrides):
    payload = {
        "query": "为什么订单接口报500？",
        "route": {"type": "complex_troubleshooting"},
        "plan": {"plan_type": "troubleshooting_plan", "steps": []},
        "tool_results": [
            {
                "tool": "log_tool",
                "tool_name": "log_tool",
                "status": "success",
                "documents": [],
            },
            {
                "tool": "config_tool",
                "tool_name": "config_tool",
                "status": "success",
                "documents": [],
            },
            {
                "tool": "git_tool",
                "tool_name": "git_tool",
                "status": "success",
                "documents": [],
            },
            {
                "tool": "rag_retriever",
                "tool_name": "rag_retriever",
                "status": "success",
                "documents": [{"title": "订单服务 FAQ"}],
            },
        ],
        "trace": {
            "steps": [
                {"stage": "router", "latency_ms": 10},
                {"stage": "planner", "latency_ms": 10},
                {"stage": "executor", "latency_ms": 50},
                {"stage": "synthesizer", "latency_ms": 30},
            ]
        },
        "answer": "工具证据显示日志里有 500 和 timeout，配置与 Git 代码变更也需要检查。",
    }
    payload.update(overrides)
    return payload


def test_tool_success_rate_is_one_when_all_tools_success():
    result = RuleBasedEvaluator().evaluate(_payload())

    assert result.metrics.tool_success_rate == 1.0


def test_tool_success_rate_decreases_when_tool_failed():
    payload = _payload()
    payload["tool_results"][1]["status"] = "failed"

    result = RuleBasedEvaluator().evaluate(payload)

    assert result.metrics.tool_success_rate == 0.75
    assert "存在工具调用失败或未成功完成" in result.issues


def test_trace_completeness_is_one_when_core_stages_exist():
    result = RuleBasedEvaluator().evaluate(_payload())

    assert result.metrics.trace_completeness == 1.0


def test_trace_completeness_decreases_when_stage_missing():
    payload = _payload(trace={"steps": [{"stage": "router"}, {"stage": "planner"}, {"stage": "executor"}]})

    result = RuleBasedEvaluator().evaluate(payload)

    assert result.metrics.trace_completeness == 0.75
    assert "Trace 缺少核心执行阶段" in result.issues


def test_simple_qa_with_rag_documents_has_high_rag_relevance():
    payload = _payload(
        route={"type": "simple_qa"},
        tool_results=[
            {
                "tool": "rag_retriever",
                "tool_name": "rag_retriever",
                "status": "success",
                "documents": [{"title": "配置中心说明"}],
            }
        ],
    )

    result = RuleBasedEvaluator().evaluate(payload)

    assert result.metrics.rag_relevance >= 0.8


def test_answer_groundedness_is_high_when_answer_contains_evidence_keywords():
    payload = _payload(answer="日志显示 500 timeout，配置和 Git 代码变更提供了工具证据。")

    result = RuleBasedEvaluator().evaluate(payload)

    assert result.metrics.answer_groundedness >= 0.75


def test_latency_score_uses_thresholds():
    evaluator = RuleBasedEvaluator()

    assert evaluator.evaluate(_payload(trace={"total_latency_ms": 1000})).metrics.latency_score == 1.0
    assert evaluator.evaluate(_payload(trace={"total_latency_ms": 3000})).metrics.latency_score == 0.8
    assert evaluator.evaluate(_payload(trace={"total_latency_ms": 8000})).metrics.latency_score == 0.6
    assert evaluator.evaluate(_payload(trace={"total_latency_ms": 8001})).metrics.latency_score == 0.3
    assert evaluator.evaluate(_payload(trace={})).metrics.latency_score == 0.5


def test_overall_score_is_between_zero_and_one():
    result = RuleBasedEvaluator().evaluate(_payload())

    assert 0 <= result.overall_score <= 1


def test_evaluator_does_not_call_real_deepseek_api(monkeypatch):
    def fail_if_called(self, system_prompt, user_prompt):
        raise AssertionError("Evaluator must not call DeepSeek")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fail_if_called)

    result = RuleBasedEvaluator().evaluate(_payload())

    assert result.overall_score > 0
