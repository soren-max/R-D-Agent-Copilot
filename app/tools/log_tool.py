"""
日志查询工具 - 通过 LocalLogAdapter 调用本地 Mock Log API。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.adapters.base import AdapterResult
from app.adapters.log_adapter import LOG_FILE as ADAPTER_LOG_FILE
from app.adapters.log_adapter import LocalLogAdapter

LOG_FILE = ADAPTER_LOG_FILE


class LogTool:
    name = "log_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        adapter_result = LocalLogAdapter(log_file=Path(LOG_FILE)).search_logs(
            query,
            context or "",
        )
        return self._to_tool_result(adapter_result)

    def _to_tool_result(self, adapter_result: AdapterResult) -> dict[str, Any]:
        result = {
            "tool_name": self.name,
            "result": adapter_result.data if adapter_result.status == "success" else "",
            "confidence": adapter_result.confidence,
            "source": adapter_result.source,
        }
        if adapter_result.status == "failed":
            result["error"] = adapter_result.error or "adapter_failed"
        return result
