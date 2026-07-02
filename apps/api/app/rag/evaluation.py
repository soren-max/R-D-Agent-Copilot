"""Small offline evaluation helpers for the v0.3.x keyword RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.api.app.rag.retriever import KeywordRetriever


@dataclass(frozen=True)
class RagEvalCase:
    query: str
    expected_sources: list[str]
    expected_keywords: list[str] = field(default_factory=list)


def evaluate_cases(cases: list[RagEvalCase], retriever: KeywordRetriever | None = None, top_k: int = 3) -> dict[str, Any]:
    resolved_retriever = retriever or KeywordRetriever()
    total = max(1, len(cases))
    recall_hits = 0
    keyword_hits = 0
    mrr_total = 0.0
    failed_cases: list[dict[str, Any]] = []

    for case in cases:
        result = resolved_retriever.retrieve_with_evidence(case.query, top_k=top_k)
        chunks = result["retrieved_chunks"]
        expected_sources = set(case.expected_sources)
        retrieved_sources = [str(chunk.get("source", "")) for chunk in chunks]
        recall_ok = any(source in expected_sources for source in retrieved_sources)
        keywords_ok = _keyword_hit(chunks, case.expected_keywords)

        recall_hits += int(recall_ok)
        keyword_hits += int(keywords_ok)
        mrr_total += _reciprocal_rank(retrieved_sources, expected_sources)

        if not recall_ok or not keywords_ok:
            failed_cases.append({
                "query": case.query,
                "expected_sources": case.expected_sources,
                "expected_keywords": case.expected_keywords,
                "retrieved_sources": retrieved_sources,
                "rewritten_queries": result.get("rewritten_queries", []),
                "grounding_status": result.get("grounding_status", ""),
            })

    return {
        "Recall@K": round(recall_hits / total, 4),
        "Keyword Hit Rate": round(keyword_hits / total, 4),
        "MRR": round(mrr_total / total, 4),
        "failed_cases": failed_cases,
    }


def _keyword_hit(chunks: list[dict[str, Any]], expected_keywords: list[str]) -> bool:
    if not expected_keywords:
        return True
    combined = "\n".join(str(chunk.get("content", "")) for chunk in chunks).lower()
    return all(keyword.lower() in combined for keyword in expected_keywords)


def _reciprocal_rank(retrieved_sources: list[str], expected_sources: set[str]) -> float:
    for index, source in enumerate(retrieved_sources, start=1):
        if source in expected_sources:
            return 1.0 / index
    return 0.0
