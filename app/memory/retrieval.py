"""Rule-based incident memory retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.memory.freshness import evaluate_freshness
from app.memory.incident_memory import IncidentMemory


@dataclass
class MemoryRetrievalResult:
    memory: IncidentMemory
    match_reason: str
    freshness_status: str

    def to_context_dict(self) -> dict[str, object]:
        return {
            "memory_id": self.memory.memory_id,
            "service": self.memory.service,
            "symptom": self.memory.symptom,
            "root_cause": self.memory.root_cause,
            "fix": self.memory.fix,
            "confidence": self.memory.confidence,
            "source_run_id": self.memory.source_run_id,
            "evidence_refs": self.memory.evidence_refs,
            "match_reason": self.match_reason,
            "freshness_status": self.freshness_status,
        }


def retrieve_incident_memories(
    memories: list[IncidentMemory],
    query: str,
    service: str | None = None,
    limit: int = 3,
    ttl_days: int = 30,
) -> list[MemoryRetrievalResult]:
    query_terms = _terms(query)
    scored: list[tuple[int, MemoryRetrievalResult]] = []
    for memory in memories:
        freshness = evaluate_freshness(memory, ttl_days=ttl_days)
        service_match = bool(service and memory.service and memory.service == service)
        symptom_terms = _terms(memory.symptom)
        overlap = len(query_terms & symptom_terms)
        if not service_match and overlap == 0:
            continue
        reason = "service_exact_match" if service_match else "symptom_keyword_match"
        freshness_penalty = 2 if freshness.freshness_status == "stale" else 0
        score = (100 if service_match else 0) + overlap - freshness_penalty
        scored.append((score, MemoryRetrievalResult(memory, reason, freshness.freshness_status)))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def _terms(text: str) -> set[str]:
    words = set(re.findall(r"[A-Za-z0-9_-]+|[\u4e00-\u9fff]{2,}", text.lower()))
    cjk_text = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    words.update(cjk_text[index:index + 2] for index in range(max(0, len(cjk_text) - 1)))
    stopwords = {"为什么", "怎么", "如何", "当前", "接口", "服务"}
    return {word for word in words if word not in stopwords}
