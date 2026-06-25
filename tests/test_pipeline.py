from app.agent.pipeline import run_pipeline
from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest
from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool
from main import app


def test_router_identifies_simple_qa():
    result = IntentRouter().route("什么是配置中心")

    assert result.type == "simple_qa"
    assert 0 <= result.confidence <= 1
    assert result.reason


def test_router_identifies_complex_troubleshooting():
    result = IntentRouter().route("为什么订单接口报500？")

    assert result.type == "complex_troubleshooting"
    assert 0 <= result.confidence <= 1
    assert result.reason


def test_planner_simple_qa_generates_single_step_plan():
    router_result = IntentRouter().route("什么是配置中心")
    plan = Planner().plan("什么是配置中心", router_result)

    assert plan.plan_type == "simple_qa"
    assert len(plan.steps) == 1


def test_planner_complex_troubleshooting_generates_three_step_plan():
    router_result = IntentRouter().route("为什么订单接口报500？")
    plan = Planner().plan("为什么订单接口报500？", router_result)

    assert plan.plan_type == "troubleshooting_plan"
    assert [step.tool for step in plan.steps] == ["log_tool", "config_tool", "git_tool"]


def test_local_data_tools_can_be_called_individually():
    tools = [LogTool(), ConfigTool(), GitTool()]

    for tool in tools:
        result = tool.run("为什么订单接口报500？", context="订单服务")
        assert result["tool_name"] == tool.name
        assert result["result"]
        assert 0 <= result["confidence"] <= 1
        assert result["source"].startswith("data/")


def test_chat_api_returns_day1_acceptance_shape():
    chat_routes = [
        route for route in app.routes
        if getattr(route, "path", None) == "/chat" and "POST" in getattr(route, "methods", set())
    ]
    assert chat_routes

    response = chat_endpoint(ChatRequest(query="为什么订单接口报500？"))
    data = response.model_dump()
    assert set(["answer", "route", "plan", "tool_results", "trace"]).issubset(data)
    assert data["route"]["type"] == "complex_troubleshooting"
    assert data["plan"]["plan_type"] == "troubleshooting_plan"
    assert len(data["tool_results"]) == 3
    assert data["trace"]["trace_id"]
    assert data["trace"]["final_answer"] == data["answer"]

    trace_stages = [step["stage"] for step in data["trace"]["steps"]]
    assert trace_stages == ["router", "planner", "executor"]


def test_troubleshooting_pipeline_executes_tools_and_trace():
    resp = run_pipeline(ChatRequest(query="为什么订单接口报500？"))

    assert resp.route.type == "complex_troubleshooting"
    assert resp.plan.plan_type == "troubleshooting_plan"
    assert len(resp.tool_results) == 3
    assert [r.tool for r in resp.tool_results] == ["log_tool", "config_tool", "git_tool"]
    assert all(r.status == "success" for r in resp.tool_results)
    assert all(r.source.startswith("data/") for r in resp.tool_results)
    assert any("\u4e00" <= c <= "\u9fff" for c in resp.answer)

    trace_stages = [s.stage for s in resp.trace.steps]
    assert trace_stages == ["router", "planner", "executor"]
    executor_step = [s for s in resp.trace.steps if s.stage == "executor"][0]
    assert executor_step.tool_calls == ["log_tool", "config_tool", "git_tool"]
    assert all(step.latency_ms >= 0 for step in resp.trace.steps)


def test_trace_id_unique():
    resp1 = run_pipeline(ChatRequest(query="订单报错"))
    resp2 = run_pipeline(ChatRequest(query="服务异常"))

    assert resp1.trace.trace_id != resp2.trace.trace_id
