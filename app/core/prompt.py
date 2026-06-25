"""Prompt templates for final answer synthesis."""

from __future__ import annotations

import json
from typing import Any


ANSWER_SYSTEM_PROMPT = (
    "你是一个研发排障智能助手。你只能根据输入的工具结果、知识库检索结果和执行链路生成中文回答。"
    "禁止编造工具结果之外的信息。回答必须结构清晰，包含初步判断、证据、建议处理方式。"
    "如果工具失败，需要明确说明。"
)


def build_answer_user_prompt(
    query: str,
    route: dict[str, Any],
    plan: dict[str, Any],
    tool_results: list[dict[str, Any]],
    trace_summary: dict[str, Any],
) -> str:
    payload = {
        "用户原始问题": query,
        "Router 输出": route,
        "Planner steps": plan.get("steps", []),
        "tool_results": tool_results,
        "trace 摘要": trace_summary,
    }
    return (
        "请基于以下执行结果生成中文最终回答。\n\n"
        "复杂排障回答结构：\n"
        "1. 初步判断\n"
        "2. 工具证据\n"
        "3. 知识库补充\n"
        "4. 建议处理方式\n"
        "5. 不确定性说明\n\n"
        "简单问答回答结构：\n"
        "1. 简要解释\n"
        "2. 知识来源\n"
        "3. 补充说明\n\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
