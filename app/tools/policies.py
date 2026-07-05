"""Deterministic tool gateway validation and policy checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolGatewayPolicy:
    """Small rule-based policy for local demo tools."""

    allowed_tools: set[str] = field(default_factory=lambda: {
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    })

    def validate_params(self, tool_name: str, params: dict[str, Any]) -> str:
        query = params.get("query")
        if not isinstance(query, str) or not query.strip():
            return "missing_query"
        return ""

    def is_allowed(self, tool_name: str, params: dict[str, Any]) -> bool:
        return tool_name in self.allowed_tools
