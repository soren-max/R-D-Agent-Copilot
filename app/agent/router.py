"""
意图路由器 — 用户输入分类。

职责边界：
- 只做意图分类（simple_qa / complex_troubleshooting）
- 纯规则驱动，不接 LLM
"""

from __future__ import annotations

import re
from typing import Final

from app.core.models import RouterResult

_TROUBLESHOOTING_KEYWORDS: Final[list[tuple[str, float]]] = [
    ("报错", 3.0), ("异常", 2.5), ("错误", 2.0), ("失败", 2.0),
    ("超时", 2.5), ("崩溃", 3.0), ("挂掉", 3.0), ("挂", 1.5),
    ("error", 3.0), ("exception", 3.0), ("crash", 3.0),
    ("timeout", 2.5), ("oom", 3.0),
    ("500", 2.5), ("502", 2.5), ("503", 2.5),
    ("排查", 2.5), ("查一下", 1.5), ("检查", 1.5), ("分析", 1.5),
    ("怎么回事", 2.0), ("什么原因", 2.0), ("为什么", 1.5),
    ("根因", 2.5), ("原因", 1.0), ("debug", 2.0), ("investigate", 2.0),
    ("不生效", 2.5), ("没生效", 2.5), ("变慢", 2.5), ("卡住", 2.5),
    ("不能用", 2.0), ("打不开", 2.0), ("连不上", 2.5), ("跑不动", 2.5),
    ("slow", 2.0), ("broken", 2.5), ("leak", 2.5), ("corrupt", 2.5),
    ("配置", 1.0), ("回滚", 2.0), ("升级后", 2.0), ("变更", 2.0), ("commit", 2.0), ("git", 2.0),
    ("部署", 2.5), ("发布", 2.0), ("启动失败", 3.0), ("起不来", 3.0),
    ("端口", 2.0), ("health check", 2.5), ("port already in use", 3.0),
    ("注入", 2.5), ("越权", 2.5), ("泄露", 2.5), ("删除数据", 3.0), ("删库", 3.0),
    ("绕过", 2.5), ("密钥", 2.5), ("prompt injection", 3.0),
]

_QA_DEFINITION_PATTERNS: Final[list[str]] = [
    r"什么是.{,30}", r".{0,30}是什么意思", r"能解释一下.{,30}",
    r"解释一下.{,30}", r".{0,10}指的是什么", r".{0,10}是指什么",
    r"什么叫.{,30}", r".{0,10}怎么理解",
]

_QA_PROCEDURAL_PATTERNS: Final[list[str]] = [
    r"在哪里.{,30}", r"从哪里.{,30}",
    r"怎么查(?!排).{,30}", r"怎么查一下.{,30}",
    r"怎么查看.{,30}", r"怎样查看.{,30}",
    r"怎么找到.{,30}", r"在哪儿.{,30}",
    r"怎样排查.{,30}", r"怎么排查.{,30}",
]

_TROUBLESHOOTING_THRESHOLD: Final[float] = 2.0
_MAX_CONFIDENCE: Final[float] = 0.95


class IntentRouter:
    """用户输入 → deterministic 意图分类。

    ``llm_provider`` is accepted only as a deprecated compatibility argument.
    Router must never call an LLM, even when ``LLM_ENABLED=true``.
    """

    def __init__(self, llm_provider: object | None = None) -> None:
        self.legacy_llm_provider_ignored = llm_provider is not None

    def route(self, message: str) -> RouterResult:
        return self._route_rule_based(message)

    def _route_rule_based(self, message: str) -> RouterResult:
        text_lower = message.lower().strip()
        if not text_lower:
            return RouterResult(type="simple_qa", intent="knowledge_qa", confidence=0.0, reason="输入为空，默认分类为简单问答。")

        # Layer 1: QA 定义模式
        for pattern in _QA_DEFINITION_PATTERNS:
            m = re.search(pattern, text_lower)
            if m:
                return RouterResult(
                    type="simple_qa", intent="knowledge_qa", confidence=0.75,
                    reason=f"检测到定义类问句模式「{m.group().strip()}」，判定为简单问答。",
                )

        # Layer 2: QA 程序模式
        for pattern in _QA_PROCEDURAL_PATTERNS:
            m = re.search(pattern, text_lower)
            if m:
                return RouterResult(
                    type="simple_qa", intent="knowledge_qa", confidence=0.70,
                    reason=f"检测到程序类问句模式「{m.group().strip()}」，判定为简单问答。",
                )

        # Layer 3: 排障关键词评分
        matched_trouble: list[str] = []
        trouble_score = 0.0
        for keyword, weight in _TROUBLESHOOTING_KEYWORDS:
            count = len(re.findall(re.escape(keyword), text_lower, re.IGNORECASE))
            if count > 0:
                matched_trouble.append(keyword)
                trouble_score += weight * count

        if trouble_score >= _TROUBLESHOOTING_THRESHOLD:
            raw_conf = min(trouble_score / (_TROUBLESHOOTING_THRESHOLD * 2), 1.0)
            confidence = round(min(raw_conf, _MAX_CONFIDENCE), 2)
            matched_str = "、".join(matched_trouble[:8])
            if len(matched_trouble) > 8:
                matched_str += f" 等 {len(matched_trouble)} 个关键词"
            return RouterResult(
                type="complex_troubleshooting", intent=_infer_troubleshooting_intent(text_lower), confidence=confidence,
                reason=f"检测到排障关键词 [{matched_str}]，判定为复杂排障问题。",
            )

        # Fallback: simple_qa
        return RouterResult(type="simple_qa", intent="knowledge_qa", confidence=0.40, reason="未检测到排障关键词，默认判定为简单问答。")


def _infer_troubleshooting_intent(text_lower: str) -> str:
    if any(keyword in text_lower for keyword in ["注入", "越权", "泄露", "删库", "删除数据", "绕过", "prompt injection"]):
        return "safety_risk"
    if any(keyword in text_lower for keyword in ["配置", "config", "不生效", "没生效"]):
        return "config_diff"
    if any(keyword in text_lower for keyword in ["git", "commit", "提交", "代码", "变更"]) and "日志" not in text_lower:
        return "git_change"
    if any(keyword in text_lower for keyword in ["日志", "error", "exception", "异常", "报错", "500", "502", "503", "oom", "崩溃", "timeout"]):
        return "log_analysis"
    if any(keyword in text_lower for keyword in ["部署", "发布", "启动失败", "起不来", "端口", "health check", "port already in use", "上线", "readiness"]):
        return "deployment_issue"
    return "log_analysis"
