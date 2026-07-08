from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.eval.bad_cases import write_bad_case_replay
from app.rag.retriever import LocalKnowledgeRetriever

CASES_PATH = ROOT / "eval" / "rag_eval_cases.jsonl"
REPORT_DIR = ROOT / "data" / "reports"
RESULT_PATH = REPORT_DIR / "rag_eval_result.json"
REPORT_PATH = REPORT_DIR / "rag_eval_report.md"
FAILED_CASES_PATH = REPORT_DIR / "rag_eval_failed_cases.json"


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def source_hit(documents: list[dict[str, Any]], expected_sources: set[str], top_k: int) -> bool:
    if not expected_sources:
        return len(documents[:top_k]) == 0
    return any(document.get("source") in expected_sources for document in documents[:top_k])


def precision_at_k(documents: list[dict[str, Any]], expected_sources: set[str], top_k: int) -> float:
    selected = documents[:top_k]
    if not expected_sources:
        return 1.0 if not selected else 0.0
    if not selected:
        return 0.0
    relevant = sum(1 for document in selected if document.get("source") in expected_sources)
    return relevant / len(selected)


def reciprocal_rank(documents: list[dict[str, Any]], expected_sources: set[str]) -> float:
    if not expected_sources:
        return 1.0 if not documents else 0.0
    for index, document in enumerate(documents, start=1):
        if document.get("source") in expected_sources:
            return 1.0 / index
    return 0.0


def keyword_hit(documents: list[dict[str, Any]], expected_keywords: list[str]) -> bool:
    combined = "\n".join(str(document.get("content", "")) for document in documents).lower()
    return all(keyword.lower() in combined for keyword in expected_keywords)


def doc_type_hit(documents: list[dict[str, Any]], expected_doc_type: str) -> bool:
    if not expected_doc_type:
        return True
    return any(document.get("doc_type") == expected_doc_type for document in documents)


def evaluate(cases_path: Path = CASES_PATH) -> dict[str, Any]:
    retriever = LocalKnowledgeRetriever()
    cases = load_cases(cases_path)
    failed_cases: list[dict[str, Any]] = []
    evaluated_cases: list[dict[str, Any]] = []

    recall3_hits = 0
    recall5_hits = 0
    hit_count = 0
    grounding_pass_count = 0
    precision3_total = 0.0
    mrr_total = 0.0
    latency_total = 0.0

    for case in cases:
        start = time.perf_counter()
        result = retriever.retrieve(case["query"], top_k=5, score_threshold=0.12, retrieval_type="hybrid")
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        latency_total += latency_ms

        documents = list(result.get("documents") or [])
        expected_sources = set(case.get("expected_sources") or [])
        expected_keywords = list(case.get("expected_keywords") or [])
        expected_doc_type = str(case.get("expected_doc_type") or "")
        expected_grounding_status = str(case.get("expected_grounding_status") or "")

        recall3 = source_hit(documents, expected_sources, 3)
        recall5 = source_hit(documents, expected_sources, 5)
        precision3 = precision_at_k(documents, expected_sources, 3)
        mrr = reciprocal_rank(documents, expected_sources)
        keywords_ok = keyword_hit(documents, expected_keywords)
        doc_type_ok = doc_type_hit(documents, expected_doc_type)
        grounding_status = str(result.get("grounding_status") or "")
        grounding_ok = grounding_status == expected_grounding_status
        case_passed = recall5 and keywords_ok and doc_type_ok and grounding_ok

        recall3_hits += int(recall3)
        recall5_hits += int(recall5)
        precision3_total += precision3
        mrr_total += mrr
        grounding_pass_count += int(grounding_ok)
        hit_count += int(case_passed)

        case_result = {
            "id": case.get("id", ""),
            "query": case["query"],
            "expected_sources": sorted(expected_sources),
            "expected_keywords": expected_keywords,
            "expected_doc_type": expected_doc_type,
            "expected_grounding_status": expected_grounding_status,
            "retrieved_sources": [document.get("source") for document in documents],
            "retrieved_chunks": [document.get("chunk_id") for document in documents],
            "retrieved_doc_types": [document.get("doc_type") for document in documents],
            "grounding_status": grounding_status,
            "latency_ms": latency_ms,
            "checks": {
                "recall_at_3": recall3,
                "recall_at_5": recall5,
                "precision_at_3": round(precision3, 4),
                "mrr": round(mrr, 4),
                "keywords_ok": keywords_ok,
                "doc_type_ok": doc_type_ok,
                "grounding_ok": grounding_ok,
            },
            "passed": case_passed,
        }
        evaluated_cases.append(case_result)
        if not case_passed:
            failed_cases.append(case_result)

    total = max(1, len(cases))
    metrics = {
        "total_cases": len(cases),
        "Recall@3": round(recall3_hits / total, 4),
        "Recall@5": round(recall5_hits / total, 4),
        "Precision@3": round(precision3_total / total, 4),
        "MRR": round(mrr_total / total, 4),
        "Hit Rate": round(hit_count / total, 4),
        "grounding_pass_rate": round(grounding_pass_count / total, 4),
        "average_latency_ms": round(latency_total / total, 2),
        "failed_cases": len(failed_cases),
    }

    result_payload = {
        "metrics": metrics,
        "failed_case_details": failed_cases,
        "cases": evaluated_cases,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FAILED_CASES_PATH.write_text(json.dumps(failed_cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_bad_case_replay(rag_failed_cases=failed_cases)
    REPORT_PATH.write_text(render_report(metrics, failed_cases), encoding="utf-8")
    return metrics


def render_report(metrics: dict[str, Any], failed_cases: list[dict[str, Any]]) -> str:
    lines = [
        "# RAG Evaluation Report",
        "",
        "This report is generated by `python scripts/eval_rag.py` against local Markdown files in `data/docs/`.",
        "No LLM, external embedding service, vector database, or enterprise API is called.",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Failed Cases", ""])
    if not failed_cases:
        lines.append("No failed RAG cases.")
    else:
        for case in failed_cases:
            checks = ", ".join(
                f"{key}={value}"
                for key, value in case.get("checks", {}).items()
            )
            lines.extend(
                [
                    f"### {case.get('id', '')}",
                    "",
                    f"- Query: {case.get('query', '')}",
                    f"- Expected sources: {case.get('expected_sources', [])}",
                    f"- Retrieved sources: {case.get('retrieved_sources', [])}",
                    f"- Grounding: {case.get('grounding_status', '')}",
                    f"- Checks: {checks}",
                    "",
                ]
            )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
