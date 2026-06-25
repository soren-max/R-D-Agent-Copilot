"""Git platform adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any

from app.adapters.base import AdapterResult

GIT_SOURCE = "data/git/commits.json"
GIT_FILE = Path(__file__).resolve().parents[2] / GIT_SOURCE

_RELEVANT_KEYWORDS = [
    "order-service",
    "order",
    "订单",
    "异常",
    "error",
    "payment",
    "支付",
    "timeout",
    "超时",
    "retry",
    "重试",
]

_RISK_WEIGHT = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


class GitAdapter(ABC):
    """Adapter boundary for commit search data sources."""

    @abstractmethod
    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        """Search commit metadata for troubleshooting evidence."""


class LocalGitAdapter(GitAdapter):
    """Local mock Git adapter backed by deterministic sample data."""

    adapter_name = "local_git_adapter"

    def __init__(self, git_file: Path = GIT_FILE, source: str = GIT_SOURCE) -> None:
        self.git_file = git_file
        self.source = source

    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()

        if not self.git_file.exists():
            return AdapterResult(
                adapter_name=self.adapter_name,
                status="failed",
                data="",
                source=self.source,
                confidence=0.0,
                error="file_not_found",
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        commits = json.loads(self.git_file.read_text(encoding="utf-8"))
        query_text = f"{query} {context}".lower()

        ranked_commits = []
        for index, commit in enumerate(commits):
            searchable = self._searchable_text(commit)
            relevance = self._relevance_score(searchable, query_text)
            if relevance <= 0:
                continue
            risk_score = _RISK_WEIGHT.get(str(commit.get("risk_level", "")).lower(), 0)
            ranked_commits.append((relevance, risk_score, index, commit))

        ranked_commits.sort(key=lambda item: (-item[0], -item[1], item[2]))
        selected = [commit for _, _, _, commit in ranked_commits[:3]]

        if not selected:
            data = "未发现与 order-service、异常处理或支付流程相关的近期提交。"
            confidence = 0.55
        else:
            lines = []
            for commit in selected:
                changed_files = ", ".join(commit.get("changed_files", []))
                lines.append(
                    f"{commit.get('commit_id')} [{commit.get('risk_level')}] "
                    f"{commit.get('message')} by {commit.get('author')}"
                )
                lines.append(f"  变更文件: {changed_files}")
                lines.append(f"  说明: {commit.get('summary')}")
            data = "最近相关提交风险摘要：\n" + "\n".join(lines)
            confidence = 0.8

        return AdapterResult(
            adapter_name=self.adapter_name,
            status="success",
            data=data,
            source=self.source,
            confidence=confidence,
            error=None,
            latency_ms=(perf_counter() - started_at) * 1000,
        )

    def _searchable_text(self, commit: dict[str, Any]) -> str:
        values = [
            str(commit.get("commit_id", "")),
            str(commit.get("message", "")),
            str(commit.get("risk_level", "")),
            str(commit.get("summary", "")),
            " ".join(commit.get("changed_files", [])),
        ]
        return " ".join(values).lower()

    def _relevance_score(self, searchable: str, query_text: str) -> int:
        score = 0
        for keyword in _RELEVANT_KEYWORDS:
            keyword_lower = keyword.lower()
            if not re.search(re.escape(keyword_lower), searchable):
                continue
            score += 2 if re.search(re.escape(keyword_lower), query_text) else 1
        return score
