from fastapi.testclient import TestClient

from main import app


def test_main_app_registers_chat_and_runs_routes():
    routes = [
        (getattr(route, "path", None), getattr(route, "methods", set()))
        for route in app.routes
    ]

    assert any(path == "/chat" and methods and "POST" in methods for path, methods in routes)
    assert any(path == "/runs" and methods and "GET" in methods for path, methods in routes)
    assert any(path == "/runs/{run_id}" and methods and "GET" in methods for path, methods in routes)


def test_post_chat_route_preserves_day1_and_current_fields():
    client = TestClient(app)

    response = client.post("/chat", json={"query": "为什么订单接口报500？"})

    assert response.status_code == 200
    data = response.json()
    assert {
        "answer",
        "route",
        "plan",
        "tool_results",
        "trace",
        "run_id",
        "evaluation",
        "answer_source",
        "llm_used",
    }.issubset(data)
    assert data["route"]["type"] == "complex_troubleshooting"
    assert data["trace"]["trace_id"]
    assert data["run_id"] == data["trace"]["trace_id"]
    assert data["evaluation"] is not None
