"""Small offline evaluation helpers for the v0.3.x keyword RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from apps.api.app.rag.retriever import KeywordRetriever


@dataclass(frozen=True)
class RagEvalCase:
    query: str
    expected_sources: list[str]
    expected_keywords: list[str] = field(default_factory=list)
    expect_evidence: bool = True


def load_eval_cases(path: Path) -> list[RagEvalCase]:
    cases: list[RagEvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        cases.append(
            RagEvalCase(
                query=data["query"],
                expected_sources=data.get("expected_sources", []),
                expected_keywords=data.get("expected_keywords", []),
                expect_evidence=data.get("expect_evidence", True),
            )
        )
    return cases


def evaluate_cases(
    cases: list[RagEvalCase],
    retriever: KeywordRetriever | None = None,
    top_k: int = 5,
    retrieval_type: str = "hybrid",
    baseline_retrieval_type: str | None = "keyword",
    use_query_rewrite: bool = True,
) -> dict[str, Any]:
    resolved_retriever = retriever or KeywordRetriever()
    total = max(1, len(cases))
    evidence_total = max(1, sum(1 for case in cases if case.expect_evidence))
    recall_hits = 0
    keyword_hits = 0
    grounding_total = 0.0
    refusal_correct = 0
    refusal_total = 0
    mrr_total = 0.0
    failed_cases: list[dict[str, Any]] = []

    for case in cases:
        result = resolved_retriever.retrieve_with_evidence(
            case.query,
            top_k=top_k,
            retrieval_type=retrieval_type,
            use_query_rewrite=use_query_rewrite,
        )
        chunks = result["retrieved_chunks"]
        expected_sources = set(case.expected_sources)
        retrieved_sources = [str(chunk.get("source", "")) for chunk in chunks]
        recall_ok = bool(expected_sources) and any(source in expected_sources for source in retrieved_sources)
        keywords_ok = _keyword_hit(chunks, case.expected_keywords)
        has_evidence = result.get("grounding_status") == "grounded" and bool(result.get("evidence"))
        grounding_ok = (has_evidence is case.expect_evidence) and (recall_ok or not case.expect_evidence)

        if not case.expect_evidence:
            refusal_total += 1
            refusal_correct += int(not has_evidence)

        if case.expect_evidence:
            recall_hits += int(recall_ok)
            mrr_total += _reciprocal_rank(retrieved_sources, expected_sources)
        keyword_hits += int(keywords_ok)
        grounding_total += float(grounding_ok)

        if case.expect_evidence and (not recall_ok or not keywords_ok or not grounding_ok):
            failed_cases.append({
                "query": case.query,
                "expected_sources": case.expected_sources,
                "expected_keywords": case.expected_keywords,
                "retrieved_sources": retrieved_sources,
                "rewritten_queries": result.get("rewritten_queries", []),
                "grounding_status": result.get("grounding_status", ""),
            })

    metrics = {
        f"Recall@{top_k}": round(recall_hits / evidence_total, 4),
        "Keyword Hit Rate": round(keyword_hits / total, 4),
        "Grounding Score": round(grounding_total / total, 4),
        "No Evidence Rejection Accuracy": round(refusal_correct / max(1, refusal_total), 4),
        "MRR": round(mrr_total / evidence_total, 4),
        "retrieval_type": retrieval_type,
        "failed_cases": failed_cases,
    }
    if baseline_retrieval_type:
        baseline = evaluate_cases(
            cases,
            retriever=resolved_retriever,
            top_k=top_k,
            retrieval_type=baseline_retrieval_type,
            baseline_retrieval_type=None,
            use_query_rewrite=False,
        )
        metrics["baseline"] = {
            "retrieval_type": baseline_retrieval_type,
            f"Recall@{top_k}": baseline[f"Recall@{top_k}"],
            "Grounding Score": baseline["Grounding Score"],
        }
        metrics["improvement"] = {
            f"Recall@{top_k}": round(metrics[f"Recall@{top_k}"] - baseline[f"Recall@{top_k}"], 4),
            "Grounding Score": round(metrics["Grounding Score"] - baseline["Grounding Score"], 4),
        }
    return metrics


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
