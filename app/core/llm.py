"""OpenAI-compatible DeepSeek client wrapper."""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass, field, replace
from typing import Callable

from app.core.config import LLMSettings, get_llm_settings
from app.core.logging import log_event

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is declared in requirements.
    OpenAI = None


class LLMClientError(Exception):
    """Base error for controlled LLM client failures."""

    def __init__(self, message: str, metadata: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.metadata = metadata or {}


class LLMDisabledError(LLMClientError):
    """Raised when generation is requested while LLM is disabled."""


class MissingAPIKeyError(LLMClientError):
    """Raised when LLM is enabled but the DeepSeek API key is missing."""


class LLMDependencyError(LLMClientError):
    """Raised when the OpenAI SDK is unavailable."""


class LLMCircuitOpenError(LLMClientError):
    """Raised when provider calls are blocked by the circuit breaker."""


class DailyTokenLimitExceededError(LLMClientError):
    """Raised when local daily token governance blocks generation."""


MODEL_PRICING = {
    # Demo-only pricing placeholder. Keep zero until pricing is verified externally.
    "deepseek-v4-flash": {
        "input_per_1m_tokens": 0.0,
        "output_per_1m_tokens": 0.0,
    }
}


@dataclass(frozen=True)
class ProviderRuntime:
    provider: str
    model: str
    base_url: str
    api_key: str = field(default="", repr=False)
    role: str = "primary"


@dataclass(frozen=True)
class LLMUsage:
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    generation_cost_estimate: float = 0.0
    currency: str = "USD"
    latency_ms: int = 0
    source: str = "fallback"
    daily_token_usage: int = 0

    def model_dump(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "generation_cost_estimate": self.generation_cost_estimate,
            "currency": self.currency,
            "latency_ms": self.latency_ms,
            "source": self.source,
            "daily_token_usage": self.daily_token_usage,
        }


@dataclass(frozen=True)
class LLMGeneration:
    content: str
    usage: LLMUsage
    provider_metadata: dict[str, object] = field(default_factory=dict)

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
        generation_cost_estimate=0.0,
        latency_ms=latency_ms,
        source=source,
        daily_token_usage=daily_token_usage(),
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
    cost = estimate_cost(settings.model, prompt_tokens, completion_tokens)
    return LLMUsage(
        provider=settings.provider,
        model=settings.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=cost,
        generation_cost_estimate=cost,
        latency_ms=latency_ms,
        source=source,
        daily_token_usage=daily_token_usage(),
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
    provider: str | None = None,
    model: str | None = None,
) -> LLMUsage | None:
    if usage is None:
        return None

    prompt_tokens = _usage_value(usage, "prompt_tokens")
    completion_tokens = _usage_value(usage, "completion_tokens")
    total_tokens = _usage_value(usage, "total_tokens") or prompt_tokens + completion_tokens
    active_model = model or settings.model
    cost = estimate_cost(active_model, prompt_tokens, completion_tokens)
    return LLMUsage(
        provider=provider or settings.provider,
        model=active_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=cost,
        generation_cost_estimate=cost,
        latency_ms=latency_ms,
        source="api_usage",
        daily_token_usage=daily_token_usage(),
    )


_CIRCUIT_STATE: dict[str, dict[str, float | int]] = {}
_TOKEN_USAGE: dict[str, int] = {}


def _today_key() -> str:
    return dt.date.today().isoformat()


def daily_token_usage() -> int:
    return int(_TOKEN_USAGE.get(_today_key(), 0))


def reset_runtime_state() -> None:
    """Reset in-memory LLM runtime governance state. Intended for tests."""

    _CIRCUIT_STATE.clear()
    _TOKEN_USAGE.clear()


def _add_daily_tokens(tokens: int) -> int:
    key = _today_key()
    _TOKEN_USAGE[key] = int(_TOKEN_USAGE.get(key, 0)) + max(0, tokens)
    return _TOKEN_USAGE[key]


def _circuit_key(runtime: ProviderRuntime) -> str:
    return f"{runtime.provider}:{runtime.model}:{runtime.base_url}"


def _is_circuit_open(runtime: ProviderRuntime, settings: LLMSettings) -> bool:
    state = _CIRCUIT_STATE.get(_circuit_key(runtime), {})
    opened_at = float(state.get("opened_at", 0) or 0)
    if not opened_at:
        return False
    if time.time() - opened_at >= settings.circuit_breaker_reset_seconds:
        _CIRCUIT_STATE.pop(_circuit_key(runtime), None)
        return False
    return True


def _record_provider_success(runtime: ProviderRuntime) -> None:
    _CIRCUIT_STATE.pop(_circuit_key(runtime), None)


def _record_provider_failure(runtime: ProviderRuntime, settings: LLMSettings) -> bool:
    key = _circuit_key(runtime)
    state = _CIRCUIT_STATE.setdefault(key, {"failures": 0, "opened_at": 0.0})
    failures = int(state.get("failures", 0) or 0) + 1
    state["failures"] = failures
    if failures >= settings.circuit_breaker_failure_threshold:
        state["opened_at"] = time.time()
        return True
    return False


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
            log_event(
                event="provider_skipped",
                stage="provider",
                error_code="llm_disabled",
                message="LLM disabled",
            )
            raise LLMDisabledError("LLM is disabled. Set LLM_ENABLED=true to enable it.")
        prompt_tokens_estimate = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
        if self.settings.daily_token_limit and daily_token_usage() + prompt_tokens_estimate > self.settings.daily_token_limit:
            metadata = self._metadata(
                provider_status="degraded",
                daily_token_limit_exceeded=True,
                prompt_tokens=prompt_tokens_estimate,
            )
            log_event(
                event="provider_token_limit_exceeded",
                stage="provider",
                level="WARNING",
                error_code="daily_token_limit_exceeded",
                message="Daily token limit exceeded",
            )
            raise DailyTokenLimitExceededError("daily_token_limit_exceeded", metadata=metadata)

        factory = self._openai_factory or OpenAI
        if factory is None:
            raise LLMDependencyError("OpenAI SDK is not installed.")

        primary = ProviderRuntime(
            provider=self.settings.provider,
            model=self.settings.model,
            base_url=self.settings.base_url,
            api_key=self.settings.api_key or self.settings.deepseek_api_key,
            role="primary",
        )
        fallback = self._fallback_runtime()
        errors: list[Exception] = []
        for runtime in [primary, *([fallback] if fallback else [])]:
            log_event(
                event="provider_attempt_started",
                stage="provider",
                message=f"{runtime.provider}:{runtime.model}:{runtime.role}",
            )
            if not runtime.api_key:
                error = MissingAPIKeyError(
                    "DEEPSEEK_API_KEY is required when LLM is enabled."
                    if runtime.role == "primary"
                    else "LLM_FALLBACK_API_KEY is required when fallback provider is configured."
                )
                errors.append(error)
                if runtime.role == "primary" and fallback:
                    continue
                metadata = self._metadata(
                    provider_status="degraded",
                    fallback_provider_used=runtime.role == "fallback",
                    provider_error_code="missing_api_key",
                )
                raise MissingAPIKeyError(str(error), metadata=metadata)
            try:
                return self._generate_with_runtime(runtime, factory, system_prompt, user_prompt)
            except Exception as exc:
                errors.append(exc)
                if runtime.role == "primary" and fallback:
                    continue
                metadata = getattr(exc, "metadata", None) or self._metadata(
                    provider_status="degraded",
                    fallback_provider_used=runtime.role == "fallback",
                    provider_error_code=exc.__class__.__name__,
                )
                raise LLMClientError(exc.__class__.__name__, metadata=metadata) from exc

        last = errors[-1] if errors else LLMClientError("provider_unavailable")
        raise LLMClientError(last.__class__.__name__) from last

    def _generate_with_runtime(
        self,
        runtime: ProviderRuntime,
        factory: Callable[..., object],
        system_prompt: str,
        user_prompt: str,
    ) -> LLMGeneration:
        if _is_circuit_open(runtime, self.settings):
            metadata = self._metadata(
                provider=runtime.provider,
                model=runtime.model,
                provider_status="degraded",
                fallback_provider_used=runtime.role == "fallback",
                circuit_open=True,
                provider_error_code="circuit_open",
            )
            log_event(
                event="provider_circuit_open",
                stage="provider",
                level="WARNING",
                error_code="circuit_open",
                message=runtime.provider,
            )
            raise LLMCircuitOpenError("circuit_open", metadata=metadata)

        attempts = self.settings.retry_count + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self._call_provider(factory, runtime, system_prompt, user_prompt)
                content = response.choices[0].message.content or ""
                usage = usage_from_api_response(
                    self.settings,
                    getattr(response, "usage", None),
                    provider=runtime.provider,
                    model=runtime.model,
                )
                if usage is None:
                    usage = estimated_usage(self.settings, system_prompt, user_prompt, content)
                    usage = replace(usage, provider=runtime.provider, model=runtime.model)
                daily_total = _add_daily_tokens(usage.total_tokens)
                usage = replace(usage, daily_token_usage=daily_total)
                _record_provider_success(runtime)
                metadata = self._metadata(
                    provider=runtime.provider,
                    model=runtime.model,
                    provider_status="healthy",
                    fallback_provider_used=runtime.role == "fallback",
                    retry_count=attempt,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    daily_token_usage=daily_total,
                )
                log_event(
                    event="provider_completed",
                    stage="provider",
                    latency_ms=usage.latency_ms,
                    message=f"{runtime.provider}:{runtime.model}",
                    total_tokens=usage.total_tokens,
                )
                return LLMGeneration(content=content, usage=usage, provider_metadata=metadata)
            except Exception as exc:
                last_error = exc
                circuit_open = _record_provider_failure(runtime, self.settings)
                if attempt < attempts - 1:
                    time.sleep(self.settings.retry_backoff_seconds * (2 ** attempt))
                    continue
                metadata = self._metadata(
                    provider=runtime.provider,
                    model=runtime.model,
                    provider_status="degraded",
                    fallback_provider_used=runtime.role == "fallback",
                    circuit_open=circuit_open,
                    retry_count=attempt,
                    provider_error_code=exc.__class__.__name__,
                )
                log_event(
                    event="provider_failed",
                    stage="provider",
                    level="ERROR",
                    error_code=exc.__class__.__name__,
                    message=f"{runtime.provider}:{runtime.model}",
                )
                raise LLMClientError(exc.__class__.__name__, metadata=metadata) from exc
        raise LLMClientError((last_error or Exception("provider_unavailable")).__class__.__name__)

    def _call_provider(
        self,
        factory: Callable[..., object],
        runtime: ProviderRuntime,
        system_prompt: str,
        user_prompt: str,
    ) -> object:
        client_kwargs = {
            "api_key": runtime.api_key,
            "base_url": runtime.base_url,
        }
        if self._openai_factory is None:
            client_kwargs["timeout"] = self.settings.timeout_seconds
        client = factory(
            **client_kwargs,
        )
        create_kwargs = dict(
            model=runtime.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return client.chat.completions.create(**create_kwargs)

    def _fallback_runtime(self) -> ProviderRuntime | None:
        if not (self.settings.fallback_provider or self.settings.fallback_model or self.settings.fallback_base_url):
            return None
        return ProviderRuntime(
            provider=self.settings.fallback_provider or self.settings.provider,
            model=self.settings.fallback_model or self.settings.model,
            base_url=self.settings.fallback_base_url or self.settings.base_url,
            api_key=self.settings.fallback_api_key,
            role="fallback",
        )

    def _metadata(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        provider_status: str,
        fallback_provider_used: bool = False,
        circuit_open: bool = False,
        retry_count: int = 0,
        provider_error_code: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        daily_token_usage: int | None = None,
        daily_token_limit_exceeded: bool = False,
    ) -> dict[str, object]:
        return {
            "timeout_ms": int(self.settings.timeout_seconds * 1000),
            "retry_count": retry_count,
            "provider_status": provider_status,
            "fallback_provider_used": fallback_provider_used,
            "circuit_open": circuit_open,
            "model_provider": provider or self.settings.provider,
            "model_name": model or self.settings.model,
            "provider_error_code": provider_error_code,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "daily_token_usage": daily_token_usage if daily_token_usage is not None else globals()["daily_token_usage"](),
            "daily_token_limit": self.settings.daily_token_limit,
            "daily_token_limit_exceeded": daily_token_limit_exceeded,
        }
