from fastapi.testclient import TestClient

from main import app


def test_v070_health_returns_deployment_checks():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.8.0"
    assert data["status"] in {"ok", "degraded"}
    assert data["checks"]
    assert any(check["name"] == "database" for check in data["checks"])


def test_v070_config_check_is_safe_and_descriptive():
    response = TestClient(app).get("/config/check")

    assert response.status_code == 200
    data = response.json()
    assert data["llm"]["api_key_configured"] is False
    assert "api_key" not in data["llm"]
    assert data["rag"]["kb_documents"] >= 6
    assert data["rag"]["embedding_provider"] == "local"
    assert data["rag"]["rerank_provider"] == "local"


def test_v070_trace_export_returns_persisted_run():
    client = TestClient(app)
    chat_response = client.post("/chat", json={"query": "port already in use 服务启动失败"})
    run_id = chat_response.json()["run_id"]

    response = client.get(f"/trace/export/{run_id}")

    assert response.status_code == 200
    export = response.json()["trace_export"]
    assert export["run_id"] == run_id
    assert export["query"] == "port already in use 服务启动失败"
    assert export["steps"]
    assert export["tool_calls"]


def test_v070_trace_export_returns_404_for_unknown_run():
    response = TestClient(app).get("/trace/export/not-found")

    assert response.status_code == 404
    assert response.json()["detail"] == "run_not_found"


def test_v070_eval_report_lists_local_reports():
    response = TestClient(app).get("/eval/report")

    assert response.status_code == 200
    reports = response.json()["reports"]
    assert "planning_eval" in reports
    assert "bad_case_replay" in reports
    assert "rag_failed_cases" in reports
    assert reports["planning_eval"]["path"] == "data/eval/planning_eval_report.md"

