import app.agent.synthesizer as synthesizer_module
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest


def _clear_llm_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")


def test_chat_uses_fallback_when_llm_disabled_and_does_not_call_deepseek(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "false")
    calls = {"count": 0}

    def fail_if_called(self, system_prompt, user_prompt):
        calls["count"] += 1
        raise AssertionError("DeepSeek should not be called when LLM is disabled")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fail_if_called)

    response = chat_endpoint(ChatRequest(query="什么是配置中心？"))
    data = response.model_dump()

    assert calls["count"] == 0
    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "llm_disabled"
    synthesizer_step = [s for s in data["trace"]["steps"] if s["stage"] == "synthesizer"][0]
    assert synthesizer_step["engine"] == "fallback"
    assert synthesizer_step["llm_used"] is False
    assert synthesizer_step["prompt_version"] == "fallback_prompt_v1"


def test_chat_falls_back_when_llm_enabled_without_api_key(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "true")

    response = chat_endpoint(ChatRequest(query="什么是配置中心？"))
    data = response.model_dump()

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "missing_api_key"
    assert data["answer"]
    synthesizer_step = [s for s in data["trace"]["steps"] if s["stage"] == "synthesizer"][0]
    assert synthesizer_step["engine"] == "fallback"
    assert synthesizer_step["llm_error"] == "missing_api_key"
    assert synthesizer_step["prompt_version"] == "fallback_prompt_v1"


def test_chat_uses_mocked_llm_answer_for_complex_troubleshooting(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
    calls = {}

    def fake_generate(self, system_prompt, user_prompt):
        calls["system_prompt"] = system_prompt
        calls["user_prompt"] = user_prompt
        return "1. 初步判断\n模拟中文回答"

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    response = chat_endpoint(ChatRequest(query="为什么订单接口报500？"))
    data = response.model_dump()

    assert data["answer"] == "1. 初步判断\n模拟中文回答"
    assert data["answer_source"] == "llm"
    assert data["llm_used"] is True
    assert data["llm_error"] is None
    assert "工具结果" in calls["system_prompt"]
    assert "用户原始问题" in calls["user_prompt"]
    assert "Router 输出" in calls["user_prompt"]
    assert "Planner steps" in calls["user_prompt"]
    assert "tool_results" in calls["user_prompt"]
    assert "trace 摘要" in calls["user_prompt"]
    synthesizer_step = [s for s in data["trace"]["steps"] if s["stage"] == "synthesizer"][0]
    assert synthesizer_step["engine"] == "deepseek"
    assert synthesizer_step["llm_used"] is True
    assert synthesizer_step["prompt_version"] == "synthesizer_prompt_v1"


def test_chat_falls_back_when_llm_generate_raises(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def fail_generate(self, system_prompt, user_prompt):
        raise RuntimeError("network failed")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fail_generate)

    response = chat_endpoint(ChatRequest(query="为什么订单接口报500？"))
    data = response.model_dump()

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "RuntimeError"
    assert "工具证据" in data["answer"]
    synthesizer_step = [s for s in data["trace"]["steps"] if s["stage"] == "synthesizer"][0]
    assert synthesizer_step["engine"] == "fallback"
    assert synthesizer_step["llm_used"] is False
    assert synthesizer_step["llm_error"] == "RuntimeError"
    assert synthesizer_step["prompt_version"] == "fallback_prompt_v1"


def test_simple_qa_and_complex_troubleshooting_both_pass_with_fallback(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "false")

    simple = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()
    complex_resp = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert simple["route"]["type"] == "simple_qa"
    assert simple["answer_source"] == "fallback"
    assert complex_resp["route"]["type"] == "complex_troubleshooting"
    assert complex_resp["answer_source"] == "fallback"
