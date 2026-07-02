from fastapi.testclient import TestClient

import app.api.chat as chat_module
from app.persistence.repositories import RunRepository
from main import app


client = TestClient(app)


def _post_chat(query: str) -> dict:
    response = client.post("/chat", json={"query": query})
    assert response.status_code == 200
    return response.json()


def test_post_chat_simple_qa_returns_evaluation():
    data = _post_chat("什么是配置中心？")

    assert data["evaluation"] is not None
    assert 0 <= data["evaluation"]["overall_score"] <= 1
    assert "tool_success_rate" in data["evaluation"]["metrics"]
    assert "latency_breakdown" in data["evaluation"]
    assert data["evaluation"]["latency_breakdown"]["total_ms"] >= 0
    assert data["evaluation"]["latency_breakdown"]["bottleneck_stage"]


def test_post_chat_complex_troubleshooting_returns_evaluation():
    data = _post_chat("为什么订单接口报500？")

    assert data["evaluation"] is not None
    assert 0 <= data["evaluation"]["overall_score"] <= 1
    assert data["evaluation"]["metrics"]["trace_completeness"] == 1.0


def test_trace_steps_include_evaluation_stage():
    data = _post_chat("为什么订单接口报500？")

    stages = [step["stage"] for step in data["trace"]["steps"]]

    assert stages == ["safety", "router", "planner", "executor", "synthesizer", "grounding_checker", "evaluation", "evidence"]
    evaluation_step = [step for step in data["trace"]["steps"] if step["stage"] == "evaluation"][0]
    assert evaluation_step["engine"] == "rule_based"
    assert 0 <= evaluation_step["overall_score"] <= 1


def test_persisted_run_includes_evaluation():
    data = _post_chat("为什么订单接口报500？")

    run = RunRepository().get_run(data["run_id"])

    assert run["evaluation"] is not None
    assert run["evaluation"]["overall_score"] == data["evaluation"]["overall_score"]
    assert run["evaluation"]["metrics"]["tool_success_rate"] == data["evaluation"]["metrics"]["tool_success_rate"]


def test_get_run_returns_evaluation():
    data = _post_chat("为什么订单接口报500？")

    response = client.get(f"/runs/{data['run_id']}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["evaluation"] is not None
    assert detail["evaluation"]["overall_score"] == data["evaluation"]["overall_score"]
    assert detail["evaluation"]["latency_breakdown"]["tools_ms"] >= 0
    assert detail["evaluation"]["latency_breakdown"]["synthesizer_ms"] >= 0


def test_get_runs_list_returns_evaluation_score():
    data = _post_chat("为什么订单接口报500？")

    response = client.get("/runs")

    assert response.status_code == 200
    run = [item for item in response.json()["runs"] if item["run_id"] == data["run_id"]][0]
    assert run["evaluation_score"] == data["evaluation"]["overall_score"]


def test_get_run_without_evaluation_returns_null():
    RunRepository().create_run(run_id="manual-run", query="manual query")

    response = client.get("/runs/manual-run")

    assert response.status_code == 200
    assert response.json()["evaluation"] is None


def test_evaluation_failure_does_not_break_chat(monkeypatch):
    def fail_evaluation(self, payload):
        raise RuntimeError("secret evaluation internals")

    monkeypatch.setattr(chat_module.RuleBasedEvaluator, "evaluate", fail_evaluation)

    data = _post_chat("为什么订单接口报500？")

    assert data["answer"]
    assert data["evaluation"] is None
    assert data["trace"]["evaluation_error"] == "evaluation_failed"
    evaluation_step = [step for step in data["trace"]["steps"] if step["stage"] == "evaluation"][0]
    assert evaluation_step["evaluation_error"] == "evaluation_failed"
    assert "secret" not in evaluation_step["evaluation_error"]


def test_evaluation_passes_without_real_deepseek_api(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    data = _post_chat("什么是配置中心？")

    assert data["llm_used"] is False
    assert data["evaluation"] is not None
