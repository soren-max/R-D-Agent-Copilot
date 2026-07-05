"""Final report schema and rule-based validation helpers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.models import ToolCallRecord


class FinalReport(BaseModel):
    """Stable schema for the final troubleshooting report."""

    summary: str = Field(default="")
    root_cause: str = Field(default="")
    evidence: list[str] = Field(default_factory=list)
    fix_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risks: list[str] = Field(default_factory=list)


def parse_final_report(raw_output: str) -> tuple[FinalReport | None, str]:
    """Parse and validate provider JSON output."""

    raw = _strip_json_fence(raw_output)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "schema_validation_failed"
    try:
        return FinalReport.model_validate(payload), ""
    except ValidationError:
        return None, "schema_validation_failed"


def build_fallback_report(
    answer: str,
    tool_results: list[ToolCallRecord],
    *,
    confidence: float | None = None,
) -> FinalReport:
    """Build a schema-valid report from deterministic tool/RAG evidence."""

    evidence = _evidence_lines(tool_results)
    has_current_evidence = bool(evidence)
    insufficient = "证据不足" in answer or "insufficient_evidence" in answer
    root_cause = (
        "当前证据不足，无法确认根因。"
        if insufficient or not has_current_evidence
        else "基于当前工具和 RAG evidence 的初步判断，根因仍需结合现场状态确认。"
    )
    risks = ["Incident Memory 只能作为历史参考，不能单独作为当前事实。"]
    if insufficient or not has_current_evidence:
        risks.append("当前工具证据或 RAG evidence 不足，不能编造根因。")
    return FinalReport(
        summary=_first_non_empty_line(answer) or "已根据当前执行结果生成排障报告。",
        root_cause=root_cause,
        evidence=evidence,
        fix_steps=_fix_steps_from_answer(answer),
        confidence=confidence if confidence is not None else (0.45 if has_current_evidence else 0.2),
        risks=risks,
    )


def build_unstructured_llm_report(raw_output: str, tool_results: list[ToolCallRecord]) -> FinalReport:
    """Preserve a non-JSON provider response while still exposing the stable schema."""

    report = build_fallback_report(raw_output, tool_results)
    report.summary = _first_non_empty_line(raw_output) or "LLM 未返回合法 JSON。"
    report.risks.append("Provider 未返回合法 JSON，schema_valid=false；已按非结构化文本降级解析。")
    return report


def render_final_report(report: FinalReport) -> str:
    evidence = "\n".join(f"- {item}" for item in report.evidence) or "- 当前无可用 evidence。"
    fix_steps = "\n".join(f"- {item}" for item in report.fix_steps) or "- 继续补充日志、配置或 RAG evidence 后再确认。"
    risks = "\n".join(f"- {item}" for item in report.risks) or "- 暂无额外风险。"
    return (
        f"【摘要】{report.summary}\n\n"
        f"【根因判断】{report.root_cause}\n\n"
        f"【证据】\n{evidence}\n\n"
        f"【建议处理】\n{fix_steps}\n\n"
        f"【置信度】{report.confidence:.2f}\n\n"
        f"【风险提示】\n{risks}"
    )


def _strip_json_fence(raw_output: str) -> str:
    raw = raw_output.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:300]
    return ""


def _evidence_lines(tool_results: list[ToolCallRecord]) -> list[str]:
    lines: list[str] = []
    for record in tool_results:
        if record.status not in {"success", "partial_success"}:
            continue
        if record.tool == "rag_retriever" and record.documents:
            for doc in record.documents[:3]:
                title = doc.get("title") or doc.get("source") or doc.get("chunk_id") or "RAG document"
                excerpt = str(doc.get("content") or doc.get("text") or doc.get("snippet") or "")[:160]
                lines.append(f"RAG:{title} {excerpt}".strip())
            continue
        if record.result:
            label = record.tool_name or record.tool
            lines.append(f"{label}: {record.result[:180]}")
    return lines[:6]


def _fix_steps_from_answer(answer: str) -> list[str]:
    candidates = []
    for line in answer.splitlines():
        stripped = line.strip(" -\t")
        if any(keyword in stripped for keyword in ("建议", "处理", "排查", "核对", "查看", "补充")):
            candidates.append(stripped[:220])
    if candidates:
        return candidates[:4]
    return ["继续补充日志、配置、Git 变更或 RAG evidence 后再确认根因。"]
