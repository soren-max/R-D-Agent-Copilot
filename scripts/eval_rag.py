from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.retriever import LocalKnowledgeRetriever

CASES_PATH = ROOT / "eval" / "rag_eval_cases.jsonl"
FAILED_CASES_PATH = ROOT / "data" / "reports" / "rag_eval_failed_cases.json"


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def reciprocal_rank(documents: list[dict[str, Any]], expected_sources: set[str]) -> float:
    for index, document in enumerate(documents, start=1):
        if document.get("source") in expected_sources:
            return 1.0 / index
    return 0.0


def source_hit(documents: list[dict[str, Any]], expected_sources: set[str], top_k: int) -> bool:
    return any(document.get("source") in expected_sources for document in documents[:top_k])


def keyword_hit(documents: list[dict[str, Any]], expected_keywords: list[str]) -> bool:
    combined = "\n".join(str(document.get("content", "")) for document in documents).lower()
    return all(keyword.lower() in combined for keyword in expected_keywords)


def evaluate() -> dict[str, Any]:
    retriever = LocalKnowledgeRetriever()
    cases = load_cases()
    failed_cases: list[dict[str, Any]] = []
    recall3_hits = 0
    recall5_hits = 0
    hit_count = 0
    mrr_total = 0.0
    latency_total = 0

    for case in cases:
        start = time.perf_counter()
        result = retriever.retrieve(case["query"], top_k=5, score_threshold=0.12, retrieval_type="hybrid")
        latency_ms = int((time.perf_counter() - start) * 1000)
        latency_total += latency_ms

        documents = result.get("documents", [])
        expected_sources = set(case.get("expected_sources", []))
        expected_keywords = case.get("expected_keywords", [])
        recall3 = source_hit(documents, expected_sources, 3)
        recall5 = source_hit(documents, expected_sources, 5)
        keywords_ok = keyword_hit(documents, expected_keywords)

        recall3_hits += int(recall3)
        recall5_hits += int(recall5)
        hit_count += int(recall5 and keywords_ok)
        mrr_total += reciprocal_rank(documents, expected_sources)

        if not recall5 or not keywords_ok:
            failed_cases.append(
                {
                    "query": case["query"],
                    "expected_sources": case.get("expected_sources", []),
                    "expected_keywords": expected_keywords,
                    "retrieved_sources": [document.get("source") for document in documents],
                    "retrieved_chunks": [document.get("chunk_id") for document in documents],
                    "grounding_status": result.get("grounding_status"),
                }
            )

    total = max(1, len(cases))
    metrics = {
        "Recall@3": round(recall3_hits / total, 4),
        "Recall@5": round(recall5_hits / total, 4),
        "Hit Rate": round(hit_count / total, 4),
        "MRR": round(mrr_total / total, 4),
        "average_latency_ms": round(latency_total / total, 2),
        "failed_cases": len(failed_cases),
    }

    FAILED_CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    FAILED_CASES_PATH.write_text(
        json.dumps(failed_cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metrics


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
