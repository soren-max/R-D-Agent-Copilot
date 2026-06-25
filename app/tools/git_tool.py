"""
Git 变更查询工具 - 通过 LocalGitAdapter 检索本地确定性提交样例。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.adapters.base import AdapterResult
from app.adapters.git_adapter import GIT_FILE as ADAPTER_GIT_FILE
from app.adapters.git_adapter import GIT_SOURCE, LocalGitAdapter

GIT_FILE = ADAPTER_GIT_FILE


class GitTool:
    name = "git_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        adapter_result = LocalGitAdapter(git_file=Path(GIT_FILE), source=GIT_SOURCE).search_commits(
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
