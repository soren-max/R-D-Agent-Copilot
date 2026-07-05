# 04 Incident Memory Mapping

本篇记录 Pico 的结构化记忆思路如何迁移到 R&D Agent Copilot。

## Pico 结构化记忆解决什么问题

Pico 这类 Agent Harness 不能只依赖当前 prompt。长期运行后，系统需要把已经验证过的经验沉淀下来，供后续相似任务参考：

- 过去遇到过什么问题。
- 当时有哪些证据。
- 最终判断的根因是什么。
- 采取了什么修复动作。
- 这条记忆来自哪个 run，是否仍然可信。

结构化记忆的重点不是“把历史对话全塞回模型”，而是把可复用经验压缩成可检索、可追踪、可降权的事实片段。

## 本项目为什么需要 Incident Memory

R&D Agent Copilot 面向研发排障场景。很多故障会重复出现，例如同一个服务的 500、timeout、配置差异或最近代码变更。Incident Memory v1 用来沉淀历史排障结果：

- `service`
- `symptom`
- `root_cause`
- `fix`
- `confidence`
- `source_run_id`
- `evidence_refs`

后续相似问题进入 Context Manager 时，系统会通过规则召回最多 3 条相关历史 memory，放入 `incident_memory` section。它只作为“历史参考”，不替代当前 `tool_evidence` 或 `rag_evidence`。

## Memory、History、Prompt Cache 的区别

| 类型 | 内容 | 生命周期 | 是否可作为当前证据 |
| --- | --- | --- | --- |
| History | 当前 run 或会话过程中的消息、工具输出、trace | 短期 | 否，只是运行过程 |
| Prompt Cache | 为节省构造成本或 token 成本缓存的 prompt 片段 | 工程优化 | 否，只是缓存 |
| Incident Memory | 历史排障结论、证据引用、修复动作和置信度 | 跨 run | 否，只是历史参考 |

Incident Memory 和 RAG 也不同。RAG 是知识库文档检索，Incident Memory 是历史排障经验检索。二者都不能绕过当前工具证据。

## Freshness 为什么重要

历史 memory 不能无条件当成当前事实。服务配置、代码和运行环境都会变化，所以每条 memory 都要带 freshness：

- `fresh`：有 `source_run_id`、`created_at`、`evidence_refs`，且未超过默认 TTL。
- `weak`：缺少来源 run、创建时间或证据引用。
- `stale`：超过默认 TTL，例如 30 天。

`weak` 和 `stale` 仍可以返回，但必须作为低可信历史参考展示。Answer Synthesizer 不能在当前工具/RAG 不支持时，直接把 memory 的 root cause 当作本次最终根因。

## v1 为什么不用向量数据库

Incident Memory v1 只做规则召回：

- service 精确匹配优先。
- 再基于 symptom/query 关键词匹配。
- 最多返回 3 条。
- 每条结果带 `match_reason` 和 `freshness_status`。

当前不引入 Milvus、FAISS、pgvector 或其他向量数据库，原因是：

- v1 目标是建立记忆边界，而不是优化召回算法。
- 本项目仍是 backend MVP，默认 demo 必须本地可运行。
- 规则召回更容易测试、解释和面试讲解。
- 未来要换向量检索时，可以在 retrieval 层替换，不需要改 Router、Planner、Executor。

## 30 秒面试话术

我给排障 Agent 加了 Incident Memory，但没有把历史对话直接塞进 prompt。每次排障完成后，系统把 service、symptom、root cause、fix、confidence、source run 和 evidence refs 写成结构化 memory。下一次相似问题进来时，Context Manager 会用规则召回最多 3 条历史 memory，作为 `incident_memory` section 放进上下文。它只作为历史参考，不替代当前工具证据或 RAG 证据，并且每条 memory 都会标记 fresh、weak 或 stale，避免把过期历史当成当前事实。

## 1 分钟面试话术

Pico 的结构化记忆解决的是 Agent 如何跨任务复用经验的问题。我把这个思路迁移到 R&D Agent Copilot 里，做成 Incident Memory v1。它不引入向量数据库，也不让 LLM 判断 memory 是否可信，而是用 JSON 文件和规则检索实现一个可测试的最小版本。

排障完成后，系统在 Evaluation 和 Evidence Chain 之后，把最终回答和证据链整理成结构化 memory，包括服务、故障现象、根因、修复建议、置信度、来源 run 和证据引用。后续相似问题进入 Context Manager 时，系统先按 service 精确匹配，再按 symptom/query 关键词匹配，最多召回 3 条，并带上 match reason 和 freshness status。

关键边界是：Incident Memory 只是历史参考，不是当前证据。Answer Synthesizer 不能在当前 tool evidence 或 RAG evidence 不支持时，直接把历史 root cause 当作本次最终根因。这样既能复用历史经验，又保持排障结论受当前证据约束。
