"""Deterministic LLM provider for final-answer tests and local debugging."""

from __future__ import annotations

import time

from app.core.config import LLMSettings
from app.llms.base import LLMProviderResponse


class MockLLMProvider:
    """Return stable structured outputs without network access."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def is_available(self) -> bool:
        return True

    def generate(self, prompt_name: str, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        start = time.perf_counter()
        content = self._content(prompt_name, user_prompt)
        return LLMProviderResponse(
            content=content,
            model=self.settings.model or "mock-model",
            provider="mock",
            latency_ms=int((time.perf_counter() - start) * 1000),
            raw_output=content,
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "source": "mock",
            },
        )

    def _content(self, prompt_name: str, user_prompt: str) -> str:
        if prompt_name in {"router_prompt", "planner_prompt"}:
            raise RuntimeError(f"{prompt_name} is legacy-disabled; Router and Planner are deterministic")

        return "1. 初步判断\nmock provider 基于已有证据生成中文排障报告。"
