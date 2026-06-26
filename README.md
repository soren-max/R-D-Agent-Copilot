# R-D-Agent-Copilot

研发排障智能助手 / Agent 系统 / 工具调用。

## Current Status

Current release target: v0.1.0

Status: Week1 backend Agent MVP completed

Next milestone: Trace Viewer + Evaluation + API adapter abstraction

## Week2 Frontend

`apps/web` 是 Trace Viewer 前端工程，使用 Next.js、TypeScript 和 TailwindCSS。

当前 PR 仅新增前端骨架，包含 Chat、Agent 执行结果和 Trace 执行链路的静态占位。后续会接入 `POST /chat` 和 Trace Viewer 展示，不在前端暴露 API Key。

## Week1 Milestone

- Day1 Agent MVP：完成 `POST /chat`、Router、Planner、Executor、Tools、Trace、Response 的确定性闭环。
- Day2 Local Tools：用本地样例数据实现日志、配置和 Git 变更工具。
- Day3 Local RAG：基于 `data/docs/` 实现本地知识库检索。
- Day4 LangGraph Execution Layer：把工具执行编排放入 Executor 内部的 LangGraph layer。
- Day5 Conditional Execution / Retry / Fallback：支持条件工具执行、失败重试和工具 fallback。
- Day6 DeepSeek Answer Synthesizer：DeepSeek 只用于最终中文回答生成，不控制 Router、Planner 或 Tool Selection。
- Day7 Regression / Docs / Release Checklist：补齐第一周回归验收、架构文档和 demo 说明。

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

默认 `LLM_ENABLED=false`，不需要 DeepSeek API Key 也可以运行完整 fallback 链路。

## API Demo

简单问答：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是配置中心？"}'
```

复杂排障：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```

本地 demo 脚本：

```bash
python scripts/demo_week1.py
```

更多说明见 `docs/architecture.md` 和 `docs/week1-demo.md`。

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

## API Adapter Layer

Adapter 层用于隔离真实系统 API 和本地 mock 数据来源，向后续工具改造提供统一的数据访问边界。tools 不直接绑定具体数据源，而是通过 Adapter 访问日志、配置和 Git 数据。

当前实现 `LocalLogAdapter`、`LocalConfigAdapter` 和 `LocalGitAdapter`，仍只面向本地确定性 mock 数据，不调用真实外部 API，不参与 Agent 推理、Planner 输出修改、Trace 写入或最终回答生成。后续可在保持工具契约稳定的前提下接入 `RealLogAPIAdapter`、`RealConfigCenterAdapter` 和 `RealGitAPIAdapter`。

这是第二周企业级改造重点之一：让 demo 继续可复现，同时保留未来替换真实系统 API 的扩展边界。更多说明见 `docs/day9-adapter-architecture.md`。

## Run / Trace Persistence

Day10 新增 SQLite 持久化基础设施，默认数据库文件为 `data/runs.db`，也可通过 `DATABASE_URL=sqlite:///data/runs.db` 配置。

`/chat` 执行完成后会持久化 Agent run、step 和 tool_call 数据，`run_id` 与 `trace.trace_id` 保持一致，便于后续前端 Trace Viewer 和查询 API 对齐历史执行链路。

后续可以通过查询 API 读取历史 run 和完整执行链路。

## Evaluation v1

Day11 新增 rule-based Agent 执行质量评估，评分维度包括工具成功率、Trace 完整性、RAG 命中、回答证据性和执行耗时。

当前 Evaluation v1 不使用 LLM 评审，不调用 DeepSeek，保证本地测试稳定且不影响 `/chat` 主流程。

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

## DeepSeek Answer Synthesizer

DeepSeek API 当前只用于最终回答生成，也就是 Answer Synthesizer 阶段。Router 分类、Planner steps、LangGraph 工具编排和 Tool Selection 仍由确定性代码控制，DeepSeek 只能基于已有工具结果、RAG 文档和 trace 摘要组织更自然的中文回答。

LLM 默认关闭。开启方式是在 `.env` 中设置：

```bash
LLM_ENABLED=true
DEEPSEEK_API_KEY=your_key_here
```

如果 LLM 关闭、API Key 缺失、网络异常或模型调用失败，`/chat` 会自动回退到 rule-based fallback answer，并在响应中返回 `answer_source=fallback`、`llm_used=false` 和对应 `llm_error`。测试不依赖真实 DeepSeek API。

更多本地验收步骤见 `docs/day6-deepseek-demo.md`。

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
