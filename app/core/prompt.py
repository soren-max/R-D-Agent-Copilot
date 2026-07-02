"""Prompt templates and file-backed prompt loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SYNTHESIZER_PROMPT_VERSION = "answer_synthesizer_prompt_v020"
FALLBACK_PROMPT_VERSION = "fallback_prompt_v1"
PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(prompt_name: str) -> tuple[str, str]:
    """Load a prompt file and return (content, version)."""

    path = PROMPT_DIR / f"{prompt_name}.txt"
    content = path.read_text(encoding="utf-8")
    version = ""
    for line in content.splitlines()[:8]:
        if line.startswith("prompt_version:"):
            version = line.split(":", 1)[1].strip()
            break
    return content, version or f"{prompt_name}_v020"

ANSWER_SYSTEM_PROMPT, SYNTHESIZER_PROMPT_VERSION = load_prompt("answer_synthesizer_prompt")


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
