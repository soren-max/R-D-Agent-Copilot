# R-D-Agent-Copilot

研发排障智能助手 / Agent 系统 / 工具调用。

## Day1 MVP

Day1 只实现最小可运行 Agent 闭环：

User -> Router -> Planner -> Executor -> Tools -> Trace -> Response

当前范围：

- `POST /chat`
- 规则 Router：`simple_qa` / `complex_troubleshooting`
- Planner：简单问答单步计划，复杂排障三步计划
- Mock Tools：`log_tool`、`config_tool`、`git_tool`
- Executor：按 Planner 步骤调用工具
- Trace：每次请求返回完整内存 Trace

Day1 不包含 LangGraph、RAG、真实 LLM、前端、数据库、Redis 或外部 API。

## 本地样例数据说明

Day2 提供一组确定性的本地排障样例数据，作为后续工具系统强化的数据来源：

- `data/logs/order-service.log`：模拟订单接口 500、payment-service timeout、trace_id 和服务名等日志线索。
- `data/configs/dev.json` / `data/configs/prod.json`：模拟不同环境配置差异，包括支付超时、订单重试次数和新支付流程开关。
- `data/git/commits.json`：模拟最近提交记录，包含提交 ID、作者、变更文件、风险等级和中文友好的摘要。

这些数据仅用于本地确定性排障演示，不接入真实外部 API、数据库、RAG 或 LLM。

## Local Knowledge Base

`data/docs/` 存放本地知识库样例文档，覆盖配置中心、服务日志、接口异常排查流程和订单服务 FAQ。Day3 会基于这些文档实现轻量 RAG 检索。当前文档仅用于模拟研发排障场景，不接入外部知识库或真实公司数据。

## LangGraph Execution Layer

Router 和 Planner 仍由项目自定义实现。LangGraph 只用于 Executor 内部工具执行编排，不替代现有意图分类和任务规划。当前 graph 节点包括 `log_tool_node`、`config_tool_node`、`git_tool_node`、`rag_tool_node`。每个节点执行结果会进入 trace，方便后续 Trace Viewer 展示。

## Day5 LangGraph Execution

Day5 在 Executor 内部增强 LangGraph 工具编排能力：

- 根据 Planner 输出的 `plan.steps[].tool` 条件执行工具节点。
- 对临时失败工具最多重试 1 次，并在失败后继续执行后续工具。
- 在 trace 中记录 `tool_calls`、`skipped_nodes`、`retry_count`、`error` 和 `fallback_used`。
- 保持 Router、Planner、Executor、Tools、Trace、Response 的既有职责边界。

运行测试：

```bash
python -m pytest
```

运行本地服务：

```bash
uvicorn main:app --reload
```

运行 demo 请求：

```bash
python scripts/demo_day5.py
```

也可以直接请求复杂排障示例：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```

当前 Day5 范围不包含 DeepSeek、真实 LLM、前端、数据库或外部 API。

更多验收说明见 `docs/day5-langgraph-demo.md`。

## DeepSeek API Configuration

Day6 开始支持 DeepSeek API 配置和 OpenAI-compatible client 封装。LLM 默认关闭，仅作为后续最终回答生成器使用，不控制 Router、Planner、Tool 执行或 LangGraph 编排。

在 `.env` 中按需配置：

```bash
LLM_ENABLED=true
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=your_api_key_here
```

默认 `LLM_ENABLED=false`，没有 API Key 时项目仍可运行。真实 API Key 不应写入代码或提交到仓库。

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Test

```bash
python -m pytest
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```
