"""
全链路追踪 — 记录 Agent 执行的每个环节。

每次请求必须生成完整 Trace，包含 trace_id、各阶段耗时、工具调用列表。
Day1 使用内存返回，不写入数据库。
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.models import ToolCallRecord, TraceData, TraceStep, TraceToolCall


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
    ) -> None:
        """记录某个阶段的结束时间和输出。"""
        start = self._timestamps.pop(stage, None)
        latency_ms = 0
        if start is not None:
            latency_ms = int((time.perf_counter() - start) * 1000)
        self._steps.append(TraceStep(
            stage=stage,
            output=output,
            latency_ms=latency_ms,
            tool_calls=tool_calls or [],
        ))

    def end_executor_stage(self, output: str, tool_results: list[ToolCallRecord]) -> None:
        """记录 executor 阶段，并保存每个工具调用的状态摘要。"""
        tool_calls = [
            TraceToolCall(
                tool_name=result.tool_name or result.tool,
                status=result.status,
                latency_ms=result.latency_ms,
                source=result.source,
            )
            for result in tool_results
            if result.tool != "none"
        ]
        self.end_stage("executor", output=output, tool_calls=tool_calls)

    def set_final_answer(self, answer: str) -> None:
        self._final_answer = answer

    def snapshot(self) -> TraceData:
        """返回当前请求的完整追踪数据。"""
        return TraceData(
            trace_id=self._trace_id,
            steps=self._steps,
            final_answer=self._final_answer,
        )
