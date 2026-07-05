# 07 Prompt / Provider Governance Mapping

## 为什么需要 prompt_version

Pico Agent Harness 会把 prompt 当成可演进的工程资产，而不是临时字符串。R&D Agent Copilot 的 Answer Synthesizer 也需要同样治理：每次最终报告生成都记录 `prompt_version`，方便回看某次 run 使用了哪版约束、输出 schema 和 fallback 策略。

本项目当前版本为 `answer_synthesizer_v1`。

## 为什么 DeepSeek 只放在 Answer Synthesizer

本项目链路仍然是：

```text
User Query -> Router -> Planner -> Executor -> Tools/RAG -> Trace -> Answer Synthesizer
```

DeepSeek / OpenAI-compatible provider 只允许在最终 Answer Synthesizer 中使用。它不能参与 Router、Planner、工具选择、Incident Memory freshness 判断或 Checkpoint Resume 决策。这样可以保证工具执行链路仍由确定性工程逻辑控制，LLM 只负责把已有证据组织成中文报告。

## 为什么最终报告要固定 JSON schema

最终报告固定为：

```json
{
  "summary": "中文摘要",
  "root_cause": "基于当前证据的根因判断；证据不足时写不确定",
  "evidence": ["仅列出 tool_evidence 或 rag_evidence 支撑的证据"],
  "fix_steps": ["可执行的排障或修复建议"],
  "confidence": 0.0,
  "risks": ["不确定性、工具失败、历史参考限制等风险"]
}
```

固定 schema 的价值是让 trace、evaluation、历史 run 和后续前端展示都能稳定消费最终报告，而不是解析自由文本。

## Fallback 对演示和测试的意义

默认 `LLM_ENABLED=false` 时，系统使用 rule-based fallback 生成同一 schema 的报告，不需要真实 API Key，也不会因为 provider 不可用导致主流程失败。

当 provider 报错时，fallback 会接管，并在 trace 中记录：

- `fallback_used=true`
- `provider_error_code`
- `provider_error_message`
- `schema_valid=true`，表示最终 fallback 报告满足 schema

当 provider 返回非法 JSON 时，系统会标记 `schema_valid=false`，并规则解析或降级生成 schema-compatible 的 `parsed_output`，方便后续定位 prompt 或 provider 问题。

## Provider metadata 如何进入 trace / evaluation

Answer Synthesizer 结束后会写入 `TraceStep.provider_metadata`：

- `prompt_version`
- `model_provider`
- `model_name`
- `llm_enabled`
- `fallback_used`
- `schema_valid`
- `generation_latency_ms`
- `provider_error_code`
- `provider_error_message`

Evaluation v2 的 provider metrics 会优先读取这份 metadata，并聚合出 provider 可用性、fallback、schema 校验和错误计数。

## 30 秒面试话术

我把最终 Answer Synthesizer 做成了可治理模块：prompt 有版本，provider 调用有 metadata，最终报告固定 JSON schema。DeepSeek 只在最终报告生成阶段使用，不参与路由、规划和工具选择。默认 `LLM_ENABLED=false` 仍然走规则 fallback，所以演示和测试不依赖真实 API Key。

## 1 分钟面试话术

这个项目的 LLM 边界很清楚：Router、Planner、Executor、Tools、RAG 都是工程可控逻辑，LLM 只负责基于已有证据合成最终中文排障报告。我给 Answer Synthesizer 增加了 `answer_synthesizer_v1` prompt version、固定 final report JSON schema、schema validation 和 provider metadata。LLM 输出非法 JSON 会被标记 `schema_valid=false` 并降级解析；provider 异常或未启用时会使用 rule-based fallback，fallback 输出也满足同一个 schema。所有 provider metadata 会进入 trace，并被 Evaluation v2 聚合成可解释指标。
