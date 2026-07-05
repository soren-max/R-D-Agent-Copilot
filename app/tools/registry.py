"""Local tool registry used by ToolGateway."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool


ToolFactory = Callable[[], Any]


class ToolRegistry:
    """Registry of tools allowed to cross the gateway boundary."""

    def __init__(self) -> None:
        self._factories: dict[str, ToolFactory | None] = {}

    def register(self, tool_name: str, factory: ToolFactory | None = None) -> None:
        self._factories[tool_name] = factory

    def is_registered(self, tool_name: str) -> bool:
        return tool_name in self._factories

    def create(self, tool_name: str) -> Any:
        factory = self._factories.get(tool_name)
        if factory is None:
            return None
        return factory()


def default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("log_tool", LogTool)
    registry.register("config_tool", ConfigTool)
    registry.register("git_tool", GitTool)
    registry.register("rag_retriever", None)
    return registry
