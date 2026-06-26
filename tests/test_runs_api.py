from fastapi.testclient import TestClient

from app.persistence.repositories import RunRepository
from main import app


client = TestClient(app)


def _post_chat(query: str) -> dict:
    response = client.post("/chat", json={"query": query})
    assert response.status_code == 200
    return response.json()


def test_get_runs_includes_chat_run():
    chat = _post_chat("什么是配置中心？")

    response = client.get("/runs")

    assert response.status_code == 200
    runs = response.json()["runs"]
    assert any(run["run_id"] == chat["run_id"] for run in runs)


def test_get_runs_limit_one_returns_one_run():
    _post_chat("什么是配置中心？")
    _post_chat("为什么订单接口报500？")

    response = client.get("/runs?limit=1")

    assert response.status_code == 200
    assert len(response.json()["runs"]) == 1


def test_get_runs_limit_above_100_is_clamped():
    repo = RunRepository()
    for index in range(105):
        repo.create_run(run_id=f"manual-run-{index}", query=f"query {index}")

    response = client.get("/runs?limit=101")

    assert response.status_code == 200
    assert len(response.json()["runs"]) == 100


def test_get_run_returns_run_steps_and_tool_calls():
    chat = _post_chat("为什么订单接口报500？")

    response = client.get(f"/runs/{chat['run_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["run"]["run_id"] == chat["run_id"]
    assert [step["stage"] for step in data["steps"]] == [
        "router",
        "planner",
        "executor",
        "synthesizer",
    ]
    assert [tool_call["tool_name"] for tool_call in data["tool_calls"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert data["steps"][0]["input"]
    assert data["steps"][0]["output"]


def test_get_missing_run_returns_404():
    response = client.get("/runs/not-a-real-run")

    assert response.status_code == 404
    assert response.json() == {"detail": "run_not_found"}


def test_runs_api_does_not_expose_deepseek_api_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key")
    chat = _post_chat("为什么订单接口报500？")

    list_response = client.get("/runs")
    detail_response = client.get(f"/runs/{chat['run_id']}")

    assert "super-secret-key" not in list_response.text
    assert "DEEPSEEK_API_KEY" not in list_response.text
    assert "super-secret-key" not in detail_response.text
    assert "DEEPSEEK_API_KEY" not in detail_response.text
