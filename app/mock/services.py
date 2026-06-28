"""Deterministic mock platform service logic.

These functions back the local /mock/* API endpoints. They read only bundled
sample data and never call external services.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]

LOG_SOURCE = "data/logs/order-service.log"
DEV_CONFIG_SOURCE = "data/configs/dev.json"
PROD_CONFIG_SOURCE = "data/configs/prod.json"
CONFIG_SOURCE = f"{DEV_CONFIG_SOURCE},{PROD_CONFIG_SOURCE}"
GIT_SOURCE = "data/git/commits.json"

LOG_FILE = ROOT_DIR / LOG_SOURCE
DEV_CONFIG_FILE = ROOT_DIR / DEV_CONFIG_SOURCE
PROD_CONFIG_FILE = ROOT_DIR / PROD_CONFIG_SOURCE
GIT_FILE = ROOT_DIR / GIT_SOURCE

LOG_MATCH_KEYWORDS = [
    "500",
    "报错",
    "异常",
    "timeout",
    "超时",
    "order",
    "订单",
]

CONFIG_RELEVANT_KEYWORDS = [
    "order",
    "订单",
    "payment",
    "支付",
    "timeout",
    "超时",
    "retry",
    "重试",
]

GIT_RELEVANT_KEYWORDS = [
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

RISK_WEIGHT = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def search_mock_logs(
    query: str,
    context: str = "",
    log_file: Path = LOG_FILE,
    source: str = LOG_SOURCE,
) -> dict[str, Any]:
    started_at = perf_counter()

    if not log_file.exists():
        return _failed_response(source, "file_not_found", started_at)

    query_text = f"{query} {context}".lower()
    matched_keywords = [
        keyword
        for keyword in LOG_MATCH_KEYWORDS
        if re.search(re.escape(keyword.lower()), query_text)
    ]

    lines = log_file.read_text(encoding="utf-8").splitlines()
    if matched_keywords:
        relevant_lines = [
            line
            for line in lines
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

    return _success_response(
        data=summary + "\n" + "\n".join(relevant_lines[:5]),
        source=source,
        confidence=confidence,
        started_at=started_at,
        metadata={
            "matched_keywords": matched_keywords,
            "matched_count": len(relevant_lines),
            "platform": "mock_log_platform",
        },
    )


def compare_mock_configs(
    query: str,
    context: str = "",
    dev_config_file: Path = DEV_CONFIG_FILE,
    prod_config_file: Path = PROD_CONFIG_FILE,
    source: str = CONFIG_SOURCE,
) -> dict[str, Any]:
    started_at = perf_counter()

    if not dev_config_file.exists() or not prod_config_file.exists():
        return _failed_response(source, "file_not_found", started_at)

    dev_config = json.loads(dev_config_file.read_text(encoding="utf-8"))
    prod_config = json.loads(prod_config_file.read_text(encoding="utf-8"))

    dev_flat = _flatten(dev_config)
    prod_flat = _flatten(prod_config)
    query_text = f"{query} {context}".lower()

    diff_lines: list[str] = []
    diffs: list[dict[str, Any]] = []
    for key in sorted(set(dev_flat) | set(prod_flat)):
        if dev_flat.get(key) == prod_flat.get(key):
            continue
        if not _is_config_relevant(key, query_text):
            continue
        dev_value = dev_flat.get(key)
        prod_value = prod_flat.get(key)
        diff_lines.append(f"{key}: dev={dev_value!r}, prod={prod_value!r}")
        diffs.append({"key": key, "dev": dev_value, "prod": prod_value})

    if diff_lines:
        data = "发现订单/支付相关配置差异：\n" + "\n".join(diff_lines)
        confidence = 0.85
    else:
        data = "未发现订单、支付、timeout 或 retry 相关配置差异。"
        confidence = 0.6

    return _success_response(
        data=data,
        source=source,
        confidence=confidence,
        started_at=started_at,
        metadata={
            "diff_count": len(diffs),
            "diffs": diffs,
            "platform": "mock_config_center",
        },
    )


def search_mock_commits(
    query: str,
    context: str = "",
    git_file: Path = GIT_FILE,
    source: str = GIT_SOURCE,
) -> dict[str, Any]:
    started_at = perf_counter()

    if not git_file.exists():
        return _failed_response(source, "file_not_found", started_at)

    commits = json.loads(git_file.read_text(encoding="utf-8"))
    query_text = f"{query} {context}".lower()

    ranked_commits = []
    for index, commit in enumerate(commits):
        searchable = _searchable_commit_text(commit)
        relevance = _git_relevance_score(searchable, query_text)
        if relevance <= 0:
            continue
        risk_score = RISK_WEIGHT.get(str(commit.get("risk_level", "")).lower(), 0)
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

    return _success_response(
        data=data,
        source=source,
        confidence=confidence,
        started_at=started_at,
        metadata={
            "commit_count": len(selected),
            "commits": selected,
            "platform": "mock_git_platform",
        },
    )


def _success_response(
    *,
    data: str,
    source: str,
    confidence: float,
    started_at: float,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "success",
        "data": data,
        "source": source,
        "confidence": confidence,
        "error": None,
        "latency_ms": (perf_counter() - started_at) * 1000,
        "metadata": metadata,
    }


def _failed_response(source: str, error: str, started_at: float) -> dict[str, Any]:
    return {
        "status": "failed",
        "data": "",
        "source": source,
        "confidence": 0.0,
        "error": error,
        "latency_ms": (perf_counter() - started_at) * 1000,
        "metadata": {},
    }


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten(value, path))
        else:
            flattened[path] = value
    return flattened


def _is_config_relevant(key: str, query_text: str) -> bool:
    key_text = key.lower()
    if any(keyword in key_text for keyword in ["order", "payment", "timeout", "retry"]):
        return True
    return any(
        re.search(re.escape(keyword.lower()), query_text)
        for keyword in CONFIG_RELEVANT_KEYWORDS
    )


def _searchable_commit_text(commit: dict[str, Any]) -> str:
    values = [
        str(commit.get("commit_id", "")),
        str(commit.get("message", "")),
        str(commit.get("risk_level", "")),
        str(commit.get("summary", "")),
        " ".join(commit.get("changed_files", [])),
    ]
    return " ".join(values).lower()


def _git_relevance_score(searchable: str, query_text: str) -> int:
    score = 0
    for keyword in GIT_RELEVANT_KEYWORDS:
        keyword_lower = keyword.lower()
        if not re.search(re.escape(keyword_lower), searchable):
            continue
        score += 2 if re.search(re.escape(keyword_lower), query_text) else 1
    return score
