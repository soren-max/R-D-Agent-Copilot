"""Deterministic LLM provider for tests and local prompt debugging."""

from __future__ import annotations

import json
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
        text = user_prompt.lower()
        if prompt_name == "router_prompt":
            intent = "knowledge_qa"
            if any(keyword in text for keyword in ["日志", "log", "500", "error", "报错", "异常", "超时"]):
                intent = "log_analysis"
            elif any(keyword in text for keyword in ["配置", "config", "不生效"]):
                intent = "config_diff"
            elif any(keyword in text for keyword in ["git", "提交", "变更", "commit"]):
                intent = "git_change"
            return json.dumps({
                "intent": intent,
                "confidence": 0.86,
                "reason": "mock provider 根据关键词返回结构化路由结果",
            }, ensure_ascii=False)

        if prompt_name == "planner_prompt":
            if any(keyword in text for keyword in ["log_analysis", "日志", "500", "error", "报错"]):
                steps = [
                    {
                        "step_name": "query_logs",
                        "tool": "log_tool",
                        "input": "用户问题",
                        "expected_output": "相关错误日志与异常摘要",
                    },
                    {
                        "step_name": "retrieve_knowledge",
                        "tool": "rag_retriever",
                        "input": "用户问题",
                        "expected_output": "本地知识库排障说明",
                    },
                ]
                task_type = "log_analysis"
            else:
                steps = [
                    {
                        "step_name": "retrieve_knowledge",
                        "tool": "rag_retriever",
                        "input": "用户问题",
                        "expected_output": "本地知识库说明",
                    }
                ]
                task_type = "knowledge_qa"
            return json.dumps({"task_type": task_type, "steps": steps}, ensure_ascii=False)

        return "1. 初步判断\nmock provider 基于已有证据生成中文排障报告。"
