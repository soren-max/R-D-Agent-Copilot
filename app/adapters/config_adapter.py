"""Config center adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any

from app.adapters.base import AdapterResult

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


class ConfigAdapter(ABC):
    """Adapter boundary for config comparison data sources."""

    @abstractmethod
    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        """Compare configuration data for troubleshooting evidence."""


class LocalConfigAdapter(ConfigAdapter):
    """Local mock config adapter backed by deterministic sample data."""

    adapter_name = "local_config_adapter"

    def __init__(
        self,
        dev_config_file: Path = DEV_CONFIG_FILE,
        prod_config_file: Path = PROD_CONFIG_FILE,
        source: str = CONFIG_SOURCE,
    ) -> None:
        self.dev_config_file = dev_config_file
        self.prod_config_file = prod_config_file
        self.source = source

    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()

        if not self.dev_config_file.exists() or not self.prod_config_file.exists():
            return AdapterResult(
                adapter_name=self.adapter_name,
                status="failed",
                data="",
                source=self.source,
                confidence=0.0,
                error="file_not_found",
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        dev_config = json.loads(self.dev_config_file.read_text(encoding="utf-8"))
        prod_config = json.loads(self.prod_config_file.read_text(encoding="utf-8"))

        dev_flat = self._flatten(dev_config)
        prod_flat = self._flatten(prod_config)
        query_text = f"{query} {context}".lower()

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
            data = "发现订单/支付相关配置差异：\n" + "\n".join(diff_lines)
            confidence = 0.85
        else:
            data = "未发现订单、支付、timeout 或 retry 相关配置差异。"
            confidence = 0.6

        return AdapterResult(
            adapter_name=self.adapter_name,
            status="success",
            data=data,
            source=self.source,
            confidence=confidence,
            error=None,
            latency_ms=(perf_counter() - started_at) * 1000,
        )

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
