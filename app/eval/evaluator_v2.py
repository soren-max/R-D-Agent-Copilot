"""Evaluation v2 rule-based report builder."""

from __future__ import annotations

from typing import Any

from app.core.logging import log_event
from app.eval.metrics import (
    context_metrics,
    evidence_metrics,
    memory_metrics,
    provider_metrics,
    rag_metrics,
    resume_metrics,
    tool_metrics,
)
from app.eval.schemas import EvaluationReportV2


class EvaluationV2Evaluator:
    """Build an explainable multi-module EvaluationReportV2."""

    def evaluate(self, payload: dict[str, Any]) -> EvaluationReportV2:
        trace = payload.get("trace") or {}
        tool_results = list(payload.get("tool_results") or [])
        answer = str(payload.get("answer") or "")
        context = context_metrics(trace, query=str(payload.get("query") or ""))
        tool = tool_metrics(trace, tool_results)
        rag = rag_metrics(tool_results, trace)
        memory = memory_metrics(trace, answer, tool_results)
        resume = resume_metrics(trace, payload.get("checkpoint"), payload.get("resume_result"))
        evidence = evidence_metrics(payload.get("evidence_chain"), answer)
        provider = provider_metrics(trace)
        overall = self._overall(context, tool, rag, memory, resume, evidence)
        log_event(
            event="evaluation_v2_completed",
            stage="evaluation_v2",
            run_id=str(payload.get("run_id") or trace.get("trace_id") or ""),
            message=f"overall={overall}",
        )
        return EvaluationReportV2(
            run_id=str(payload.get("run_id") or trace.get("trace_id") or ""),
            overall=overall,
            context=context,
            tool=tool,
            rag=rag,
            memory=memory,
            resume=resume,
            evidence=evidence,
            provider=provider,
        )

    def _overall(self, context, tool, rag, memory, resume, evidence) -> float:
        components = [
            1.0 if context.current_query_preserved else 0.0,
            tool.tool_success_rate,
            rag.grounding_score,
            1.0 if memory.memory_misused_as_current_fact_count == 0 else 0.0,
            1.0 if resume.duplicated_step_count == 0 else 0.0,
            1.0 if evidence.evidence_chain_complete else 0.5,
        ]
        return round(sum(components) / len(components), 4)
