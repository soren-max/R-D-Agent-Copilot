"""Log system adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
from time import perf_counter

from app.adapters.base import AdapterResult

LOG_SOURCE = "data/logs/order-service.log"
LOG_FILE = Path(__file__).resolve().parents[2] / LOG_SOURCE

_MATCH_KEYWORDS = [
    "500",
    "报错",
    "异常",
    "timeout",
    "超时",
    "order",
    "订单",
]


class LogAdapter(ABC):
    """Adapter boundary for log search data sources."""

    @abstractmethod
    def search_logs(self, query: str, context: str = "") -> AdapterResult:
        """Search logs for troubleshooting evidence."""


class LocalLogAdapter(LogAdapter):
    """Local mock log adapter backed by deterministic sample data."""

    adapter_name = "local_log_adapter"

    def __init__(self, log_file: Path = LOG_FILE, source: str = LOG_SOURCE) -> None:
        self.log_file = log_file
        self.source = source

    def search_logs(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()

        if not self.log_file.exists():
            return AdapterResult(
                adapter_name=self.adapter_name,
                status="failed",
                data="",
                source=self.source,
                confidence=0.0,
                error="file_not_found",
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        query_text = f"{query} {context}".lower()
        matched_keywords = [
            keyword for keyword in _MATCH_KEYWORDS
            if re.search(re.escape(keyword.lower()), query_text)
        ]

        lines = self.log_file.read_text(encoding="utf-8").splitlines()
        if matched_keywords:
            relevant_lines = [
                line for line in lines
                if any(keyword.lower() in line.lower() for keyword in matched_keywords)
            ]
        else:
            relevant_lines = []

        if not relevant_lines:
            relevant_lines = lines[:3]
            confidence = 0.55
            summary = "未命中明确关键词，返回最近日志片段："
        else:
            confidence = 0.9
            summary = f"命中关键词：{', '.join(matched_keywords)}。匹配到 {len(relevant_lines)} 条相关日志："

        return AdapterResult(
            adapter_name=self.adapter_name,
            status="success",
            data=summary + "\n" + "\n".join(relevant_lines[:5]),
            source=self.source,
            confidence=confidence,
            error=None,
            latency_ms=(perf_counter() - started_at) * 1000,
        )
