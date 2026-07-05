import pytest
from fastapi.testclient import TestClient

import app.agent.synthesizer as synthesizer_module
from app.api.chat import chat_endpoint
from app.core.config import LLMSettings
from app.core.llm import LLMClient, LLMGeneration, LLMUsage, reset_runtime_state
from app.core.models import ChatRequest
from app.core.rate_limit import reset_rate_limiter
from app.eval import EvaluationV2Evaluator
from main import app


@pytest.fixture(autouse=True)
def runtime_state(monkeypatch):
    reset_runtime_state()
    reset_rate_limiter()
    monkeypatch.setenv("LLM_RETRY_BACKOFF_SECONDS", "0")
    yield
    reset_runtime_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "60")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    reset_rate_limiter()


def _settings(**overrides):
    values = {
        "enabled": True,
        "provider": "primary",
        "model": "primary-model",
        "base_url": "https://primary.example",
        "api_key": "primary-key",
        "deepseek_api_key": "primary-key",
        "retry_count": 0,
        "retry_backoff_seconds": 0,
        "circuit_breaker_failure_threshold": 2,
        "daily_token_limit": 100000,
    }
    values.update(overrides)
    return LLMSettings(**values)


def test_provider_timeout_triggers_rule_based_fallback(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def timeout_generate(self, system_prompt, user_prompt):
        raise TimeoutError("request timed out")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", timeout_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    step = [item for item in data["trace"]["steps"] if item["stage"] == "synthesizer"][0]

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "TimeoutError"
    assert step["provider_metadata"]["provider_error_code"] == "TimeoutError"
    assert step["provider_metadata"]["fallback_used"] is True


def test_provider_consecutive_failures_open_circuit_breaker():
    calls = {"count": 0}

    class FailingCompletions:
        def create(self, **kwargs):
            calls["count"] += 1
            raise TimeoutError("timeout")

    class FakeChat:
        completions = FailingCompletions()

    class FakeClient:
        chat = FakeChat()

    def factory(**kwargs):
        return FakeClient()

    client = LLMClient(_settings(), openai_factory=factory)

    with pytest.raises(Exception):
        client.generate("system", "user")
    with pytest.raises(Exception) as exc_info:
        client.generate("system", "user")

    assert calls["count"] == 2
    assert getattr(exc_info.value, "metadata")["circuit_open"] is True
    assert getattr(exc_info.value, "metadata")["provider_status"] == "degraded"

    with pytest.raises(Exception) as open_exc:
        client.generate("system", "user")

    assert calls["count"] == 2
    assert getattr(open_exc.value, "metadata")["provider_error_code"] == "circuit_open"


def test_fallback_provider_is_used_when_primary_fails():
    calls = []

    class FakeMessage:
        content = "fallback provider answer"

    class FakeChoice:
        message = FakeMessage()

    class FakeUsage:
        prompt_tokens = 10
        completion_tokens = 5
        total_tokens = 15

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeCompletions:
        def __init__(self, base_url):
            self.base_url = base_url

        def create(self, **kwargs):
            calls.append((self.base_url, kwargs["model"]))
            if "primary" in self.base_url:
                raise RuntimeError("primary down")
            return FakeResponse()

    class FakeChat:
        def __init__(self, base_url):
            self.completions = FakeCompletions(base_url)

    class FakeClient:
        def __init__(self, base_url):
            self.chat = FakeChat(base_url)

    def factory(**kwargs):
        return FakeClient(kwargs["base_url"])

    client = LLMClient(
        _settings(
            fallback_provider="backup",
            fallback_model="backup-model",
            fallback_base_url="https://backup.example",
            fallback_api_key="backup-key",
        ),
        openai_factory=factory,
    )

    result = client.generate("system", "user")

    assert result.content == "fallback provider answer"
    assert calls == [
        ("https://primary.example", "primary-model"),
        ("https://backup.example", "backup-model"),
    ]
    assert result.usage.provider == "backup"
    assert result.provider_metadata["fallback_provider_used"] is True


def test_daily_token_limit_blocks_llm_call():
    calls = {"count": 0}

    def factory(**kwargs):
        calls["count"] += 1
        return object()

    client = LLMClient(_settings(daily_token_limit=1), openai_factory=factory)

    with pytest.raises(Exception) as exc_info:
        client.generate("system prompt exceeds limit", "user prompt")

    assert calls["count"] == 0
    assert getattr(exc_info.value, "metadata")["daily_token_limit_exceeded"] is True


def test_llm_enabled_false_still_runs(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")

    def fail_if_called(self, system_prompt, user_prompt):
        raise AssertionError("LLM must not be called when disabled")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fail_if_called)

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "llm_disabled"


def test_provider_metadata_enters_trace(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def fake_generate(self, system_prompt, user_prompt):
        return LLMGeneration(
            content="1. 初步判断\n模拟中文回答",
            usage=LLMUsage(
                provider="deepseek",
                model="deepseek-v4-flash",
                prompt_tokens=20,
                completion_tokens=8,
                total_tokens=28,
                generation_cost_estimate=0.01,
                estimated_cost=0.01,
                daily_token_usage=28,
                source="api_usage",
            ),
            provider_metadata={
                "timeout_ms": 15000,
                "retry_count": 1,
                "provider_status": "healthy",
                "fallback_provider_used": False,
                "circuit_open": False,
                "prompt_tokens": 20,
                "completion_tokens": 8,
                "total_tokens": 28,
                "daily_token_usage": 28,
                "daily_token_limit_exceeded": False,
            },
        )

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    metadata = [item for item in data["trace"]["steps"] if item["stage"] == "synthesizer"][0]["provider_metadata"]

    assert metadata["timeout_ms"] == 15000
    assert metadata["retry_count"] == 1
    assert metadata["provider_status"] == "healthy"
    assert metadata["prompt_tokens"] == 20
    assert metadata["completion_tokens"] == 8
    assert metadata["total_tokens"] == 28
    assert metadata["daily_token_usage"] == 28


def test_evaluation_v2_aggregates_token_and_cost_metrics():
    report = EvaluationV2Evaluator().evaluate({
        "run_id": "run-runtime",
        "query": "为什么订单接口报500？",
        "answer": "fallback",
        "tool_results": [],
        "trace": {
            "trace_id": "run-runtime",
            "steps": [
                {
                    "stage": "synthesizer",
                    "provider_metadata": {
                        "model_provider": "deepseek",
                        "model_name": "deepseek-v4-flash",
                        "prompt_tokens": 100,
                        "completion_tokens": 30,
                        "total_tokens": 130,
                        "generation_cost_estimate": 0.02,
                        "daily_token_usage": 130,
                        "daily_token_limit_exceeded": False,
                        "provider_status": "healthy",
                        "fallback_provider_used": True,
                        "circuit_open": False,
                        "timeout_ms": 15000,
                        "retry_count": 1,
                    },
                }
            ],
        },
    })

    assert report.provider.total_tokens == 130
    assert report.provider.generation_cost_estimate == 0.02
    assert report.provider.daily_token_usage == 130
    assert report.provider.provider_status == "healthy"
    assert report.provider.fallback_provider_used is True


def test_local_rate_limit_returns_uniform_error(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    reset_rate_limiter()
    client = TestClient(app)

    first = client.post("/chat", json={"query": "什么是配置中心？"})
    second = client.post("/chat", json={"query": "什么是配置中心？"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
