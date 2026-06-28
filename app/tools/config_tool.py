"""
配置查询工具 - 通过 LocalConfigAdapter 调用本地 Mock Config API。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.adapters.base import AdapterResult
from app.adapters.config_adapter import DEV_CONFIG_FILE as ADAPTER_DEV_CONFIG_FILE
from app.adapters.config_adapter import DEV_CONFIG_SOURCE, LocalConfigAdapter
from app.adapters.config_adapter import PROD_CONFIG_FILE as ADAPTER_PROD_CONFIG_FILE
from app.adapters.config_adapter import PROD_CONFIG_SOURCE

DEV_CONFIG_FILE = ADAPTER_DEV_CONFIG_FILE
PROD_CONFIG_FILE = ADAPTER_PROD_CONFIG_FILE


class ConfigTool:
    name = "config_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        adapter_result = LocalConfigAdapter(
            dev_config_file=Path(DEV_CONFIG_FILE),
            prod_config_file=Path(PROD_CONFIG_FILE),
        ).compare_configs(query, context or "")
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
