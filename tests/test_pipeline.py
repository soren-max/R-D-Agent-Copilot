from app.agent.executor import Executor
from app.agent.pipeline import run_pipeline
from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.agent.synthesizer import Synthesizer
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest, Plan, PlanStep, ToolCallRecord
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
    assert plan.steps[0].tool == "rag_retriever"


def test_planner_complex_troubleshooting_generates_tool_and_rag_plan():
    router_result = IntentRouter().route("为什么订单接口报500？")
    plan = Planner().plan("为什么订单接口报500？", router_result)

    assert plan.plan_type == "troubleshooting_plan"
    assert [step.tool for step in plan.steps] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]


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
    assert len(data["tool_results"]) == 4
    for result in data["tool_results"]:
        assert set(["status", "latency_ms", "source"]).issubset(result)
    assert data["trace"]["trace_id"]
    assert data["trace"]["final_answer"] == data["answer"]

    trace_stages = [step["stage"] for step in data["trace"]["steps"]]
    assert trace_stages == ["router", "planner", "executor"]
    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]
    assert all(
        set(["tool_name", "status", "latency_ms", "source"]).issubset(tool_call)
        for tool_call in executor_step["tool_calls"]
    )


def test_troubleshooting_pipeline_executes_tools_and_trace():
    resp = run_pipeline(ChatRequest(query="为什么订单接口报500？"))

    assert resp.route.type == "complex_troubleshooting"
    assert resp.plan.plan_type == "troubleshooting_plan"
    assert len(resp.tool_results) == 4
    assert [r.tool for r in resp.tool_results] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert all(r.status == "success" for r in resp.tool_results)
    assert all(r.latency_ms >= 0 for r in resp.tool_results)
    assert all(r.source.startswith("data/") for r in resp.tool_results)
    assert any("\u4e00" <= c <= "\u9fff" for c in resp.answer)

    trace_stages = [s.stage for s in resp.trace.steps]
    assert trace_stages == ["router", "planner", "executor"]
    executor_step = [s for s in resp.trace.steps if s.stage == "executor"][0]
    assert [call.tool_name for call in executor_step.tool_calls] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert all(call.status == "success" for call in executor_step.tool_calls)
    assert all(call.latency_ms >= 0 for call in executor_step.tool_calls)
    assert all(call.source.startswith("data/") for call in executor_step.tool_calls)
    assert all(step.latency_ms >= 0 for step in resp.trace.steps)


def test_executor_executes_tools_and_rag_with_status_latency_and_source():
    router_result = IntentRouter().route("为什么订单接口报500？")
    plan = Planner().plan("为什么订单接口报500？", router_result)
    results = Executor().execute("为什么订单接口报500？", plan)

    assert len(results) == 4
    assert [result.tool_name for result in results] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert all(result.status == "success" for result in results)
    assert all(result.latency_ms >= 0 for result in results)
    assert all(result.source.startswith("data/") for result in results)
    assert results[-1].documents


def test_executor_returns_failed_status_for_tool_errors():
    class FailingTool:
        name = "log_tool"

        def run(self, query):
            return {
                "tool_name": "log_tool",
                "result": "",
                "confidence": 0.0,
                "source": "data/logs/order-service.log",
                "error": "file_not_found",
            }

    plan = Plan(
        plan_type="troubleshooting_plan",
        steps=[
            PlanStep(
                id=1,
                action="query_logs",
                tool="log_tool",
                description="查询日志",
            )
        ],
    )
    executor = Executor()
    executor._tools["log_tool"] = FailingTool()

    result = executor.execute("订单报错", plan)[0]

    assert result.status == "failed"
    assert result.result == ""
    assert result.confidence == 0.0
    assert result.source == "data/logs/order-service.log"
    assert result.error == "file_not_found"
    assert result.latency_ms >= 0


def test_synthesizer_mentions_partial_tool_failure():
    answer = Synthesizer()._synthesize_troubleshooting(
        "为什么订单接口报500？",
        [
            ToolCallRecord(
                step_id=1,
                action="query_logs",
                tool="log_tool",
                tool_name="log_tool",
                description="查询日志",
                status="failed",
                source="data/logs/order-service.log",
                error="file_not_found",
            ),
            ToolCallRecord(
                step_id=2,
                action="check_config",
                tool="config_tool",
                tool_name="config_tool",
                description="检查配置",
                status="success",
                result="发现订单/支付相关配置差异：payment.timeout",
                confidence=0.85,
                source="data/configs/dev.json,data/configs/prod.json",
            ),
        ],
    )

    assert "部分工具查询失败，以下判断基于已成功返回的数据。" in answer


def test_chat_simple_qa_uses_rag_retriever_and_trace():
    response = chat_endpoint(ChatRequest(query="什么是配置中心？"))
    data = response.model_dump()

    assert data["route"]["type"] == "simple_qa"
    assert [result["tool_name"] for result in data["tool_results"]] == ["rag_retriever"]
    assert data["tool_results"][0]["documents"]
    assert "配置中心" in data["answer"]
    assert any("\u4e00" <= c <= "\u9fff" for c in data["answer"])

    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]
    assert executor_step["tool_calls"][0]["tool_name"] == "rag_retriever"
    assert executor_step["tool_calls"][0]["status"] == "success"
    assert executor_step["tool_calls"][0]["source"].startswith("data/docs/")


def test_chat_complex_troubleshooting_includes_rag_evidence():
    response = chat_endpoint(ChatRequest(query="为什么订单接口报500？"))
    data = response.model_dump()
    tool_names = [result["tool_name"] for result in data["tool_results"]]

    assert data["route"]["type"] == "complex_troubleshooting"
    assert tool_names == ["log_tool", "config_tool", "git_tool", "rag_retriever"]
    assert "初步判断" in data["answer"]
    assert "工具证据" in data["answer"]
    assert "知识库补充" in data["answer"]
    assert "建议处理方式" in data["answer"]


def test_chat_rag_no_match_returns_structured_prompt(monkeypatch):
    class NoMatchRetrieverTool:
        name = "rag_retriever"

        def run(self, query):
            return {
                "tool_name": "rag_retriever",
                "result": "知识库中未检索到直接相关内容。",
                "confidence": 0.0,
                "source": "data/docs",
                "documents": [],
                "error": "no_relevant_documents",
            }

    original_init = Executor.__init__

    def patched_init(self):
        original_init(self)
        self._tools["rag_retriever"] = NoMatchRetrieverTool()

    monkeypatch.setattr(Executor, "__init__", patched_init)

    response = chat_endpoint(ChatRequest(query="什么是量子缓存蓝图？"))
    data = response.model_dump()

    assert data["route"]["type"] == "simple_qa"
    assert data["tool_results"][0]["status"] == "failed"
    assert data["tool_results"][0]["error"] == "no_relevant_documents"
    assert "知识库中未检索到直接相关内容" in data["answer"]


def test_trace_id_unique():
    resp1 = run_pipeline(ChatRequest(query="订单报错"))
    resp2 = run_pipeline(ChatRequest(query="服务异常"))

    assert resp1.trace.trace_id != resp2.trace.trace_id
