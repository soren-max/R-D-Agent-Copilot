"""Deterministic query rewrite for local troubleshooting RAG."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class QueryRewriteResult:
    original_query: str
    rewritten_queries: list[str] = field(default_factory=list)
    expansions: list[str] = field(default_factory=list)

    def all_queries(self) -> list[str]:
        queries: list[str] = []
        for query in [self.original_query, *self.rewritten_queries]:
            normalized = " ".join(query.split())
            if normalized and normalized not in queries:
                queries.append(normalized)
        return queries


_EXPANSION_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("端口被占用", "端口占用", "端口冲突", "端口已被使用"), ("port already in use", "failed to start", "listen port")),
    (("启动失败", "起不来", "无法启动"), ("failed to start", "health check", "deployment")),
    (("redis", "缓存"), ("redis timeout", "connection pool", "slowlog")),
    (("连接池", "连接超时"), ("connection pool", "connection timeout", "timeout")),
    (("nginx", "网关"), ("nginx", "upstream", "502 bad gateway")),
    (("502", "bad gateway"), ("502 bad gateway", "upstream service unavailable", "proxy timeout")),
    (("慢查询", "sql 慢", "数据库慢"), ("slow query", "execution plan", "missing index")),
    (("ci", "构建失败", "流水线失败"), ("ci build failed", "job log", "dependency resolution")),
    (("回滚", "撤销提交"), ("git rollback", "revert", "risky commit")),
]


def rewrite_query(query: str, max_expansions: int = 8) -> QueryRewriteResult:
    """Expand common Chinese troubleshooting phrases into searchable terms."""

    normalized = _normalize(query)
    expansions: list[str] = []
    lowered = normalized.lower()

    for triggers, terms in _EXPANSION_RULES:
        if any(trigger.lower() in lowered for trigger in triggers):
            for term in terms:
                if term not in expansions:
                    expansions.append(term)
                if len(expansions) >= max_expansions:
                    break
        if len(expansions) >= max_expansions:
            break

    rewritten_queries = []
    if expansions:
        rewritten_queries.append(f"{normalized} {' '.join(expansions)}")

    return QueryRewriteResult(
        original_query=normalized,
        rewritten_queries=rewritten_queries,
        expansions=expansions,
    )


def _normalize(query: str) -> str:
    text = query.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("，", " ").replace("？", " ").replace("。", " ")
    return " ".join(text.split())
