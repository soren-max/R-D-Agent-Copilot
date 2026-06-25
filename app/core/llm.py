"""OpenAI-compatible DeepSeek client wrapper."""

from __future__ import annotations

from typing import Callable

from app.core.config import LLMSettings, get_llm_settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is declared in requirements.
    OpenAI = None


class LLMClientError(Exception):
    """Base error for controlled LLM client failures."""


class LLMDisabledError(LLMClientError):
    """Raised when generation is requested while LLM is disabled."""


class MissingAPIKeyError(LLMClientError):
    """Raised when LLM is enabled but the DeepSeek API key is missing."""


class LLMDependencyError(LLMClientError):
    """Raised when the OpenAI SDK is unavailable."""


class LLMClient:
    """Minimal DeepSeek client used only for future final-answer generation."""

    def __init__(
        self,
        settings: LLMSettings | None = None,
        openai_factory: Callable[..., object] | None = None,
    ) -> None:
        self.settings = settings or get_llm_settings()
        self._openai_factory = openai_factory

    def is_enabled(self) -> bool:
        return self.settings.enabled

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.settings.enabled:
            raise LLMDisabledError("LLM is disabled. Set LLM_ENABLED=true to enable it.")
        if not self.settings.deepseek_api_key:
            raise MissingAPIKeyError("DEEPSEEK_API_KEY is required when LLM is enabled.")

        factory = self._openai_factory or OpenAI
        if factory is None:
            raise LLMDependencyError("OpenAI SDK is not installed.")

        client = factory(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.base_url,
        )
        response = client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
