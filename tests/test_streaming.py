import json

from fastapi.testclient import TestClient

from app.tools.log_tool import LogTool
from main import app

client = TestClient(app)


def _stream(query: str):
    response = client.get("/chat/stream", params={"query": query})
    assert response.status_code == 200
    return response


def _events(text: str) -> list[dict]:
    parsed = []
    current_event = ""
    for line in text.splitlines():
        if line.startswith("event: "):
            current_event = line.removeprefix("event: ").strip()
        elif line.startswith("data: "):
            data = json.loads(line.removeprefix("data: "))
            parsed.append({"event": current_event, "data": data})
    return parsed


def test_chat_stream_returns_event_stream():
    response = _stream("什么是配置中心？")

    assert response.headers["content-type"].startswith("text/event-stream")


def test_simple_qa_stream_contains_core_events():
    response = _stream("什么是配置中心？")
    event_names = [event["event"] for event in _events(response.text)]

    for expected in [
        "router_started",
        "router_completed",
        "planner_started",
        "planner_completed",
        "executor_started",
        "synthesizer_started",
        "synthesizer_completed",
        "evaluation_started",
        "evaluation_completed",
        "completed",
    ]:
        assert expected in event_names


def test_complex_troubleshooting_streams_tool_events():
    response = _stream("为什么订单接口报500？")
    events = _events(response.text)
    tool_started = [event for event in events if event["event"] == "tool_started"]
    tool_completed = [event for event in events if event["event"] == "tool_completed"]

    assert [event["data"]["tool_name"] for event in tool_started] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert [event["data"]["tool_name"] for event in tool_completed] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert all(event["data"]["status"] == "success" for event in tool_completed)


def test_tool_failure_streams_failed_tool_completed(monkeypatch):
    def fail_log_tool(self, query, context=""):
        return {
            "tool_name": self.name,
            "status": "failed",
            "result": "",
            "confidence": 0.0,
            "source": "mock_api:/mock/logs",
            "documents": [],
            "error": "file_not_found",
        }

    monkeypatch.setattr(LogTool, "run", fail_log_tool)

    response = _stream("为什么订单接口报500？")
    tool_completed = [
        event["data"]
        for event in _events(response.text)
        if event["event"] == "tool_completed"
    ]
    log_event = [event for event in tool_completed if event["tool_name"] == "log_tool"][0]

    assert log_event["status"] == "failed"
    assert log_event["error"] == "tool_failed"


def test_chat_stream_does_not_call_real_deepseek_api():
    response = _stream("什么是配置中心？")
    completed = [
        event["data"]
        for event in _events(response.text)
        if event["event"] == "completed"
    ][0]

    assert completed["response"]["llm_used"] is False
    assert completed["response"]["answer_source"] == "fallback"
