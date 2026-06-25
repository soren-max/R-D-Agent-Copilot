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
    deepseek_api_key: str = field(default="", repr=False)


def get_llm_settings() -> LLMSettings:
    """Load LLM settings from environment variables and optional .env."""

    load_dotenv()
    return LLMSettings(
        enabled=_parse_bool(os.getenv("LLM_ENABLED"), default=False),
        provider=os.getenv("LLM_PROVIDER", "deepseek"),
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )
