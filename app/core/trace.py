"""
全链路追踪 — 记录 Agent 执行的每个环节。

每次请求必须生成完整 Trace，包含 trace_id、各阶段耗时、工具调用列表。
Day1 使用内存返回，不写入数据库。
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.models import ToolCallRecord, TraceData, TraceSkippedNode, TraceStep, TraceToolCall


class Tracer:
    """执行轨迹记录器。"""

    def __init__(self):
        self._trace_id: str = str(uuid.uuid4())
        self._steps: list[TraceStep] = []
        self._final_answer: str = ""
        self._timestamps: dict[str, float] = {}

    def start_stage(self, stage: str) -> None:
        """记录某个阶段的开始时间。"""
        self._timestamps[stage] = time.perf_counter()

    def end_stage(
        self,
        stage: str,
        output: str = "",
        tool_calls: list[TraceToolCall] | None = None,
        skipped_nodes: list[TraceSkippedNode] | None = None,
        fallback_used: bool = False,
        engine: str = "",
        graph_name: str = "",
        llm_used: bool = False,
        llm_error: str = "",
        prompt_name: str = "",
        prompt_version: str = "",
        model: str = "",
        raw_llm_output: str = "",
        parsed_output: dict[str, Any] | None = None,
        error_message: str = "",
        llm_usage: dict[str, Any] | None = None,
        rag_metadata: dict[str, Any] | None = None,
        grounded_claims: list[dict[str, Any]] | None = None,
        unsupported_claims: list[dict[str, Any]] | None = None,
        claim_grounding_score: float | None = None,
        planning_eval: dict[str, Any] | None = None,
    ) -> None:
        """记录某个阶段的结束时间和输出。"""
        start = self._timestamps.pop(stage, None)
        latency_ms = 0
        if start is not None:
            latency_ms = int((time.perf_counter() - start) * 1000)
        self._steps.append(TraceStep(
            stage=stage,
            engine=engine,
            graph_name=graph_name,
            output=output,
            latency_ms=latency_ms,
            llm_used=llm_used,
            llm_error=llm_error,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            model=model,
            raw_llm_output=raw_llm_output,
            parsed_output=parsed_output,
            error_message=error_message,
            llm_usage=llm_usage,
            tool_calls=tool_calls or [],
            skipped_nodes=skipped_nodes or [],
            fallback_used=fallback_used,
            retrieval_top_k=(rag_metadata or {}).get("retrieval_top_k"),
            score_threshold=(rag_metadata or {}).get("score_threshold"),
            retrieved_count=(rag_metadata or {}).get("retrieved_count"),
            grounding_status=(rag_metadata or {}).get("grounding_status", ""),
            retrieval_latency_ms=(rag_metadata or {}).get("retrieval_latency_ms"),
            query=(rag_metadata or {}).get("query", ""),
            retrieved_chunks=(rag_metadata or {}).get("retrieved_chunks", []),
            rewritten_queries=(rag_metadata or {}).get("rewritten_queries", []),
            query_expansions=(rag_metadata or {}).get("query_expansions", []),
            evidence=(rag_metadata or {}).get("evidence", []),
            rerank_results=(rag_metadata or {}).get("rerank_results", []),
            no_evidence_reason=(rag_metadata or {}).get("no_evidence_reason", ""),
            keyword_hit_count=(rag_metadata or {}).get("keyword_hit_count"),
            vector_hit_count=(rag_metadata or {}).get("vector_hit_count"),
            grounded_claims=grounded_claims or [],
            unsupported_claims=unsupported_claims or [],
            claim_grounding_score=claim_grounding_score,
            expected_intent=(planning_eval or {}).get("expected_intent", ""),
            actual_intent=(planning_eval or {}).get("actual_intent", ""),
            router_correct=(planning_eval or {}).get("router_correct"),
            expected_tools=(planning_eval or {}).get("expected_tools", []),
            actual_tools=(planning_eval or {}).get("actual_tools", []),
            missing_tools=(planning_eval or {}).get("missing_tools", []),
            extra_tools=(planning_eval or {}).get("extra_tools", []),
            plan_quality_score=(planning_eval or {}).get("plan_quality_score"),
            failure_reasons=(planning_eval or {}).get("failure_reasons", []),
        ))

    def end_executor_stage(self, output: str, tool_results: list[ToolCallRecord]) -> None:
        """记录 executor 阶段，并保存每个工具调用的状态摘要。"""
        raw_tool_calls = getattr(tool_results, "tool_calls", [])
        if raw_tool_calls:
            tool_calls = [TraceToolCall(**tool_call) for tool_call in raw_tool_calls]
        else:
            tool_calls = [
                TraceToolCall(
                    node=result.node,
                    tool_name=result.tool_name or result.tool,
                    status=result.status,
                    retry_count=result.retry_count,
                    error=result.error,
                    latency_ms=result.latency_ms,
                    source=result.source,
                    retrieval_top_k=result.rag_metadata.get("retrieval_top_k"),
                    score_threshold=result.rag_metadata.get("score_threshold"),
                    retrieved_count=result.rag_metadata.get("retrieved_count"),
                    grounding_status=result.rag_metadata.get("grounding_status", ""),
                    retrieval_latency_ms=result.rag_metadata.get("retrieval_latency_ms"),
                    retrieval_type=result.rag_metadata.get("retrieval_type", ""),
                    fallback_used=result.rag_metadata.get("fallback_used"),
                )
                for result in tool_results
                if result.tool != "none"
            ]
        rag_metadata = next(
            (
                result.rag_metadata
                for result in tool_results
                if result.tool == "rag_retriever" or result.tool_name == "rag_retriever"
            ),
            {},
        )
        skipped_nodes = [
            TraceSkippedNode(**skipped_node)
            for skipped_node in getattr(tool_results, "skipped_nodes", [])
        ]
        self.end_stage(
            "executor",
            output=output,
            tool_calls=tool_calls,
            skipped_nodes=skipped_nodes,
            fallback_used=getattr(tool_results, "fallback_used", False),
            engine="langgraph",
            graph_name="tool_execution_graph",
            rag_metadata=rag_metadata,
        )

    def end_synthesizer_stage(
        self,
        answer_source: str,
        llm_used: bool,
        llm_error: str | None,
        prompt_name: str = "",
        prompt_version: str = "",
        model: str = "",
        raw_llm_output: str = "",
        parsed_output: dict[str, Any] | None = None,
        error_message: str = "",
        llm_usage: dict[str, Any] | None = None,
    ) -> None:
        """记录 synthesizer 阶段的 LLM 使用情况。"""
        self.end_stage(
            "synthesizer",
            output=f"answer_source={answer_source}",
            engine="deepseek" if llm_used else "fallback",
            llm_used=llm_used,
            llm_error=llm_error or "",
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            model=model,
            raw_llm_output=raw_llm_output,
            parsed_output=parsed_output,
            error_message=error_message,
            llm_usage=llm_usage,
        )

    def end_grounding_checker_stage(self, grounding_check: dict[str, Any]) -> None:
        """Record claim-level grounding check results."""
        self.end_stage(
            "grounding_checker",
            output=f"grounding_score={grounding_check.get('grounding_score', 0.0)}",
            engine="rule_based",
            grounded_claims=grounding_check.get("grounded_claims", []),
            unsupported_claims=grounding_check.get("unsupported_claims", []),
            claim_grounding_score=grounding_check.get("grounding_score"),
        )

    def set_final_answer(self, answer: str) -> None:
        self._final_answer = answer

    def snapshot(self) -> TraceData:
        """返回当前请求的完整追踪数据。"""
        return TraceData(
            trace_id=self._trace_id,
            steps=self._steps,
            final_answer=self._final_answer,
        )
