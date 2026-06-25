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
            tool_calls=tool_calls or [],
            skipped_nodes=skipped_nodes or [],
            fallback_used=fallback_used,
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
                )
                for result in tool_results
                if result.tool != "none"
            ]
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
        )

    def end_synthesizer_stage(
        self,
        answer_source: str,
        llm_used: bool,
        llm_error: str | None,
    ) -> None:
        """记录 synthesizer 阶段的 LLM 使用情况。"""
        self.end_stage(
            "synthesizer",
            output=f"answer_source={answer_source}",
            engine="deepseek" if llm_used else "fallback",
            llm_used=llm_used,
            llm_error=llm_error or "",
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
