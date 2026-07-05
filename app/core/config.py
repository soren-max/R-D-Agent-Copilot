"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LLMSettings:
    enabled: bool = False
    provider: str = "deepseek"
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: float = 15.0
    retry_count: int = 1
    retry_backoff_seconds: float = 0.2
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_reset_seconds: float = 60.0
    daily_token_limit: int = 100_000
    fallback_provider: str = ""
    fallback_model: str = ""
    fallback_base_url: str = ""
    fallback_api_key: str = field(default="", repr=False)
    api_key: str = field(default="", repr=False)
    deepseek_api_key: str = field(default="", repr=False)


@dataclass(frozen=True)
class RateLimitSettings:
    enabled: bool = True
    requests_per_window: int = 60
    window_seconds: int = 60


def _parse_int(value: str | None, default: int, minimum: int = 0) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    return max(minimum, parsed)


def _parse_float(value: str | None, default: float, minimum: float = 0.0) -> float:
    try:
        parsed = float(value) if value is not None else default
    except ValueError:
        return default
    return max(minimum, parsed)


def get_llm_settings(load_env: bool = True) -> LLMSettings:
    """Load LLM settings from environment variables and optional .env."""

    if load_env:
        load_dotenv()
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
    fallback_api_key = os.getenv("LLM_FALLBACK_API_KEY", "")
    return LLMSettings(
        enabled=_parse_bool(os.getenv("LLM_ENABLED"), default=False),
        provider=os.getenv("LLM_PROVIDER", "deepseek"),
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        timeout_seconds=_parse_float(os.getenv("LLM_TIMEOUT_SECONDS"), 15.0, minimum=0.1),
        retry_count=_parse_int(os.getenv("LLM_RETRY_COUNT"), 1, minimum=0),
        retry_backoff_seconds=_parse_float(os.getenv("LLM_RETRY_BACKOFF_SECONDS"), 0.2),
        circuit_breaker_failure_threshold=_parse_int(
            os.getenv("LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD"),
            3,
            minimum=1,
        ),
        circuit_breaker_reset_seconds=_parse_float(
            os.getenv("LLM_CIRCUIT_BREAKER_RESET_SECONDS"),
            60.0,
        ),
        daily_token_limit=_parse_int(os.getenv("LLM_DAILY_TOKEN_LIMIT"), 100_000, minimum=0),
        fallback_provider=os.getenv("LLM_FALLBACK_PROVIDER", ""),
        fallback_model=os.getenv("LLM_FALLBACK_MODEL", ""),
        fallback_base_url=os.getenv("LLM_FALLBACK_BASE_URL", ""),
        fallback_api_key=fallback_api_key,
        api_key=api_key,
        deepseek_api_key=api_key,
    )


def get_rate_limit_settings(load_env: bool = True) -> RateLimitSettings:
    """Load local API rate-limit settings from environment variables."""

    if load_env:
        load_dotenv()
    return RateLimitSettings(
        enabled=_parse_bool(os.getenv("RATE_LIMIT_ENABLED"), default=True),
        requests_per_window=_parse_int(os.getenv("RATE_LIMIT_REQUESTS"), 60, minimum=1),
        window_seconds=_parse_int(os.getenv("RATE_LIMIT_WINDOW_SECONDS"), 60, minimum=1),
    )
