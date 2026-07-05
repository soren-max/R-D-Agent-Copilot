# 02 Context Manager Mapping

本篇记录 Pico Context Manager 思路如何迁移到 R&D Agent Copilot。

## Pico Context Manager 解决什么问题

Pico 作为 Coding Harness，需要把任务描述、仓库文件、工具结果、运行历史和模型约束组织成模型可消费的上下文。这个过程不能只是简单字符串拼接，因为 coding loop 会不断产生新的观察结果、工具输出和历史记录。

Pico Context Manager 主要解决这些问题：

- 分层：区分 system、task、workspace、tool result、memory、trace 等不同信息来源。
- 预算：控制上下文长度，避免无边界地把历史和工具输出塞进模型。
- 保真：关键输入不能被错误裁剪，例如当前用户任务和安全边界。
- 可回看：记录哪些 section 被压缩，压缩前后字符数是多少。
- 可演进：后续可以替换压缩策略，而不需要重写 Agent 主循环。

## 本项目为什么需要 Context Manager

R&D Agent Copilot 当前面向研发排障场景，工具结果和 RAG evidence 很容易变长：

- 日志工具可能返回大量 ERROR/WARN/堆栈片段。
- 配置工具可能返回多环境 diff。
- Git 工具可能返回多条提交记录。
- RAG 可能返回多个知识库 chunk、source、score 和 grounding evidence。
- Trace 和历史 run 会随着链路变长而膨胀。

如果把这些内容直接堆给 Answer Synthesizer，会带来几个问题：

- prompt 结构不稳定，后续难以调试。
- 长日志和历史信息挤占 RAG evidence 或当前 query。
- 前端 Trace Viewer 无法知道上下文是否被压缩。
- 面试讲解时很难说明 Agent Harness 的上下文边界。

因此本项目需要 Context Manager，把最终回答阶段的输入组织为分层 `ContextPackage`，并输出 `ContextMetadata` 供 trace 回看。

## Section 映射表

| Pico Section | Pico 含义 | 本项目 Section | 本项目含义 | 裁剪策略 |
| --- | --- | --- | --- | --- |
| system | Agent 角色、安全边界、输出规则 | `system_prefix` | Answer Synthesizer 的系统约束 | 最后裁剪 |
| task | 当前用户任务 | `current_query` | 用户原始问题 | 永不裁剪 |
| plan | 当前执行意图和步骤 | `route_plan` | Router 输出和 Planner steps | 倒数第二裁剪 |
| tool results | 工具观察结果 | `tool_evidence` | log/config/git 工具证据 | 第三裁剪 |
| knowledge | 检索知识和引用来源 | `rag_evidence` | RAG documents、source、title、grounding evidence | 第二裁剪 |
| memory/history | 历史状态和运行记录 | `run_history` | 当前 run 的 trace summary | 第一裁剪 |
| metadata | 上下文构建信息 | `ContextMetadata` | 字符数、压缩率、被压缩 section | 不进入 prompt 主体裁剪 |

默认裁剪顺序：

```text
run_history
-> rag_evidence
-> tool_evidence
-> route_plan
-> system_prefix
```

`current_query` 不进入裁剪流程。

当 `current_query` 极长时，`ContextPackage.metadata.total_chars_after` 可能超过 `total_budget`。这是 v1 的明确取舍：用户原始问题的完整性优先于总字符预算，其他 section 会按顺序尽量压缩。

RAG evidence 的 metadata 优先级高于正文。`source`、`title`、`score`、`chunk_id`、`doc_id` 等字段应优先保留；长正文只进入 `content_summary`，二次压缩也优先压缩正文摘要，而不是整体截断导致引用来源丢失。

## 本次 PR 边界

本次只实现 Context Manager v1：

- 新增 `apps/api/app/context/` 小模块。
- 定义 `ContextSection`、`ContextPackage` 和 `ContextMetadata`。
- 定义 deterministic reducers，不调用 LLM。
- 在 Answer Synthesizer 调用前构建 `ContextPackage`。
- 将 `ContextMetadata` 写入 synthesizer trace step。
- `current_query` 不参与裁剪；`total_budget` 在极长 query 场景下允许被突破。
- RAG evidence 优先保留 `source/title/score/chunk_id/doc_id` 等 metadata，再压缩正文摘要。
- 保持 Router、Planner、Executor、Tools、RAG、Trace、Evaluation 主流程不重写。
- 保持默认 `LLM_ENABLED=false` 的 fallback 能力。

本次不做：

- 不让 LLM 参与 Router、Planner 或 Tool Selection。
- 不接真实日志平台、配置中心或 Git API。
- 不引入数据库、Redis 或新依赖。
- 不新增前端 Trace Viewer 展示，只为后续展示提供 metadata。

## 后续 TODO

- Tool Gateway：统一工具白名单、参数校验、权限和审计字段。
- Incident Memory：沉淀历史故障、根因候选、证据链和处理建议。
- Checkpoint Resume：支持较长 run 的中断恢复。
- Evaluation v2：加入 evidence coverage、tool usefulness、latency budget 和 bad case replay。
- Trace Viewer：展示 `ContextMetadata`、section 字符数和压缩状态。

## 面试讲解话术

我把 Pico 的 Context Manager 思路迁移到了研发排障 Agent。Pico 解决的是 Coding Agent 中任务、代码、工具结果和历史如何进入模型的问题；我的项目里对应的是用户故障问题、Router/Planner 输出、log/config/git 工具证据、RAG evidence 和 trace history。

这次没有改 Router、Planner 或工具选择链路，而是在 Answer Synthesizer 前新增一个 `ContextPackage` 层。它把上下文拆成 `system_prefix`、`current_query`、`route_plan`、`tool_evidence`、`rag_evidence` 和 `run_history`，其中用户原始问题永不裁剪，长日志、RAG 和历史按预算压缩，并把压缩 metadata 写入 trace。这样既保留默认 fallback 能力，也让最终回答的上下文组织更可控、可测试、可回看。
