from app.agent.graph import build_execution_graph
from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest


def _plan_for(query: str) -> dict:
    route = IntentRouter().route(query)
    return Planner().plan(query, route).model_dump()


def test_build_execution_graph_compiles():
    graph = build_execution_graph()

    assert graph is not None
    assert hasattr(graph, "invoke")


def test_complex_troubleshooting_plan_executes_all_tools():
    query = "为什么订单接口报500？"
    graph = build_execution_graph()
    result = graph.invoke({
        "query": query,
        "plan": _plan_for(query),
        "tool_results": [],
        "tool_calls": [],
        "skipped_nodes": [],
        "errors": [],
    })

    assert set(["query", "plan", "tool_results", "tool_calls", "skipped_nodes", "errors"]).issubset(result)
    assert [item["tool_name"] for item in result["tool_results"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert [item["node"] for item in result["tool_results"]] == [
        "log_tool_node",
        "config_tool_node",
        "git_tool_node",
        "rag_tool_node",
    ]
    assert [item["tool_name"] for item in result["tool_calls"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert [item["node"] for item in result["tool_calls"]] == [
        "log_tool_node",
        "config_tool_node",
        "git_tool_node",
        "rag_tool_node",
    ]
    assert result["skipped_nodes"] == []
    assert all(item["status"] == "success" for item in result["tool_results"])


def test_simple_qa_plan_executes_only_rag_tool():
    query = "什么是配置中心？"
    graph = build_execution_graph()
    result = graph.invoke({
        "query": query,
        "plan": _plan_for(query),
        "tool_results": [],
        "tool_calls": [],
        "skipped_nodes": [],
        "errors": [],
    })

    assert [item["tool_name"] for item in result["tool_results"]] == ["rag_retriever"]
    assert [item["node"] for item in result["tool_results"]] == ["rag_tool_node"]
    assert [item["tool_name"] for item in result["tool_calls"]] == ["rag_retriever"]
    assert result["skipped_nodes"] == [
        {
            "node": "log_tool_node",
            "tool_name": "log_tool",
            "reason": "tool_not_in_plan",
        },
        {
            "node": "config_tool_node",
            "tool_name": "config_tool",
            "reason": "tool_not_in_plan",
        },
        {
            "node": "git_tool_node",
            "tool_name": "git_tool",
            "reason": "tool_not_in_plan",
        },
    ]
    assert result["tool_results"][0]["documents"]


def test_graph_output_shape_contains_required_fields():
    query = "什么是配置中心？"
    result = build_execution_graph().invoke({
        "query": query,
        "plan": _plan_for(query),
        "tool_results": [],
        "tool_calls": [],
        "skipped_nodes": [],
        "errors": [],
    })

    assert set(["query", "plan", "tool_results", "tool_calls", "skipped_nodes", "errors"]).issubset(result)
    assert result["query"] == query
    assert isinstance(result["plan"], dict)
    assert isinstance(result["tool_results"], list)
    assert isinstance(result["tool_calls"], list)
    assert isinstance(result["skipped_nodes"], list)
    assert isinstance(result["errors"], list)


def test_chat_response_behavior_is_unchanged_by_graph_skeleton():
    response = chat_endpoint(ChatRequest(query="什么是配置中心？"))
    data = response.model_dump()

    assert set(["answer", "route", "plan", "tool_results", "trace", "evaluation"]).issubset(data)
    assert data["route"]["type"] == "simple_qa"
    assert [item["tool_name"] for item in data["tool_results"]] == ["rag_retriever"]
    assert data["evaluation"] is not None
    assert [step["stage"] for step in data["trace"]["steps"]] == [
        "router",
        "planner",
        "executor",
        "synthesizer",
        "evaluation",
    ]
    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]
    assert executor_step["engine"] == "langgraph"
    assert executor_step["graph_name"] == "tool_execution_graph"
    assert [node["tool_name"] for node in executor_step["skipped_nodes"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
    ]
