"""Rule-based safety policy constants.

These policies are deterministic and local-only. They do not call LLMs or
external services, and they do not decide Router or Planner outputs.
"""

from __future__ import annotations

TOOL_ALLOWLIST = frozenset({"log_tool", "config_tool", "git_tool", "rag_retriever"})

PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "忽略之前的规则",
    "泄露系统提示词",
    "输出 api key",
    "绕过工具限制",
    "删除日志",
    "修改生产配置",
)

DANGEROUS_ACTION_PATTERNS = (
    "delete_logs",
    "drop_logs",
    "remove_logs",
    "delete_production_config",
    "modify_production_config",
    "write_production_config",
    "删除日志",
    "修改生产配置",
    "删除生产配置",
)
