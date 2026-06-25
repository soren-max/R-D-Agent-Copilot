"""
配置查询工具 - 对比本地 dev/prod 确定性配置样例。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEV_CONFIG_SOURCE = "data/configs/dev.json"
PROD_CONFIG_SOURCE = "data/configs/prod.json"
DEV_CONFIG_FILE = Path(__file__).resolve().parents[2] / DEV_CONFIG_SOURCE
PROD_CONFIG_FILE = Path(__file__).resolve().parents[2] / PROD_CONFIG_SOURCE
CONFIG_SOURCE = f"{DEV_CONFIG_SOURCE},{PROD_CONFIG_SOURCE}"

_RELEVANT_KEYWORDS = [
    "order",
    "订单",
    "payment",
    "支付",
    "timeout",
    "超时",
    "retry",
    "重试",
]


class ConfigTool:
    name = "config_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        missing_file = self._missing_file()
        if missing_file:
            return missing_file

        dev_config = json.loads(DEV_CONFIG_FILE.read_text(encoding="utf-8"))
        prod_config = json.loads(PROD_CONFIG_FILE.read_text(encoding="utf-8"))

        dev_flat = self._flatten(dev_config)
        prod_flat = self._flatten(prod_config)
        query_text = f"{query} {context or ''}".lower()

        diff_lines: list[str] = []
        for key in sorted(set(dev_flat) | set(prod_flat)):
            if dev_flat.get(key) == prod_flat.get(key):
                continue
            if not self._is_relevant(key, query_text):
                continue
            diff_lines.append(
                f"{key}: dev={dev_flat.get(key)!r}, prod={prod_flat.get(key)!r}"
            )

        if diff_lines:
            result = "发现订单/支付相关配置差异：\n" + "\n".join(diff_lines)
            confidence = 0.85
        else:
            result = "未发现订单、支付、timeout 或 retry 相关配置差异。"
            confidence = 0.6

        return {
            "tool_name": self.name,
            "result": result,
            "confidence": confidence,
            "source": CONFIG_SOURCE,
        }

    def _missing_file(self) -> dict[str, Any] | None:
        if not DEV_CONFIG_FILE.exists() or not PROD_CONFIG_FILE.exists():
            return {
                "tool_name": self.name,
                "result": "",
                "confidence": 0.0,
                "source": CONFIG_SOURCE,
                "error": "file_not_found",
            }
        return None

    def _flatten(self, data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flattened.update(self._flatten(value, path))
            else:
                flattened[path] = value
        return flattened

    def _is_relevant(self, key: str, query_text: str) -> bool:
        key_text = key.lower()
        if any(keyword in key_text for keyword in ["order", "payment", "timeout", "retry"]):
            return True
        return any(re.search(re.escape(keyword.lower()), query_text) for keyword in _RELEVANT_KEYWORDS)
