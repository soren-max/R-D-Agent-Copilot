"""
日志查询工具 - 从本地确定性日志样例中检索排障线索。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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


class LogTool:
    name = "log_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        if not LOG_FILE.exists():
            return self._file_not_found()

        query_text = f"{query} {context or ''}".lower()
        matched_keywords = [
            keyword for keyword in _MATCH_KEYWORDS
            if re.search(re.escape(keyword.lower()), query_text)
        ]

        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
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

        return {
            "tool_name": self.name,
            "result": summary + "\n" + "\n".join(relevant_lines[:5]),
            "confidence": confidence,
            "source": LOG_SOURCE,
        }

    def _file_not_found(self) -> dict[str, Any]:
        return {
            "tool_name": self.name,
            "result": "",
            "confidence": 0.0,
            "source": LOG_SOURCE,
            "error": "file_not_found",
        }
