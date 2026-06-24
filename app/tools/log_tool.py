"""
日志查询工具 — 模拟系统日志搜索。
"""

from __future__ import annotations

import re
from typing import Any

_MOCK_ERROR_LOGS = [
    {"level": "ERROR", "service": "order-service", "timestamp": "2025-06-24 10:23:01",
     "message": "request failed, status=500, path=/api/orders, trace_id=mock-trace-001"},
    {"level": "ERROR", "service": "order-service", "timestamp": "2025-06-24 10:23:00",
     "message": "database connection timeout after 30s, trace_id=mock-trace-002"},
    {"level": "ERROR", "service": "payment-service", "timestamp": "2025-06-24 10:22:55",
     "message": "NullPointerException in processPayment(), line 142, trace_id=mock-trace-003"},
    {"level": "ERROR", "service": "gateway", "timestamp": "2025-06-24 10:22:50",
     "message": "upstream connect error, status=502, from=order-service, trace_id=mock-trace-004"},
    {"level": "CRITICAL", "service": "cache-service", "timestamp": "2025-06-24 10:22:45",
     "message": "Redis connection pool exhausted, max_connections=50, trace_id=mock-trace-005"},
    {"level": "ERROR", "service": "notification-service", "timestamp": "2025-06-24 10:22:30",
     "message": "message queue send failed, topic=order_notify, status=503, trace_id=mock-trace-008"},
]

_MOCK_NORMAL_LOGS = [
    {"level": "INFO", "service": "order-service", "timestamp": "2025-06-24 10:23:05",
     "message": "health check passed, status=200"},
    {"level": "INFO", "service": "payment-service", "timestamp": "2025-06-24 10:23:03",
     "message": "payment completed, order_id=ORD-20250624-001"},
]

_ERROR_KEYWORDS = ["500", "报错", "error", "异常", "exception", "timeout", "超时",
                   "fail", "失败", "崩溃", "crash", "oom", "502", "503",
                   "连不上", "挂", "慢", "卡"]


class LogTool:
    name = "log_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        query_lower = query.lower()
        matched_keywords = [kw for kw in _ERROR_KEYWORDS
                           if re.search(re.escape(kw), query_lower)]

        if matched_keywords:
            relevant = [log for log in _MOCK_ERROR_LOGS
                       if any(kw in log["message"].lower() for kw in matched_keywords)]
            if not relevant:
                relevant = _MOCK_ERROR_LOGS[:3]
            lines = "\n".join(
                f"[{e['level']:>8}] [{e['service']}] {e['timestamp']}  {e['message']}"
                for e in relevant
            )
            return {
                "tool_name": "log_tool",
                "result": f"查询到 {len(relevant)} 条相关错误日志：\n匹配关键词：{', '.join(matched_keywords)}\n{lines}",
                "confidence": round(min(0.65 + 0.08 * len(relevant), 0.95), 2),
                "source": "mock",
            }
        else:
            lines = "\n".join(
                f"[{e['level']:>8}] [{e['service']}] {e['timestamp']}  {e['message']}"
                for e in _MOCK_NORMAL_LOGS[:3]
            )
            return {
                "tool_name": "log_tool",
                "result": f"未发现明显异常，最近日志如下：\n{lines}",
                "confidence": 0.50,
                "source": "mock",
            }
