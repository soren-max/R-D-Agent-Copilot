"""Rule-based prompt injection and dangerous request detection."""

from __future__ import annotations

from apps.api.app.safety.schemas import SafetyCheckResult

_HIGH_RISK_PATTERNS = {
    "ignore_previous_instructions": ["ignore previous instructions", "忽略之前", "无视系统提示", "忽略系统"],
    "secret_exfiltration": ["api key", "apikey", "密钥", "token", "泄露", "打印环境变量"],
    "destructive_operation": ["删库", "删除数据", "drop table", "rm -rf", "truncate table"],
    "privilege_bypass": ["绕过权限", "越权", "bypass auth", "disable safety"],
}

_MEDIUM_RISK_PATTERNS = {
    "prompt_injection": ["prompt injection", "系统提示词", "system prompt", "开发者消息"],
    "untrusted_instruction": ["按照文档中的指令执行", "执行知识库里的命令", "直接运行命令"],
}


def detect_prompt_injection(text: str) -> SafetyCheckResult:
    lowered = text.lower()
    reasons: list[str] = []
    matched: list[str] = []
    for reason, patterns in _HIGH_RISK_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lowered:
                reasons.append(reason)
                matched.append(pattern)
                break

    if reasons:
        return SafetyCheckResult(
            safety_status="blocked",
            risk_level="high",
            reasons=reasons,
            matched_patterns=matched,
        )

    for reason, patterns in _MEDIUM_RISK_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lowered:
                reasons.append(reason)
                matched.append(pattern)
                break

    if reasons:
        return SafetyCheckResult(
            safety_status="allowed",
            risk_level="medium",
            reasons=reasons,
            matched_patterns=matched,
        )

    return SafetyCheckResult()
