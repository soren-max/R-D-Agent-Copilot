# Safety Boundary

This project uses deterministic safety checks before tool execution. The checks are local rule-based guards and do not call LLMs or external services.

## Tool Allowlist

Only these tools are allowed:

- `log_tool`
- `config_tool`
- `git_tool`
- `rag_retriever`

Unknown tools are rejected with:

- `blocked=true`
- `reason="unknown_tool"`
- `tool_name=<requested tool>`

## Prompt Injection Guard

The guard checks user input and tool queries for high-risk instruction patterns, including:

- `ignore previous instructions`
- `忽略之前的规则`
- `泄露系统提示词`
- `输出 API Key`
- `绕过工具限制`
- `删除日志`
- `修改生产配置`

Matched input is rejected with `reason="prompt_injection_risk"`.

## Schema Validation

Tool input is normalized before deterministic execution:

- `tool_name` must be non-empty
- `tool_name` must be in the allowlist
- `query` must be a string
- dangerous `action` values are rejected

The guard does not generate answers and does not modify Planner output.

## Blocked Trace

Safety blocks are recorded in trace as a `safety` stage with:

- `blocked`
- `blocked_reason`
- `input_summary`
- legacy fields such as `safety_status`, `safety_risk_level`, and `safety_reasons`

The input summary is shortened for debugging and demo replay.

## Current Limits

The guard is intentionally simple. It catches known high-risk phrases and invalid tool inputs, but it is not a full policy engine. It does not inspect arbitrary code, does not execute sandboxing, and does not replace authentication or authorization in a real platform.

For production integration, keep the same adapter boundary and add server-side authorization, endpoint-level allowlists, audit logs, and read-only credentials.
