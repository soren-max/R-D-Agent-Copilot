"""
Git 变更查询工具 — 模拟最近代码变更分析。
"""

from __future__ import annotations

import re
from typing import Any

_MOCK_COMMITS = [
    {"hash": "a1b2c3d", "author": "zhangsan", "timestamp": "2025-06-23 14:30:00",
     "message": "fix: 修复订单超时未取消的 bug",
     "files_changed": ["order-service/.../OrderService.java", "order-service/.../OrderTimeoutJob.java"],
     "detail": "修改了订单超时取消逻辑，将 timeout 检查从 30s 调整为 60s。"},
    {"hash": "d4e5f6g", "author": "lisi", "timestamp": "2025-06-22 09:15:00",
     "message": "feat: 新增支付重试机制",
     "files_changed": ["payment-service/.../PaymentRetryHandler.java", "payment-service/.../application.yml"],
     "detail": "新增支付重试处理器，失败后最多重试 3 次，间隔 500ms。"},
    {"hash": "h7i8j9k", "author": "wangwu", "timestamp": "2025-06-21 17:45:00",
     "message": "refactor: 重构用户认证模块",
     "files_changed": ["user-service/.../AuthFilter.java", "user-service/.../application.yml"],
     "detail": "重构了 JWT 认证过滤器，将 token 有效期从 24h 缩短为 12h。"},
    {"hash": "m0n1o2p", "author": "zhangsan", "timestamp": "2025-06-20 11:20:00",
     "message": "fix: 修复数据库连接池泄漏问题",
     "files_changed": ["common-lib/.../ConnectionPool.java"],
     "detail": "修复了数据库连接未正确释放的问题，在 finally 块中补充了释放逻辑。"},
    {"hash": "q3r4s5t", "author": "lisi", "timestamp": "2025-06-19 08:30:00",
     "message": "feat: 新增订单自动取消功能",
     "files_changed": ["order-service/.../OrderAutoCancelJob.java", "order-service/.../application.yml"],
     "detail": "新增定时任务自动取消超时未支付订单。feature.order_auto_cancel 配置默认关闭。"},
]

_COMMIT_KEYWORDS = {
    "order": [0, 4], "订单": [0, 4], "payment": [1], "支付": [1],
    "user": [2], "用户": [2], "auth": [2], "认证": [2], "token": [2],
    "database": [3], "数据库": [3], "connection": [3], "连接": [3], "pool": [3],
    "timeout": [0], "超时": [0, 4], "retry": [1], "重试": [1],
    "cancel": [0, 4], "取消": [0, 4], "配置": [1, 4], "config": [1, 4],
    "500": [0], "502": [0], "503": [0], "error": [0, 3], "异常": [0, 3],
}


class GitTool:
    name = "git_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        query_lower = query.lower()
        if context:
            query_lower += " " + context.lower()

        matched_indices: set[int] = set()
        for keyword, indices in _COMMIT_KEYWORDS.items():
            if re.search(re.escape(keyword), query_lower):
                matched_indices.update(indices)

        commits = [_MOCK_COMMITS[i] for i in sorted(matched_indices)] if matched_indices else _MOCK_COMMITS[:2]

        if not commits:
            return {"tool_name": "git_tool", "result": "未查询到相关提交记录。", "confidence": 0.50, "source": "mock"}

        lines: list[str] = []
        for c in commits:
            lines.append(f"提交 {c['hash']}  by {c['author']}  at {c['timestamp']}")
            lines.append(f"  信息: {c['message']}")
            lines.append(f"  变更: {', '.join(c['files_changed'])}")
            lines.append(f"  详情: {c['detail']}")
            lines.append("")

        return {
            "tool_name": "git_tool",
            "result": f"查询到 {len(commits)} 条相关提交记录：\n" + "\n".join(lines).strip(),
            "confidence": 0.85 if len(commits) <= 3 else 0.70,
            "source": "mock",
        }
