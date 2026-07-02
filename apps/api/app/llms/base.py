"""Shared LLM provider contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import LLMSettings, get_llm_settings


class LLMProviderError(Exception):
    """Controlled provider failure used by router/planner fallback paths."""


class LLMProviderDisabledError(LLMProviderError):
    """Raised when a provider is unavailable by configuration."""


@dataclass(frozen=True)
class LLMProviderResponse:
    content: str
    model: str
    provider: str
    latency_ms: int
    raw_output: str
    usage: dict[str, object] = field(default_factory=dict)


class LLMProvider(Protocol):
    settings: LLMSettings

    def is_available(self) -> bool:
        ...

    def generate(self, prompt_name: str, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        ...


def get_llm_provider(settings: LLMSettings | None = None) -> LLMProvider:
    """Build the configured provider without leaking credentials."""

    resolved = settings or get_llm_settings()
    if resolved.provider.lower() == "mock":
        from app.llms.mock_provider import MockLLMProvider

        return MockLLMProvider(resolved)

    from app.llms.openai_compatible import OpenAICompatibleProvider

    return OpenAICompatibleProvider(resolved)
