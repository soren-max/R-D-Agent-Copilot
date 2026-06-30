"""
工具执行器 — 按计划调度工具。

职责边界：
- 只执行工具
- 不重新规划
- 不修改 Planner 输出
- 不绕过工具直接回答
"""

from __future__ import annotations

from typing import Any

from app.core.models import Plan, ToolCallRecord
from app.agent.graph import build_execution_graph


class ToolExecutionResults(list[ToolCallRecord]):
    """Tool result list with LangGraph execution metadata attached."""

    def __init__(
        self,
        records: list[ToolCallRecord],
        tool_calls: list[dict[str, Any]],
        skipped_nodes: list[dict[str, Any]],
        fallback_used: bool,
    ):
        super().__init__(records)
        self.tool_calls = tool_calls
        self.skipped_nodes = skipped_nodes
        self.fallback_used = fallback_used


class Executor:
    """执行计划中的每一步工具调用。"""

    def __init__(self):
        self._graph = build_execution_graph()

    def execute(self, query: str, plan: Plan) -> list[ToolCallRecord]:
        """
        将 Planner 输出交给 LangGraph 执行工具编排。

        返回实际执行的 ToolCallRecord 列表，跳过节点保存在返回列表的 skipped_nodes 元数据中。
        """
        graph_result = self._graph.invoke({
            "query": query,
            "plan": plan.model_dump(),
            "tool_results": [],
            "tool_calls": [],
            "skipped_nodes": [],
            "fallback_used": False,
            "errors": [],
        })
        records = [
            ToolCallRecord(
                step_id=result.get("step_id", 0),
                action=result.get("action", ""),
                node=result.get("node", ""),
                tool=result.get("tool", result.get("tool_name", "")),
                tool_name=result.get("tool_name", result.get("tool", "")),
                description=result.get("description", ""),
                result=result.get("result", ""),
                confidence=result.get("confidence", 0.0),
                source=result.get("source", ""),
                documents=result.get("documents", []),
                rag_metadata=result.get("rag_metadata", {}),
                error=result.get("error", ""),
                retry_count=result.get("retry_count", 0),
                latency_ms=result.get("latency_ms", 0),
                status=result.get("status", "pending"),
            )
            for result in graph_result.get("tool_results", [])
        ]
        return ToolExecutionResults(
            records,
            graph_result.get("tool_calls", []),
            graph_result.get("skipped_nodes", []),
            graph_result.get("fallback_used", False),
        )
