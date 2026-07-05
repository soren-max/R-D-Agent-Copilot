"""Reducers for long tool, RAG, and run-history context sections."""

from __future__ import annotations

import json
from typing import Any


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)


def summarize_text(text: str, budget: int, label: str = "content") -> tuple[str, bool]:
    """Keep the head and tail of a long block with a deterministic summary marker."""

    if budget <= 0:
        return "", bool(text)
    if len(text) <= budget:
        return text, False
    marker = f"\n...[{label} 已压缩，原始字符数={len(text)}]...\n"
    if budget <= len(marker) + 40:
        return text[:budget], True
    head_size = max(1, int((budget - len(marker)) * 0.65))
    tail_size = max(1, budget - len(marker) - head_size)
    return f"{text[:head_size]}{marker}{text[-tail_size:]}", True


def reduce_text(text: str, budget: int, label: str = "content") -> tuple[str, bool]:
    """Compatibility alias for older reducer callers; prefer summarize_text."""

    return summarize_text(text, budget, label)


def reduce_log_output(value: Any, budget: int) -> tuple[str, bool]:
    text = str(value or "")
    priority_lines = [
        line for line in text.splitlines()
        if any(token in line.upper() for token in ("ERROR", "WARN", "EXCEPTION", "TIMEOUT", "500"))
    ]
    if priority_lines:
        focused = "\n".join(priority_lines[:20])
        if len(focused) < len(text):
            text = f"{focused}\n\n...[log 非关键行已省略，原始字符数={len(str(value or ''))}]..."
    return summarize_text(text, budget, "log")


def reduce_config_output(value: Any, budget: int) -> tuple[str, bool]:
    text = str(value or "")
    priority_lines = [
        line for line in text.splitlines()
        if any(token in line for token in ("不一致", "diff", "prod", "dev", "timeout", "enabled"))
    ]
    if priority_lines:
        text = "\n".join(priority_lines[:24])
    return summarize_text(text, budget, "config")


def reduce_git_output(value: Any, budget: int) -> tuple[str, bool]:
    text = str(value or "")
    priority_lines = [
        line for line in text.splitlines()
        if any(token in line.lower() for token in ("commit", "author", "message", "fix", "change", "rollback"))
    ]
    if priority_lines:
        text = "\n".join(priority_lines[:24])
    return summarize_text(text, budget, "git")


