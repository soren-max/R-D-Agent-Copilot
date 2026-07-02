from fastapi.testclient import TestClient

import app.api.chat as chat_module
from app.persistence.repositories import RunRepository
from main import app


client = TestClient(app)


def _post_chat(query: str) -> dict:
    response = client.post("/chat", json={"query": query})
    assert response.status_code == 200
    return response.json()


def test_post_chat_simple_qa_creates_agent_run():
    data = _post_chat("什么是配置中心？")

    run = RunRepository().get_run(data["run_id"])

    assert run is not None
    assert run["run_id"] == data["trace"]["trace_id"]
    assert run["query"] == "什么是配置中心？"
    assert run["route_type"] == "simple_qa"
    assert run["status"] == "success"


def test_post_chat_complex_troubleshooting_creates_agent_run():
    data = _post_chat("为什么订单接口报500？")

    run = RunRepository().get_run(data["run_id"])

    assert run is not None
    assert run["query"] == "为什么订单接口报500？"
    assert run["route_type"] == "complex_troubleshooting"
    assert run["answer_source"] == data["answer_source"]
    assert run["llm_used"] == data["llm_used"]


def test_run_id_equals_trace_id():
    data = _post_chat("为什么订单接口报500？")

    assert data["run_id"] == data["trace"]["trace_id"]


def test_agent_steps_include_pipeline_stages():
    data = _post_chat("为什么订单接口报500？")

    run = RunRepository().get_run(data["run_id"])

    assert [step["stage"] for step in run["steps"]] == [
        "router",
        "planner",
        "executor",
        "synthesizer",
        "grounding_checker",
        "evaluation",
        "evidence",
    ]
    executor_step = [step for step in run["steps"] if step["stage"] == "executor"][0]
    assert executor_step["engine"] == "langgraph"
    assert "skipped_nodes" in executor_step["output_json"]


def test_complex_troubleshooting_saves_tool_calls():
    data = _post_chat("为什么订单接口报500？")

    run = RunRepository().get_run(data["run_id"])

    assert [tool_call["tool_name"] for tool_call in run["tool_calls"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert [tool_call["node"] for tool_call in run["tool_calls"]] == [
        "log_tool_node",
        "config_tool_node",
        "git_tool_node",
        "rag_tool_node",
    ]
    assert all(tool_call["status"] == "success" for tool_call in run["tool_calls"])
    assert all(tool_call["result_json"]["result"] for tool_call in run["tool_calls"])


def test_llm_fallback_saves_synthesizer_step(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")

    data = _post_chat("什么是配置中心？")
    run = RunRepository().get_run(data["run_id"])
    synthesizer_step = [step for step in run["steps"] if step["stage"] == "synthesizer"][0]

    assert data["answer_source"] == "fallback"
    assert data["llm_error"] == "missing_api_key"
    assert synthesizer_step["engine"] == "fallback"
    assert synthesizer_step["output_json"]["answer_source"] == "fallback"
    assert synthesizer_step["output_json"]["llm_error"] == "missing_api_key"
    assert synthesizer_step["output_json"]["prompt_version"] == "fallback_prompt_v1"
    assert run["evaluation"] is not None


def test_database_write_failure_does_not_break_chat(monkeypatch):
    def fail_persistence(request, response, repository=None):
        raise RuntimeError("database path contains sensitive details")

    monkeypatch.setattr(chat_module, "persist_chat_response", fail_persistence)

    data = _post_chat("为什么订单接口报500？")

    assert data["answer"]
    assert data["run_id"] == data["trace"]["trace_id"]
    assert data["trace"]["persistence_error"] == "persistence_write_failed"
    assert "sensitive" not in data["trace"]["persistence_error"]
