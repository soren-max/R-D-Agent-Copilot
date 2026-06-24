"""
工具执行器 — 按计划调度工具。

职责边界：
- 只执行工具
- 不重新规划
- 不修改 Planner 输出
- 不绕过工具直接回答
"""

from __future__ import annotations

import time
from typing import Any

from app.core.models import Plan, PlanStep, ToolCallRecord
from app.tools.log_tool import LogTool
from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool


class Executor:
    """执行计划中的每一步工具调用。"""

    def __init__(self):
        self._tools: dict[str, Any] = {
            "log_tool": LogTool(),
            "config_tool": ConfigTool(),
            "git_tool": GitTool(),
        }

    def execute(self, query: str, plan: Plan) -> list[ToolCallRecord]:
        """
        遍历计划步骤，为每步调用对应工具。

        返回 ToolCallRecord 列表（执行成功/跳过/失败的记录）。
        """
        results: list[ToolCallRecord] = []

        for step in plan.steps:
            record = ToolCallRecord(
                step_id=step.id,
                action=step.action,
                tool=step.tool,
                description=step.description,
            )

            if step.tool == "none":
                # simple_qa 无需工具调用
                record.status = "skipped"
                record.result = "无需工具调用，直接回答即可。"
                record.latency_ms = 0
                results.append(record)
                continue

            tool = self._tools.get(step.tool)
            if tool is None:
                record.status = "error"
                record.result = f"未知工具: {step.tool}"
                record.latency_ms = 0
                results.append(record)
                continue

            # 执行工具
            start = time.perf_counter()
            try:
                output = tool.run(query)
                elapsed = int((time.perf_counter() - start) * 1000)
                record.result = output.get("result", str(output))
                record.confidence = output.get("confidence", 0.0)
                record.latency_ms = elapsed
                record.status = "success"
            except Exception as e:
                elapsed = int((time.perf_counter() - start) * 1000)
                record.result = f"工具执行异常: {e}"
                record.latency_ms = elapsed
                record.status = "error"

            results.append(record)

        return results
