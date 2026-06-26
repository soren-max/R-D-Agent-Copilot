# Day10 Trace Persistence

## 1. Day10 目标

Day10 为 R&D Agent Copilot 增加执行链路持久化和历史查询能力。系统在保持 Router、Planner、Executor、LangGraph、Tools、RAG 和 Synthesizer 边界不变的前提下，将每次 `/chat` 的 run、stage step 和 tool call 写入 SQLite，并提供只读查询 API。

## 2. 数据库表设计

当前使用 SQLite，默认数据库为 `data/runs.db`，也可以通过 `DATABASE_URL=sqlite:///data/runs.db` 指定。

- `agent_runs`：保存一次 Agent 执行的 run 元数据，包括 `run_id`、用户原始问题、route 类型、回答来源、LLM 使用情况、状态、总耗时和创建时间。
- `agent_steps`：保存 Router、Planner、Executor、Synthesizer 四个阶段的输入、输出、引擎、耗时和状态。
- `tool_calls`：保存 Executor / LangGraph 中实际调用的工具节点，包括 node、tool_name、状态、source、confidence、retry_count、error、latency_ms 和工具结果摘要。

## 3. `/chat` 持久化流程

每次 `/chat` 请求仍然先完成原有 Agent 链路：

```text
User Query
-> Router
-> Planner
-> Executor
-> LangGraph Tool Nodes
-> Trace
-> Answer Synthesizer
-> Response
```

请求完成后，API 层使用 `trace.trace_id` 作为 `run_id` 写入持久化存储：

- 写入 `agent_runs`
- 写入 router / planner / executor / synthesizer 四个 `agent_steps`
- 将 executor 的实际工具执行结果写入 `tool_calls`

如果数据库写入失败，`/chat` 主流程不会崩溃，仍会返回 answer、route、plan、tool_results 和 trace，并在 trace 中标记脱敏的 `persistence_error`。

## 4. 查询 API

### `GET /runs`

返回最近的 Agent runs。查询参数 `limit` 默认 20，超过 100 时自动限制为 100。

```bash
curl "http://127.0.0.1:8000/runs?limit=20"
```

### `GET /runs/{run_id}`

返回某一次完整执行链路，包括 run 元数据、阶段 steps 和工具调用 tool_calls。

```bash
curl "http://127.0.0.1:8000/runs/{run_id}"
```

如果 `run_id` 不存在，返回 HTTP 404：

```json
{"detail": "run_not_found"}
```

## 5. 面试讲解话术

“第十天我给 Agent 执行链路增加了持久化能力。每次 /chat 请求都会生成 run_id，并保存 Router、Planner、LangGraph Executor、Synthesizer 以及每次工具调用。这样系统不仅能当场展示 Trace，还可以回查历史执行记录，为后续评估、审计和 Trace Viewer 历史页打基础。”
