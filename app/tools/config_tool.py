"""
配置查询工具 — 模拟服务配置读取。
"""

from __future__ import annotations

import re
from typing import Any

_MOCK_CONFIGS = [
    {"key": "payment.timeout", "dev": "3s", "staging": "5s", "prod": "1s",
     "note": "存在环境配置不一致，prod 超时时间最短，可能导致 timeout"},
    {"key": "order.max_retry", "dev": "3", "staging": "5", "prod": "3",
     "note": "各环境一致"},
    {"key": "database.max_connections", "dev": "10", "staging": "30", "prod": "100",
     "note": "prod 连接池最大，与负载匹配"},
    {"key": "redis.timeout_ms", "dev": "5000", "staging": "3000", "prod": "1000",
     "note": "prod 超时最短，高并发时可能触发 timeout"},
    {"key": "log.level", "dev": "DEBUG", "staging": "INFO", "prod": "WARN",
     "note": "prod 仅记录 WARN 以上级别，可能遗漏排查信息"},
    {"key": "feature.order_auto_cancel", "dev": "true", "staging": "true", "prod": "false",
     "note": "prod 未开启自动取消功能，与需求文档不一致"},
    {"key": "payment.retry_interval_ms", "dev": "100", "staging": "200", "prod": "500",
     "note": "prod 重试间隔最长，支付失败后恢复慢"},
]

_CONFIG_KEYWORDS = {
    "payment": ["payment.timeout", "payment.retry_interval_ms"],
    "order": ["order.max_retry", "feature.order_auto_cancel"],
    "database": ["database.max_connections"], "db": ["database.max_connections"],
    "redis": ["redis.timeout_ms"], "cache": ["redis.timeout_ms"],
    "timeout": ["payment.timeout", "redis.timeout_ms"],
    "日志": ["log.level"], "log": ["log.level"],
    "feature": ["feature.order_auto_cancel"],
    "retry": ["order.max_retry", "payment.retry_interval_ms"],
}


class ConfigTool:
    name = "config_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        query_lower = query.lower()
        if context:
            query_lower += " " + context.lower()

        matched_keys: set[str] = set()
        for keyword, keys in _CONFIG_KEYWORDS.items():
            if re.search(re.escape(keyword), query_lower):
                matched_keys.update(keys)

        configs = [c for c in _MOCK_CONFIGS if c["key"] in matched_keys] if matched_keys else _MOCK_CONFIGS

        if not configs:
            return {"tool_name": "config_tool", "result": "未查询到相关配置项。", "confidence": 0.50, "source": "mock"}

        lines: list[str] = []
        for cfg in configs:
            lines.append(f"  {cfg['key']}: dev={cfg['dev']}, staging={cfg['staging']}, prod={cfg['prod']}")
            lines.append(f"  → {cfg['note']}")

        has_diff = any("不一致" in c["note"] for c in configs)
        summary = f"查询到 {len(configs)} 个相关配置项："
        if has_diff:
            summary += " 发现环境配置差异。"
        return {
            "tool_name": "config_tool",
            "result": summary + "\n" + "\n".join(lines),
            "confidence": 0.85 if has_diff else 0.70,
            "source": "mock",
        }
