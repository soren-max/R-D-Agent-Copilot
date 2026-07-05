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
    context_package: Any | None = None,
) -> str:
    if context_package is not None:
        context_payload = context_package.as_prompt_payload()
        payload = {
            "ContextPackage": context_payload,
            "ContextMetadata": context_package.metadata.model_dump(),
            "用户原始问题": context_payload.get("current_query", query),
            "Router 输出": route,
            "Planner steps": plan.get("steps", []),
            "tool_results": context_payload.get("tool_evidence", tool_results),
            "RAG evidence": context_payload.get("rag_evidence", []),
            "Incident Memory 历史参考": context_payload.get("incident_memory", []),
            "trace 摘要": context_payload.get("run_history", trace_summary),
        }
    else:
        payload = {
            "用户原始问题": query,
            "Router 输出": route,
            "Planner steps": plan.get("steps", []),
            "tool_results": tool_results,
            "trace 摘要": trace_summary,
        }
    return (
        "请基于以下执行结果生成中文最终报告，并只输出合法 JSON。\n\n"
        "JSON schema 字段必须包含：summary、root_cause、evidence、fix_steps、confidence、risks。\n"
        "evidence 只能引用 tool_evidence 或 RAG evidence；incident_memory 只能写入 risks 或历史参考限制，"
        "不能作为当前根因证据。\n"
        "如果证据不足，root_cause 必须写不确定或当前证据不足。\n\n"
        "Incident Memory 仅是历史参考，不是当前证据；如果当前 tool_results 或 RAG evidence 不支持，"
        "不得直接把历史 root_cause 当作本次最终根因。\n\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
