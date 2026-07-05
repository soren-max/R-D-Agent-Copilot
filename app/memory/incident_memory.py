"""Structured incident memory model and deterministic extraction."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentMemory(BaseModel):
    """A compact historical troubleshooting memory."""

    memory_id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    service: str = ""
    symptom: str = ""
    root_cause: str = ""
    fix: str = ""
    confidence: float = 0.0
    source_run_id: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


def build_memory_from_payload(payload: dict[str, Any]) -> IncidentMemory | None:
    """Build a weak-but-structured memory from completed run artifacts."""

    query = str(payload.get("query", "")).strip()
    answer = str(payload.get("answer", "")).strip()
    evidence_chain = payload.get("evidence_chain") or {}
    root_candidates = evidence_chain.get("root_cause_candidates") or []
    evidence_items = evidence_chain.get("evidence_items") or []

    if not query and not answer:
        return None

    candidate = root_candidates[0] if root_candidates else {}
    root_cause = str(candidate.get("title") or _extract_section(answer, "初步判断") or "").strip()
    fix = _extract_section(answer, "排查步骤") or _extract_section(answer, "建议处理方式") or ""
    confidence = float(candidate.get("confidence") or evidence_chain.get("overall_confidence") or 0.0)
    evidence_refs = [
        str(item.get("id"))
        for item in evidence_items
        if item.get("id")
    ]

    memory = IncidentMemory(
        service=_infer_service(query, payload.get("tool_results", [])),
        symptom=query[:240],
        root_cause=root_cause[:240],
        fix=str(fix).strip()[:300],
        confidence=max(0.0, min(confidence, 1.0)),
        source_run_id=str(payload.get("source_run_id") or ""),
        evidence_refs=evidence_refs,
    )
    if not memory.root_cause and not memory.fix:
        return None
    return memory


def _extract_section(answer: str, label: str) -> str:
    pattern = rf"【{re.escape(label)}】(.+?)(?:\n\n【|$)"
    match = re.search(pattern, answer, flags=re.S)
    if match:
        return match.group(1).strip()
    return ""


def _infer_service(query: str, tool_results: list[dict[str, Any]]) -> str:
    service_match = re.search(r"([A-Za-z0-9_-]+-service)", query)
    if service_match:
        return service_match.group(1)
    for result in tool_results:
        text = " ".join([
            str(result.get("source", "")),
            str(result.get("result", "")),
        ])
        service_match = re.search(r"([A-Za-z0-9_-]+-service)", text)
        if service_match:
            return service_match.group(1)
    if "订单" in query:
        return "order-service"
    return ""
