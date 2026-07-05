# 05 Checkpoint Resume Mapping

本篇记录 Pico 的 checkpoint / resume 思路如何迁移到 R&D Agent Copilot。

## Pico 为什么区分 session 和 run artifact

Pico 这类 Agent Harness 通常会区分 session 和 run artifact：

- Session 更像交互上下文，记录用户正在进行的任务和短期状态。
- Run artifact 是一次执行的可恢复产物，记录输入、计划、已完成步骤、工具证据、错误和输出。

这个区分很重要。恢复任务时，系统不应该把完整历史聊天重新塞回 prompt，也不应该让 LLM 猜应该从哪里继续。恢复点应该来自结构化 run artifact。

## 本项目为什么需要 Checkpoint / Resume

R&D Agent Copilot 当前已经能回看 trace，但 trace 主要用于观察，不等同于可恢复状态。Checkpoint / Resume v1 的目标是把 run 从“只能回看”升级为“可以继续”：

- run 开始时保存初始 checkpoint。
- Router / Planner 后保存 route 和 plan。
- 工具执行后保存 completed steps 和 pending steps。
- Answer Synthesizer 前保存 evidence summary 和 context metadata。
- 成功后标记 completed。
- 失败或中断时保留 last error，并允许后续从 pending steps 继续。

## Checkpoint 字段解释

| 字段 | 含义 |
| --- | --- |
| `run_id` | 当前 run 的 trace id，也是 checkpoint 主键 |
| `query` | 原始用户问题 |
| `route` | Router 输出 |
| `plan` | Planner 输出 |
| `completed_steps` | 已完成的 plan step id |
| `pending_steps` | 尚未执行或需要继续执行的 step id |
| `tool_evidence_summary` | 已有非 RAG 工具证据摘要 |
| `rag_evidence_summary` | 已有 RAG 证据摘要 |
| `context_metadata` | Context Manager 构建时的 metadata |
| `last_error` | 最近一次失败或中断原因 |
| `status` | `running` / `resumable` / `completed` / `failed` |
| `created_at` | 创建时间 |
| `updated_at` | 最近更新时间 |

## 三个接口区别

### GET `/runs/{run_id}/checkpoint`

只读取 checkpoint，用于查看一个 run 是否有可恢复状态。

### POST `/runs/{run_id}/continue`

基于指定 run 的 checkpoint 继续执行。v1 会读取 pending steps，并构造子计划交给现有 Executor。已完成 steps 不重复执行。

### POST `/chat/resume`

继续最近一个 `resumable` checkpoint。它适合 demo 和命令式恢复，但 v1 不做复杂多用户 session 管理。

## v1 不做复杂 workspace drift 的原因

本项目是研发排障 Agent，不是代码编辑 Agent。v1 不需要比较 workspace diff，也不需要恢复复杂文件状态。当前只做规则 drift 检查：

- 缺少 `run_id` / `query` / `plan`：`not_resumable`
- `pending_steps` 为空：`already_completed`
- checkpoint 超过默认 30 天：`stale_checkpoint`

这能先建立可恢复状态边界，后续如果需要真实生产环境恢复，再扩展 drift 检查。

## 30 秒面试话术

我把 trace 从“只能回看”升级成了 checkpoint。每次 run 会保存 query、route、plan、已完成 steps、待执行 steps、证据摘要和 context metadata。恢复时系统不让 LLM 判断从哪里继续，而是读取 checkpoint，构造 pending steps 子计划，再交给现有 Executor 执行，避免重复执行已完成工具。

## 1 分钟面试话术

Pico 里 session 和 run artifact 是分开的：session 是交互状态，run artifact 才是可恢复执行状态。我把这个思路迁移到 R&D Agent Copilot，做了 Checkpoint / Resume v1。

在 pipeline 中，run 开始会创建 checkpoint，Planner 后保存 route 和 plan，Executor 后保存 completed 和 pending steps，Synthesizer 前保存 evidence summary 和 context metadata，成功后标记 completed。如果某个 run 是 resumable，`POST /runs/{run_id}/continue` 会读取 checkpoint，只执行 pending steps，不重复执行 completed steps。`POST /chat/resume` 则继续最近的 resumable checkpoint。

v1 不引入新数据库，也不做复杂 workspace diff，只用 JSON 文件和规则 drift 检查实现最小可恢复闭环。这样保持 Router、Planner、Executor 主链路不变，同时让系统具备可恢复任务状态。
