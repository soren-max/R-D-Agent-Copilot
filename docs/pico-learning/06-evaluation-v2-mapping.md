# 06 Evaluation v2 Mapping

本篇记录 Pico 的评测思想如何迁移到 R&D Agent Copilot。

## Pico 为什么不能只看一个 pass rate

Agent Harness 的质量不能只用一个 pass rate 说明。一个任务失败可能是上下文丢失、工具失败、RAG 无来源、memory 过期、resume 重复执行，也可能只是最终表达不够好。单一总分无法告诉工程师应该修哪里。

因此 Pico 类系统更需要可解释指标：每个模块单独看，最后再聚合。

## 本项目为什么拆指标

R&D Agent Copilot 已经有 Context Manager、Tool Gateway、RAG、Incident Memory、Checkpoint / Resume 和 Evidence Chain。Evaluation v2 按模块拆分：

- Context：上下文是否被正确压缩，用户原始问题是否保留。
- Tool：工具是否成功、是否 blocked、是否 partial success、延迟如何。
- RAG：检索命中数量、来源覆盖、是否缺 source/title。
- Memory：历史 memory 是否 fresh/weak/stale，是否被错误当成当前事实。
- Resume：checkpoint 是否创建、resume 是否成功、是否重复执行 step。
- Evidence：证据链是否完整，根因和修复建议是否有证据支撑。
- Provider：LLM/fallback/provider 错误和耗时。

## 每类指标解释

| 模块 | 关注点 |
| --- | --- |
| Context | `prompt_chars_before`、`prompt_chars_after`、`compression_ratio`、`current_query_preserved` |
| Tool | `tool_success_rate`、`tool_error_count`、`tool_blocked_count`、`partial_success_count` |
| RAG | `rag_hit_count`、`source_coverage`、`missing_source_count`、`grounding_score` |
| Memory | `memory_hit_count`、`fresh_memory_count`、`weak_memory_count`、`stale_memory_count`、misuse risk |
| Resume | `checkpoint_created`、`resume_success`、`duplicated_step_count` |
| Evidence | `evidence_chain_complete`、`evidence_refs_count`、`root_cause_supported` |
| Provider | `llm_enabled`、`fallback_used`、`provider_error_count` |

## v1 为什么先用规则评测

Evaluation v2 先用规则，不用 LLM 自评作为唯一评分来源：

- 默认 `LLM_ENABLED=false` 必须可运行。
- 规则指标更稳定，适合 CI 和回归测试。
- 评测结果可解释，方便定位模块问题。
- 后续可以引入 LLM judge，但只能作为补充，不应替代 trace/evidence 规则指标。

## 30 秒面试话术

我把 Evaluation 从一个总分升级成了按模块拆分的可解释指标。它分别评估 Context、Tool、RAG、Memory、Resume、Evidence 和 Provider，每类指标都来自 trace、context metadata、tool metadata、checkpoint 和 evidence chain，而不是让 LLM 自己打分。这样失败时可以直接定位是上下文压缩、工具调用、RAG 来源、历史记忆、恢复执行还是证据链的问题。

## 1 分钟面试话术

Pico 这类 Agent Harness 不能只看 pass rate，因为 pass rate 不告诉你系统哪里坏了。我在 R&D Agent Copilot 里做了 Evaluation v2，把评测拆成 Context、Tool、RAG、Memory、Resume、Evidence 和 Provider 七个模块。

Context 看 prompt 压缩和 current query 是否保留；Tool 看 Tool Gateway 状态、错误、blocked 和延迟；RAG 看命中数、source/title 覆盖和 grounding；Memory 看 fresh/weak/stale，以及是否把历史根因误当当前事实；Resume 看 checkpoint 和重复执行；Evidence 看根因和修复建议是否有证据支撑。所有指标都从已有 artifact 聚合，不接外部评测服务，也不让 LLM 自评成为唯一依据。
