import json

from app.agent.planner import Planner, _parse_planner_json
from app.agent.router import IntentRouter, _parse_router_json
from app.agent.synthesizer import Synthesizer
from app.core.config import LLMSettings
from app.core.models import Plan, RouterResult
from app.llms.mock_provider import MockLLMProvider


def test_router_json_parse_outputs_v020_intent_shape():
    parsed = _parse_router_json(
        json.dumps({
            "intent": "log_analysis",
            "confidence": 0.82,
            "reason": "问题包含报错和 500",
        }, ensure_ascii=False)
    )

    assert parsed == {
        "intent": "log_analysis",
        "confidence": 0.82,
        "reason": "问题包含报错和 500",
    }


def test_planner_json_parse_outputs_v020_steps_shape():
    parsed = _parse_planner_json(
        json.dumps({
            "task_type": "log_analysis",
            "steps": [
                {
                    "step_name": "query_logs",
                    "tool": "log_tool",
                    "input": "订单接口 500",
                    "expected_output": "错误日志摘要",
                }
            ],
        }, ensure_ascii=False)
    )

    assert parsed["task_type"] == "log_analysis"
    assert parsed["steps"][0]["tool"] == "log_tool"
    assert parsed["steps"][0]["step_name"] == "query_logs"
    assert parsed["steps"][-1]["tool"] == "rag_retriever"


def test_mock_provider_drives_router_and_planner_without_network():
    provider = MockLLMProvider(
        LLMSettings(enabled=True, provider="mock", model="mock-json-model")
    )

    route = IntentRouter(llm_provider=provider).route("订单接口报500，帮我分析日志")
    plan = Planner(llm_provider=provider).plan("订单接口报500，帮我分析日志", route)

    assert route.intent == "log_analysis"
    assert route.type == "complex_troubleshooting"
    assert route.prompt_name == "router_prompt"
    assert route.parsed_output is not None
    assert plan.task_type == "log_analysis"
    assert [step.tool for step in plan.steps] == ["log_tool", "rag_retriever"]
    assert plan.prompt_name == "planner_prompt"
    assert plan.parsed_output is not None


def test_router_falls_back_when_llm_json_is_invalid():
    class BadProvider:
        settings = LLMSettings(enabled=True, provider="mock")

        def is_available(self):
            return True

        def generate(self, prompt_name, system_prompt, user_prompt):
            class Response:
                content = "not-json"
                raw_output = "not-json"
                model = "bad-model"

            return Response()

    result = IntentRouter(llm_provider=BadProvider()).route("为什么订单接口报500？")

    assert result.type == "complex_troubleshooting"
    assert result.fallback_used is True
    assert result.error_message == "JSONDecodeError"


def test_planner_falls_back_when_llm_uses_unknown_tool():
    class BadProvider:
        settings = LLMSettings(enabled=True, provider="mock")

        def is_available(self):
            return True

        def generate(self, prompt_name, system_prompt, user_prompt):
            content = json.dumps({
                "task_type": "log_analysis",
                "steps": [{
                    "step_name": "call_external_logs",
                    "tool": "real_log_platform",
                    "input": "x",
                    "expected_output": "y",
                }],
            })

            class Response:
                model = "bad-model"

            response = Response()
            response.content = content
            response.raw_output = content
            return response

    route = RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test")
    plan = Planner(llm_provider=BadProvider()).plan("为什么订单接口报500？", route)

    assert plan.plan_type == "troubleshooting_plan"
    assert "real_log_platform" not in [step.tool for step in plan.steps]
    assert plan.fallback_used is True
    assert plan.error_message == "ValueError"


def test_answer_synthesizer_does_not_invent_without_evidence():
    answer = Synthesizer().synthesize(
        "数据库连接池是不是被打满了？",
        RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test"),
        Plan(plan_type="troubleshooting_plan", task_type="log_analysis", steps=[]),
        [],
    )

    assert "暂未获取到工具执行结果" in answer
    assert "连接池被打满" not in answer
    assert "数据库" not in answer
