import app.agent.synthesizer as synthesizer_module
from app.api.chat import chat_endpoint
from app.core.llm import LLMGeneration, LLMUsage
from app.core.models import ChatRequest


def _enable_llm(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")


def _synthesizer_step(data: dict) -> dict:
    return [step for step in data["trace"]["steps"] if step["stage"] == "synthesizer"][0]


def test_llm_disabled_usage_is_zero(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()

    assert data["llm_usage"]["total_tokens"] == 0
    assert data["llm_usage"]["estimated_cost"] == 0
    assert data["llm_usage"]["source"] == "llm_disabled"


def test_llm_usage_uses_api_usage_from_generation(monkeypatch):
    _enable_llm(monkeypatch)

    def fake_generate(self, system_prompt, user_prompt):
        return LLMGeneration(
            content="1. 初步判断\n模拟中文回答",
            usage=LLMUsage(
                provider="deepseek",
                model="deepseek-v4-flash",
                prompt_tokens=1200,
                completion_tokens=300,
                total_tokens=1500,
                estimated_cost=0,
                source="api_usage",
            ),
        )

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["llm_used"] is True
    assert data["llm_usage"]["prompt_tokens"] == 1200
    assert data["llm_usage"]["completion_tokens"] == 300
    assert data["llm_usage"]["total_tokens"] == 1500
    assert data["llm_usage"]["source"] == "api_usage"


def test_llm_usage_estimates_tokens_when_usage_missing(monkeypatch):
    _enable_llm(monkeypatch)

    def fake_generate(self, system_prompt, user_prompt):
        return "1. 初步判断\n模拟中文回答"

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["llm_used"] is True
    assert data["llm_usage"]["source"] == "estimated"
    assert data["llm_usage"]["prompt_tokens"] > 0
    assert data["llm_usage"]["completion_tokens"] > 0
    assert data["llm_usage"]["total_tokens"] == (
        data["llm_usage"]["prompt_tokens"] + data["llm_usage"]["completion_tokens"]
    )


def test_trace_synthesizer_contains_llm_usage(monkeypatch):
    _enable_llm(monkeypatch)

    def fake_generate(self, system_prompt, user_prompt):
        return "1. 初步判断\n模拟中文回答"

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    synthesizer_step = _synthesizer_step(data)

    assert synthesizer_step["llm_usage"] == data["llm_usage"]
    assert synthesizer_step["llm_usage"]["total_tokens"] > 0


def test_chat_response_includes_llm_usage_without_real_deepseek(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()

    assert data["llm_used"] is False
    assert data["llm_usage"]["provider"] == "deepseek"
    assert data["llm_usage"]["model"] == "deepseek-v4-flash"
