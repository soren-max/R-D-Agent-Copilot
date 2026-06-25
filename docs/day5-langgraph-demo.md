# Day5 LangGraph Demo 与验收清单

## 1. Day5 目标

Day5 重点验证 LangGraph 执行层的工程能力，范围保持在确定性后端 MVP 内：

- LangGraph 条件工具执行：根据 Planner 输出的 `plan.steps[].tool` 判断每个工具节点是否执行。
- 工具失败 retry：符合失败条件的工具最多重试 1 次。
- fallback 策略：单个工具失败不影响 `/chat` 整体返回，后续工具继续执行。
- trace 可观测性增强：记录执行节点、跳过节点、retry 次数、错误和 fallback 状态。

## 2. 架构说明

Router 和 Planner 仍由项目自定义实现。LangGraph 只负责 Executor 内部工具执行编排，不替代 Router、Planner，也不生成最终回答。

整体链路：

```text
User -> Router -> Planner -> Executor -> LangGraph Tool Nodes -> Trace -> Response
```

职责边界：

- Router：只分类 `simple_qa` 或 `complex_troubleshooting`。
- Planner：只根据 `query` 和 `route_result` 生成 deterministic plan。
- Executor：把 Planner 输出交给 LangGraph 执行工具节点，并收集工具结果。
- LangGraph Tool Nodes：按计划条件执行工具，记录 skipped、retry 和 fallback 元数据。
- Trace：返回完整内存追踪数据，便于验收和后续可视化。
- Response：保留 `answer`、`route`、`plan`、`tool_results`、`trace` 结构。

## 3. Demo Case 1：简单问答

请求：

```json
{
  "query": "什么是配置中心？"
}
```

预期：

- `route.type = simple_qa`
- Planner 只规划 `rag_retriever`
- LangGraph 只执行 `rag_tool_node`
- `log_tool_node`、`config_tool_node`、`git_tool_node` 被 skipped
- `trace.steps[].skipped_nodes` 中记录跳过原因：`tool_not_in_plan`
- `tool_results` 中不包含 skipped 节点

关键验收字段：

```json
{
  "tool_results": [
    {
      "node": "rag_tool_node",
      "tool_name": "rag_retriever",
      "status": "success",
      "retry_count": 0
    }
  ],
  "trace": {
    "steps": [
      {
        "stage": "executor",
        "engine": "langgraph",
        "skipped_nodes": [
          {
            "node": "log_tool_node",
            "tool_name": "log_tool",
            "reason": "tool_not_in_plan"
          }
        ],
        "fallback_used": false
      }
    ]
  }
}
```

## 4. Demo Case 2：复杂排障

请求：

```json
{
  "query": "为什么订单接口报500？"
}
```

预期：

- `route.type = complex_troubleshooting`
- Planner 规划 `log_tool`、`config_tool`、`git_tool`、`rag_retriever`
- LangGraph 执行全部对应工具节点
- trace 中 `engine = langgraph`
- `tool_calls` 中包含 `node`、`status`、`latency_ms`
- 工具成功时 `retry_count = 0`
- `skipped_nodes = []`

关键验收字段：

```json
{
  "trace": {
    "steps": [
      {
        "stage": "executor",
        "engine": "langgraph",
        "graph_name": "tool_execution_graph",
        "tool_calls": [
          {
            "node": "log_tool_node",
            "tool_name": "log_tool",
            "status": "success",
            "retry_count": 0,
            "latency_ms": 10
          }
        ],
        "fallback_used": false
      }
    ]
  }
}
```

## 5. Demo Case 3：工具失败 fallback

可以通过 pytest `monkeypatch` 模拟工具失败，不要删除真实 `data/` 文件。例如让 `LogTool.run` 返回：

```python
{
    "tool_name": "log_tool",
    "status": "failed",
    "result": "",
    "confidence": 0.0,
    "source": "data/logs/order-service.log",
    "documents": [],
    "error": "file_not_found",
}
```

预期：

- `/chat` 不崩溃
- failed 工具进入 `tool_results`
- 失败工具最多重试 1 次，最终结果包含 `retry_count = 1`
- 后续 `config_tool`、`git_tool`、`rag_retriever` 仍继续执行
- trace 中 `fallback_used = true`
- trace 的 failed `tool_calls` 中包含 `error` 和 `retry_count`
- answer 中说明“部分工具查询失败”

关键验收字段：

```json
{
  "tool_results": [
    {
      "node": "log_tool_node",
      "tool_name": "log_tool",
      "status": "failed",
      "error": "file_not_found",
      "retry_count": 1
    }
  ],
  "trace": {
    "steps": [
      {
        "stage": "executor",
        "fallback_used": true,
        "tool_calls": [
          {
            "node": "log_tool_node",
            "tool_name": "log_tool",
            "status": "failed",
            "retry_count": 1,
            "error": "file_not_found"
          }
        ]
      }
    ]
  }
}
```

## 6. 面试讲解话术

我先用确定性规则实现 Router、Planner、Executor 和工具调用闭环，等流程稳定后再引入 LangGraph。LangGraph 在项目中不是替代 Agent 设计，而是作为执行编排层，负责工具节点的状态流转、条件执行、失败重试和 trace 记录。这样系统既保持可控，又能体现复杂 Agent workflow 的工程能力。

## 验收清单

- [ ] simple QA 只执行 `rag_retriever`
- [ ] simple QA 的 log/config/git 节点进入 `skipped_nodes`
- [ ] complex troubleshooting 执行全部计划工具
- [ ] 成功工具 `retry_count = 0`
- [ ] 失败工具最多重试 1 次
- [ ] 工具失败不导致 `/chat` 崩溃
- [ ] fallback 时 `trace.executor.fallback_used = true`
- [ ] fallback 时 answer 包含“部分工具查询失败”
- [ ] `/chat` 响应仍包含 `answer`、`route`、`plan`、`tool_results`、`trace`
- [ ] 未接 DeepSeek、真实 LLM、前端或数据库
