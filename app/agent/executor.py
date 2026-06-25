"""
工具执行器 — 按计划调度工具。

职责边界：
- 只执行工具
- 不重新规划
- 不修改 Planner 输出
- 不绕过工具直接回答
"""

from __future__ import annotations

from app.core.models import Plan, ToolCallRecord
from app.agent.graph import build_execution_graph


class Executor:
    """执行计划中的每一步工具调用。"""

    def __init__(self):
        self._graph = build_execution_graph()

    def execute(self, query: str, plan: Plan) -> list[ToolCallRecord]:
        """
        将 Planner 输出交给 LangGraph 执行工具编排。

        返回 ToolCallRecord 列表（执行成功/跳过/失败的记录）。
        """
        graph_result = self._graph.invoke({
            "query": query,
            "plan": plan.model_dump(),
            "tool_results": [],
            "errors": [],
        })
        return [
            ToolCallRecord(
                step_id=result.get("step_id", 0),
                action=result.get("action", ""),
                tool=result.get("tool", result.get("tool_name", "")),
                tool_name=result.get("tool_name", result.get("tool", "")),
                description=result.get("description", ""),
                result=result.get("result", ""),
                confidence=result.get("confidence", 0.0),
                source=result.get("source", ""),
                documents=result.get("documents", []),
                error=result.get("error", ""),
                latency_ms=result.get("latency_ms", 0),
                status=result.get("status", "pending"),
            )
            for result in graph_result.get("tool_results", [])
        ]
