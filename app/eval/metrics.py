"""Rule-based metric builders for Evaluation v2."""

from __future__ import annotations

from typing import Any

from app.eval.schemas import (
    ContextMetricsV2,
    EvidenceMetricsV2,
    MemoryMetricsV2,
    ProviderMetricsV2,
    RagMetricsV2,
    ResumeMetricsV2,
    ToolMetricsV2,
)


def context_metrics(trace: dict[str, Any], query: str = "") -> ContextMetricsV2:
    metadata = _context_metadata(trace)
    section_counts = metadata.get("section_char_counts", {})
    return ContextMetricsV2(
        prompt_chars_before=int(metadata.get("total_chars_before", 0) or 0),
        prompt_chars_after=int(metadata.get("total_chars_after", 0) or 0),
        compression_ratio=float(metadata.get("compression_ratio", 1.0) or 1.0),
        current_query_preserved=bool(section_counts.get("current_query", 0) >= len(query)),
        reduced_sections=list(metadata.get("reduced_sections", []) or []),
    )


def tool_metrics(trace: dict[str, Any], tool_results: list[dict[str, Any]]) -> ToolMetricsV2:
    calls = _executor_tool_calls(trace)
    records = calls or tool_results
    counts: dict[str, int] = {}
    latencies: list[int] = []
    for record in records:
        status = str(record.get("tool_status") or record.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        latency = record.get("latency_ms")
        if isinstance(latency, (int, float)) and not isinstance(latency, bool):
            latencies.append(max(0, int(latency)))
    total = max(1, len(records))
    success = counts.get("success", 0)
    return ToolMetricsV2(
        tool_success_rate=round(success / total, 4) if records else 0.0,
        tool_error_count=counts.get("error", 0) + counts.get("failed", 0),
        tool_blocked_count=counts.get("blocked", 0),
        partial_success_count=counts.get("partial_success", 0),
        avg_tool_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        tool_status_counts=counts,
    )


def rag_metrics(tool_results: list[dict[str, Any]], trace: dict[str, Any] | None = None) -> RagMetricsV2:
    rag = next(
        (result for result in tool_results if result.get("tool") == "rag_retriever" or result.get("tool_name") == "rag_retriever"),
        {},
    )
    documents = list(rag.get("documents") or [])
    missing_source_count = sum(1 for doc in documents if not (doc.get("source") or doc.get("title")))
    complete = max(0, len(documents) - missing_source_count)
    source_coverage = round(complete / len(documents), 4) if documents else 0.0
    metadata = rag.get("rag_metadata") or {}
    grounding_status = metadata.get("grounding_status", "")
    grounding_score = 1.0 if grounding_status == "grounded" and missing_source_count == 0 and documents else source_coverage * 0.7
    return RagMetricsV2(
        rag_hit_count=len(documents),
        source_coverage=source_coverage,
        missing_source_count=missing_source_count,
        grounding_score=round(grounding_score, 4),
    )


def memory_metrics(trace: dict[str, Any], answer: str, tool_results: list[dict[str, Any]]) -> MemoryMetricsV2:
    metadata = _context_metadata(trace)
    answer_mentions_memory = int("历史参考" in answer or "Incident Memory" in answer)
    has_current_evidence = any(
        result.get("status") in {"success", "partial_success"} and (result.get("result") or result.get("documents"))
        for result in tool_results
    )
    risky_root_cause = ("历史根因参考" in answer or "历史配置差异" in answer) and not has_current_evidence
    weak_count = max(0, int(metadata.get("memory_hit_count", 0) or 0) - int(metadata.get("fresh_memory_count", 0) or 0) - int(metadata.get("stale_memory_count", 0) or 0))
    return MemoryMetricsV2(
        memory_hit_count=int(metadata.get("memory_hit_count", 0) or 0),
        fresh_memory_count=int(metadata.get("fresh_memory_count", 0) or 0),
        weak_memory_count=weak_count,
        stale_memory_count=int(metadata.get("stale_memory_count", 0) or 0),
        memory_used_as_reference_count=answer_mentions_memory,
        memory_misused_as_current_fact_count=int(risky_root_cause),
    )


def resume_metrics(trace: dict[str, Any], checkpoint: dict[str, Any] | None = None, resume_result: dict[str, Any] | None = None) -> ResumeMetricsV2:
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    checkpoint_created = any(step.get("checkpoint_created") is True for step in steps)
    resume_result = resume_result or {}
    checkpoint = checkpoint or {}
    completed = list(checkpoint.get("completed_steps") or [])
    return ResumeMetricsV2(
        checkpoint_created=checkpoint_created,
        resume_success=resume_result.get("status") == "completed",
        already_completed_count=int(resume_result.get("status") == "already_completed"),
        stale_checkpoint_count=int(resume_result.get("status") == "stale_checkpoint"),
        resumed_completed_steps_count=int(resume_result.get("resumed_completed_steps_count") or 0),
        resumed_pending_steps_count=int(resume_result.get("resumed_pending_steps_count") or 0),
        duplicated_step_count=len(completed) - len(set(completed)),
    )


def evidence_metrics(evidence_chain: dict[str, Any] | None, answer: str = "") -> EvidenceMetricsV2:
    chain = evidence_chain or {}
    items = list(chain.get("evidence_items") or [])
    candidates = list(chain.get("root_cause_candidates") or [])
    evidence_refs_count = sum(len(candidate.get("supporting_evidence_ids") or []) for candidate in candidates)
    root_supported = any(candidate.get("supporting_evidence_ids") for candidate in candidates)
    fix_supported = bool(items) and any(keyword in answer for keyword in ("建议", "处理", "修复", "排查"))
    answer_without_evidence = int(bool(answer) and not items)
    return EvidenceMetricsV2(
        evidence_chain_complete=bool(items) and bool(candidates),
        evidence_refs_count=evidence_refs_count,
        answer_without_evidence_count=answer_without_evidence,
        root_cause_supported=root_supported,
        fix_steps_supported=fix_supported,
    )


def provider_metrics(trace: dict[str, Any]) -> ProviderMetricsV2:
    synthesizer = _stage(trace, "synthesizer")
    metadata = synthesizer.get("provider_metadata") or {}
    if metadata:
        error_code = str(metadata.get("provider_error_code") or "")
        return ProviderMetricsV2(
            prompt_version=str(metadata.get("prompt_version") or synthesizer.get("prompt_version") or ""),
            llm_enabled=bool(metadata.get("llm_enabled", False)),
            provider_name=str(metadata.get("model_provider") or ""),
            model_name=str(metadata.get("model_name") or synthesizer.get("model") or ""),
            fallback_used=bool(metadata.get("fallback_used", False)),
            schema_valid=bool(metadata.get("schema_valid", True)),
            generation_latency_ms=int(metadata.get("generation_latency_ms") or synthesizer.get("latency_ms") or 0),
            provider_error_count=int(bool(error_code)),
            provider_error_code=error_code,
            provider_error_message=str(metadata.get("provider_error_message") or ""),
        )
    usage = synthesizer.get("llm_usage") or {}
    return ProviderMetricsV2(
        prompt_version=str(synthesizer.get("prompt_version") or ""),
        llm_enabled=bool(synthesizer.get("llm_used", False)),
        provider_name=str(usage.get("provider") or ""),
        model_name=str(synthesizer.get("model") or usage.get("model") or ""),
        fallback_used=not bool(synthesizer.get("llm_used", False)),
        schema_valid=bool(synthesizer.get("schema_valid", not bool(synthesizer.get("error_message")))),
        generation_latency_ms=int(usage.get("latency_ms") or synthesizer.get("latency_ms") or 0),
        provider_error_count=int(bool(synthesizer.get("llm_error"))),
        provider_error_code=str(synthesizer.get("llm_error") or ""),
        provider_error_message=str(synthesizer.get("error_message") or ""),
    )


def _context_metadata(trace: dict[str, Any]) -> dict[str, Any]:
    return _stage(trace, "synthesizer").get("context_metadata") or {}


def _executor_tool_calls(trace: dict[str, Any]) -> list[dict[str, Any]]:
    return list(_stage(trace, "executor").get("tool_calls") or [])


def _stage(trace: dict[str, Any], stage: str) -> dict[str, Any]:
    for step in trace.get("steps", []) if isinstance(trace, dict) else []:
        if step.get("stage") == stage:
            return step
    return {}
