"""OpenAI-compatible chat completion provider."""

from __future__ import annotations

import time

from app.core.config import LLMSettings
from app.llms.base import LLMProviderDisabledError, LLMProviderError, LLMProviderResponse

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class OpenAICompatibleProvider:
    """Provider for DeepSeek and other OpenAI-compatible endpoints."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def is_available(self) -> bool:
        return self.settings.enabled and bool(self.settings.api_key)

    def generate(self, prompt_name: str, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        if not self.settings.enabled:
            raise LLMProviderDisabledError("LLM is disabled.")
        if not self.settings.api_key:
            raise LLMProviderDisabledError("LLM_API_KEY is required.")
        if OpenAI is None:
            raise LLMProviderError("OpenAI SDK is not installed.")

        start = time.perf_counter()
        client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            timeout=self.settings.timeout_seconds,
        )
        response = client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else {}
        return LLMProviderResponse(
            content=content,
            model=self.settings.model,
            provider=self.settings.provider,
            latency_ms=latency_ms,
            raw_output=content,
            usage=usage_dict,
        )
