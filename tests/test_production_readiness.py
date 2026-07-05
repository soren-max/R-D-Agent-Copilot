from pathlib import Path

from fastapi.testclient import TestClient

import app.api.ops as ops_module
from app.core.errors import ErrorCode
from app.core.logging import log_event
from main import app


def test_success_response_contains_success_and_request_id():
    client = TestClient(app)

    response = client.get("/health", headers={"X-Response-Envelope": "true"})
    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["request_id"]
    assert data["data"]["status"] in {"ok", "degraded"}


def test_error_response_contains_error_code_message_and_request_id():
    client = TestClient(app)

    response = client.get("/runs/not-found/checkpoint")
    data = response.json()

    assert response.status_code == 404
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.CHECKPOINT_NOT_FOUND
    assert data["message"]
    assert data["request_id"]


def test_invalid_request_returns_invalid_request():
    client = TestClient(app)

    response = client.post("/chat", json={})
    data = response.json()

    assert response.status_code == 422
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.INVALID_REQUEST
    assert data["request_id"]


def test_unhandled_exception_does_not_expose_traceback(monkeypatch):
    def fail_config_check():
        raise RuntimeError("secret stack details")

    monkeypatch.setattr(ops_module, "build_config_check", fail_config_check)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")
    data = response.json()

    assert response.status_code == 500
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.INTERNAL_ERROR
    assert "traceback" not in response.text.lower()
    assert "secret stack details" not in response.text


def test_request_id_can_be_forwarded_from_header():
    client = TestClient(app)

    response = client.get(
        "/health",
        headers={"X-Request-ID": "req-production-test", "X-Response-Envelope": "true"},
    )
    data = response.json()

    assert response.headers["X-Request-ID"] == "req-production-test"
    assert data["request_id"] == "req-production-test"


def test_structured_log_fields_are_complete():
    payload = log_event(
        event="unit_test_event",
        stage="test",
        request_id="req-1",
        run_id="run-1",
        latency_ms=12,
        error_code="",
        message="structured log test",
    )

    assert set(payload) >= {
        "timestamp",
        "level",
        "request_id",
        "run_id",
        "stage",
        "event",
        "latency_ms",
        "error_code",
        "message",
    }
    assert payload["request_id"] == "req-1"
    assert payload["run_id"] == "run-1"


def test_checkpoint_not_found_returns_unified_error():
    response = TestClient(app).post("/runs/not-found/continue")
    data = response.json()

    assert response.status_code == 404
    assert data["success"] is False
    assert data["error_code"] == ErrorCode.CHECKPOINT_NOT_FOUND


def test_llm_disabled_service_still_runs(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")

    response = TestClient(app).post("/chat", json={"query": "什么是配置中心？"})
    data = response.json()

    assert response.status_code == 200
    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["request_id"]
    assert data["trace"]["request_id"] == data["request_id"]


def test_docker_compose_contains_required_services_and_safe_defaults():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "api:" in compose
    assert "web:" in compose
    assert "LLM_ENABLED: ${LLM_ENABLED:-false}" in compose
    assert "8000:8000" in compose
    assert "3000:3000" in compose
    assert "env_file:" not in compose
