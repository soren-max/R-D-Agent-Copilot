import pytest

from app.core.config import LLMSettings, get_llm_settings
from app.core.llm import LLMClient, LLMDisabledError, MissingAPIKeyError


def test_default_llm_enabled_is_false(monkeypatch):
    for key in [
        "LLM_ENABLED",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_BASE_URL",
        "DEEPSEEK_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = get_llm_settings(load_env=False)

    assert settings.enabled is False
    assert settings.provider == "deepseek"
    assert settings.model == "deepseek-v4-flash"
    assert settings.base_url == "https://api.deepseek.com"
    assert settings.deepseek_api_key == ""


def test_missing_api_key_error_does_not_leak_secret():
    client = LLMClient(LLMSettings(enabled=True, deepseek_api_key=""))

    with pytest.raises(MissingAPIKeyError) as exc_info:
        client.generate("system", "user")

    message = str(exc_info.value)
    assert "DEEPSEEK_API_KEY" in message
    assert "secret" not in message.lower()


def test_llm_settings_repr_masks_api_key():
    settings = LLMSettings(enabled=True, deepseek_api_key="secret-test-value")

    assert "secret-test-value" not in repr(settings)


def test_llm_client_is_enabled_reflects_settings():
    assert LLMClient(LLMSettings(enabled=True)).is_enabled() is True
    assert LLMClient(LLMSettings(enabled=False)).is_enabled() is False


def test_generate_disabled_does_not_call_external_client():
    calls = {"count": 0}

    def openai_factory(**kwargs):
        calls["count"] += 1
        return object()

    client = LLMClient(
        LLMSettings(enabled=False, deepseek_api_key="test-api-key"),
        openai_factory=openai_factory,
    )

    with pytest.raises(LLMDisabledError):
        client.generate("system", "user")

    assert calls["count"] == 0


def test_generate_uses_openai_compatible_deepseek_settings():
    calls = {}

    class FakeMessage:
        content = "生成结果"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            calls["create"] = kwargs
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAIClient:
        chat = FakeChat()

    def openai_factory(**kwargs):
        calls["client"] = kwargs
        return FakeOpenAIClient()

    settings = LLMSettings(
        enabled=True,
        provider="deepseek",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com",
        deepseek_api_key="test-api-key",
    )

    result = LLMClient(settings, openai_factory=openai_factory).generate("system", "user")

    assert result == "生成结果"
    assert calls["client"] == {
        "api_key": "test-api-key",
        "base_url": "https://api.deepseek.com",
    }
    assert calls["create"] == {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
    }


def test_generate_extracts_usage_from_openai_compatible_response():
    class FakeMessage:
        content = "生成结果"

    class FakeChoice:
        message = FakeMessage()

    class FakeUsage:
        prompt_tokens = 12
        completion_tokens = 3
        total_tokens = 15

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAIClient:
        chat = FakeChat()

    def openai_factory(**kwargs):
        return FakeOpenAIClient()

    settings = LLMSettings(
        enabled=True,
        provider="deepseek",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com",
        deepseek_api_key="test-api-key",
    )

    result = LLMClient(settings, openai_factory=openai_factory).generate("system", "user")

    assert result == "生成结果"
    assert result.usage.prompt_tokens == 12
    assert result.usage.completion_tokens == 3
    assert result.usage.total_tokens == 15
    assert result.usage.source == "api_usage"