def reduce_tool_evidence(tool_results: list[dict[str, Any]], budget: int) -> tuple[str, bool]:
    """Reduce non-RAG tool evidence while keeping tool identity and status."""

    items: list[dict[str, Any]] = []
    tool_records = [
        result for result in tool_results
        if (result.get("tool") or result.get("tool_name", "")) != "rag_retriever"
    ]
    budget_per_item = max(240, budget // max(1, len(tool_records)))
    reduced = False
    for result in tool_records:
        tool = result.get("tool") or result.get("tool_name", "")
        output = result.get("result", "")
        if tool == "log_tool":
            output, item_reduced = reduce_log_output(output, budget_per_item)
        elif tool == "config_tool":
            output, item_reduced = reduce_config_output(output, budget_per_item)
        elif tool == "git_tool":
            output, item_reduced = reduce_git_output(output, budget_per_item)
        else:
            output, item_reduced = summarize_text(str(output or ""), budget_per_item, tool or "tool")
        reduced = reduced or item_reduced
        items.append({
            "tool": tool,
            "status": result.get("status", ""),
            "source": result.get("source", ""),
            "confidence": result.get("confidence", 0),
            "error": result.get("error", ""),
            "result": output,
        })
    text = stable_json(items)
    summarized, text_reduced = summarize_text(text, budget, "tool_evidence")
    return summarized, reduced or text_reduced


def reduce_rag_output(value: Any, budget: int) -> tuple[str, bool]:
    if isinstance(value, list):
        compact = []
        for item in value[:5]:
            if isinstance(item, dict):
                compact.append({
                    "source": item.get("source", ""),
                    "chunk_id": item.get("chunk_id", item.get("id", "")),
                    "score": item.get("score", item.get("confidence", "")),
                    "content": item.get("content", item.get("content_excerpt", "")),
                })
            else:
                compact.append(item)
        text = stable_json(compact)
    else:
        text = stable_json(value) if isinstance(value, dict) else str(value or "")
    return summarize_text(text, budget, "rag")


def _document_content(document: dict[str, Any]) -> str:
    for key in ("content", "text", "body", "snippet", "content_excerpt"):
        if document.get(key):
            return str(document[key])
    return ""


def _compact_rag_document(document: dict[str, Any], content_budget: int) -> tuple[dict[str, Any], bool]:
    content_summary, reduced = summarize_text(_document_content(document), content_budget, "rag_content")
    compact = {
        "source": document.get("source", ""),
        "title": document.get("title", ""),
        "score": document.get("score", document.get("confidence", "")),
        "chunk_id": document.get("chunk_id", document.get("id", "")),
        "doc_id": document.get("doc_id", document.get("document_id", "")),
        "content_summary": content_summary,
    }
    return compact, reduced


def _fit_rag_payload_to_budget(payload: list[dict[str, Any]], budget: int) -> tuple[str, bool]:
    """Shrink content summaries only; metadata fields stay intact."""

    text = stable_json(payload)
    if len(text) <= budget:
        return text, False

    reduced = False
    content_budgets = [240, 160, 80, 40, 0]
    for content_budget in content_budgets:
        reduced_payload: list[dict[str, Any]] = []
        for item in payload:
            documents = []
            for document in item.get("documents", []):
                next_document = dict(document)
                content = str(next_document.get("content_summary", ""))
                next_document["content_summary"], item_reduced = summarize_text(
                    content,
                    content_budget,
                    "rag_content",
                )
                reduced = reduced or item_reduced or len(next_document["content_summary"]) < len(content)
                documents.append(next_document)
            next_item = dict(item)
            next_item["documents"] = documents
            reduced_payload.append(next_item)
        text = stable_json(reduced_payload)
        payload = reduced_payload
        if len(text) <= budget:
            return text, True
    return text, True


def reduce_rag_evidence(tool_results: list[dict[str, Any]], budget: int) -> tuple[str, bool]:
    """Reduce RAG evidence while preserving metadata before content summaries."""

    rag_results = [
        result for result in tool_results
        if result.get("tool") == "rag_retriever" or result.get("tool_name") == "rag_retriever"
    ]
    compact_payload = []
    reduced = False
    for result in rag_results:
        documents = []
        for document in result.get("documents", [])[:5]:
            compact_document, content_reduced = _compact_rag_document(document, 500)
            reduced = reduced or content_reduced
            documents.append(compact_document)
        metadata = result.get("rag_metadata", {})
        compact_payload.append({
            "status": result.get("status", ""),
            "error": result.get("error", ""),
            "grounding_status": metadata.get("grounding_status", ""),
            "evidence": metadata.get("evidence", [])[:5],
            "documents": documents,
        })
    summarized, text_reduced = _fit_rag_payload_to_budget(compact_payload, budget)
    return summarized, reduced or text_reduced


def reduce_run_history(value: Any, budget: int) -> tuple[str, bool]:
    if isinstance(value, dict):
        compact = {
            "trace_id": value.get("trace_id", ""),
            "steps": [
                {
                    "stage": step.get("stage", ""),
                    "engine": step.get("engine", ""),
                    "output": step.get("output", ""),
                    "latency_ms": step.get("latency_ms", 0),
                    "tool_calls": step.get("tool_calls", []),
                    "skipped_nodes": step.get("skipped_nodes", []),
                    "fallback_used": step.get("fallback_used", False),
                }
                for step in value.get("steps", [])
            ],
        }
        text = stable_json(compact)
    else:
        text = stable_json(value)
    return summarize_text(text, budget, "run_history")
