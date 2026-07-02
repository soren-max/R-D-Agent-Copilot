"""OpenAI-compatible DeepSeek client wrapper."""

from __future__ import annotations

from dataclasses import dataclass
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


MODEL_PRICING = {
    # Demo-only pricing placeholder. Keep zero until pricing is verified externally.
    "deepseek-v4-flash": {
        "input_per_1m_tokens": 0.0,
        "output_per_1m_tokens": 0.0,
    }
}


@dataclass(frozen=True)
class LLMUsage:
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    currency: str = "USD"
    latency_ms: int = 0
    source: str = "fallback"

    def model_dump(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "currency": self.currency,
            "latency_ms": self.latency_ms,
            "source": self.source,
        }


@dataclass(frozen=True)
class LLMGeneration:
    content: str
    usage: LLMUsage

    def __str__(self) -> str:
        return self.content

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.content == other
        return super().__eq__(other)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int((len(text) + 3) / 4))


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["deepseek-v4-flash"])
    input_cost = prompt_tokens * pricing["input_per_1m_tokens"] / 1_000_000
    output_cost = completion_tokens * pricing["output_per_1m_tokens"] / 1_000_000
    return round(input_cost + output_cost, 8)


def zero_usage(settings: LLMSettings, source: str = "fallback", latency_ms: int = 0) -> LLMUsage:
    return LLMUsage(
        provider=settings.provider,
        model=settings.model,
        estimated_cost=0.0,
        latency_ms=latency_ms,
        source=source,
    )


def estimated_usage(
    settings: LLMSettings,
    system_prompt: str,
    user_prompt: str,
    completion: str,
    latency_ms: int = 0,
    source: str = "estimated",
) -> LLMUsage:
    prompt_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    completion_tokens = estimate_tokens(completion)
    return LLMUsage(
        provider=settings.provider,
        model=settings.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=estimate_cost(settings.model, prompt_tokens, completion_tokens),
        latency_ms=latency_ms,
        source=source,
    )


def _usage_value(usage: object, key: str) -> int:
    if isinstance(usage, dict):
        value = usage.get(key)
    else:
        value = getattr(usage, key, None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


def usage_from_api_response(
    settings: LLMSettings,
    usage: object,
    latency_ms: int = 0,
) -> LLMUsage | None:
    if usage is None:
        return None

    prompt_tokens = _usage_value(usage, "prompt_tokens")
    completion_tokens = _usage_value(usage, "completion_tokens")
    total_tokens = _usage_value(usage, "total_tokens") or prompt_tokens + completion_tokens
    return LLMUsage(
        provider=settings.provider,
        model=settings.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimate_cost(settings.model, prompt_tokens, completion_tokens),
        latency_ms=latency_ms,
        source="api_usage",
    )


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

    def generate(self, system_prompt: str, user_prompt: str) -> LLMGeneration:
        if not self.settings.enabled:
            raise LLMDisabledError("LLM is disabled. Set LLM_ENABLED=true to enable it.")
        api_key = self.settings.api_key or self.settings.deepseek_api_key
        if not api_key:
            raise MissingAPIKeyError("DEEPSEEK_API_KEY is required when LLM is enabled.")

        factory = self._openai_factory or OpenAI
        if factory is None:
            raise LLMDependencyError("OpenAI SDK is not installed.")

        client = factory(
            api_key=api_key,
            base_url=self.settings.base_url,
        )
        response = client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        usage = usage_from_api_response(self.settings, getattr(response, "usage", None))
        if usage is None:
            usage = estimated_usage(self.settings, system_prompt, user_prompt, content)
        return LLMGeneration(content=content, usage=usage)
