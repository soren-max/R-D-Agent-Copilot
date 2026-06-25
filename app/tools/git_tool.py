"""
Git 变更查询工具 - 从本地确定性提交样例中检索风险线索。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

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


class GitTool:
    name = "git_tool"

    def run(self, query: str, context: str | None = None) -> dict[str, Any]:
        if not GIT_FILE.exists():
            return self._file_not_found()

        commits = json.loads(GIT_FILE.read_text(encoding="utf-8"))
        query_text = f"{query} {context or ''}".lower()

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
            result = "未发现与 order-service、异常处理或支付流程相关的近期提交。"
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
            result = "最近相关提交风险摘要：\n" + "\n".join(lines)
            confidence = 0.8

        return {
            "tool_name": self.name,
            "result": result,
            "confidence": confidence,
            "source": GIT_SOURCE,
        }

    def _file_not_found(self) -> dict[str, Any]:
        return {
            "tool_name": self.name,
            "result": "",
            "confidence": 0.0,
            "source": GIT_SOURCE,
            "error": "file_not_found",
        }

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
