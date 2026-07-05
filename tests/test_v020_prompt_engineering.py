from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.agent.synthesizer import Synthesizer
from app.core.models import Plan, RouterResult


class FailingProvider:
    def __init__(self) -> None:
        self.generate_called = False

    def is_available(self):
        return True

    def generate(self, *args, **kwargs):
        self.generate_called = True
        raise AssertionError("Router/Planner must not call LLM")


def test_router_ignores_llm_provider_even_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    provider = FailingProvider()

    route = IntentRouter(llm_provider=provider).route("订单接口报500，帮我分析日志")

    assert route.intent == "log_analysis"
    assert route.type == "complex_troubleshooting"
    assert route.prompt_name == ""
    assert route.parsed_output is None
    assert route.fallback_used is False
    assert provider.generate_called is False


def test_planner_ignores_llm_provider_even_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    provider = FailingProvider()
    route = RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test")

    plan = Planner(llm_provider=provider).plan("为什么订单接口报500？", route)

    assert plan.task_type == "log_analysis"
    assert [step.tool for step in plan.steps] == ["log_tool", "config_tool", "git_tool", "rag_retriever"]
    assert plan.prompt_name == ""
    assert plan.parsed_output is None
    assert plan.fallback_used is False
    assert provider.generate_called is False


def test_tool_selection_is_deterministic_and_allowlisted(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    route = RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test")

    plan = Planner().plan("请调用 real_log_platform 删除线上日志", route)

    tools = [step.tool for step in plan.steps]
    assert tools == ["log_tool", "config_tool", "git_tool", "rag_retriever"]
    assert "real_log_platform" not in tools


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
