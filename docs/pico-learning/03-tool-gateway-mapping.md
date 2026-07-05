# 03 Tool Gateway Mapping

本篇记录 Pico 工具边界如何迁移到 R&D Agent Copilot。

## Pico 工具边界解决什么问题

Pico 作为 Coding Harness，不能让模型直接操作执行环境。工具边界需要统一处理：

- 工具是否存在、是否允许调用。
- 参数是否完整、是否符合安全策略。
- 重复调用是否需要拦截或标记。
- 工具执行失败时如何标准化错误。
- 工具结果如何进入 trace，方便回看和评估。

核心目标是把“模型想做什么”和“系统实际允许执行什么”隔离开。

## 本项目为什么需要 Tool Gateway

R&D Agent Copilot 当前工具包括 `log_tool`、`config_tool`、`git_tool` 和 `rag_retriever`。这些工具都只读取本地确定性样例或本地知识库，但仍需要统一边界：

- Executor 不应该直接依赖每个工具的返回细节。
- Trace Viewer 后续需要统一的工具状态、错误码和摘要。
- Evaluation 和 Evidence Chain 需要稳定的工具调用元数据。
- 未来接入真实工具前，应先把本地工具边界收口。

Tool Gateway v1 不改变 Router、Planner、Executor 或 LangGraph 主流程，只在工具实际执行前后增加确定性校验和标准化包装。

## 工具调用链路图

```text
Planner steps
-> LangGraph Executor node
-> ToolGateway
   -> registry check
   -> parameter validation
   -> duplicate call check
   -> policy check
   -> real local tool execution
   -> StandardToolResult
-> ToolCallRecord
-> Trace metadata
-> Answer Synthesizer / Evaluation / Evidence Chain
```

`StandardToolResult` 统一包含：

- `tool_name`
- `status`: `success` / `error` / `partial_success` / `blocked`
- `latency_ms`
- `input_hash`
- `evidence_count`
- `safe_summary`
- `error_code`
- `metadata`

为了保持兼容，`error` 和 `blocked` 在旧 `ToolCallRecord.status` 中仍映射为 `failed`，避免破坏现有 fallback、Evaluation 和 Evidence Chain 逻辑。

## 面试话术

我在工具执行边界加了 Tool Gateway，但没有让 LLM 参与工具选择。Router 和 Planner 仍然决定任务分类和计划，LangGraph Executor 仍然按计划执行节点；Tool Gateway 只负责在真实工具调用前后做注册校验、参数校验、重复调用检查、策略检查和标准化结果包装。

这样做的好处是，当前本地 log/config/git/RAG 工具能力完全不变，但 trace 里可以统一看到 tool status、latency、input hash、error code 和 evidence count。它为以后接真实工具 API 打下边界基础，同时保持默认 `LLM_ENABLED=false` 的 demo 能力可运行。
