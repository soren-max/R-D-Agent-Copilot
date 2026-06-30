# R&D Agent Copilot

AI 研发排障智能助手

## Project Overview

R&D Agent Copilot 是一个面向研发排障场景的 AI Agent 系统，支持知识问答、日志排查、配置差异分析、Git 变更定位和中文排障报告生成。

项目当前定位是可复现、可测试、可追踪的后端 + Trace Viewer MVP。它用本地样例数据模拟研发排障链路，在不接入真实企业系统的前提下展示一个 Agent 从问题理解、任务规划、工具执行、证据记录到最终回答和质量评估的完整流程。

## Why This Project

微服务系统排障通常不是单点问题，而是跨日志、配置、代码变更和知识库的证据收集过程：

- 微服务系统排障链路长，问题定位需要跨多个信息源。
- 日志、配置、代码变更分散，人工切换上下文成本高。
- 人工排查效率低，且结论很难稳定复现。
- Agent 系统不能只给答案，还需要可追踪、可回退、可评估。

本项目的核心思路是：让大模型只负责最终表达，Router、Planner、工具选择和执行链路保持确定性，从而兼顾可演示性、可测试性和工程边界。

## Core Features

- Router：将用户问题分流为简单问答或复杂排障。
- Planner：根据问题类型生成结构化任务计划。
- LangGraph Executor：在 Executor 内部编排工具节点，支持条件执行、retry、fallback 和节点 trace。
- Tools：提供 `log_tool`、`config_tool`、`git_tool` 和本地 `rag_retriever`。
- Mock API Server：提供 `/mock/logs`、`/mock/configs`、`/mock/git/commits`，模拟日志平台、配置中心和 Git 平台。
- API Adapter：通过本地 Mock API 隔离样例数据和未来真实系统 API。
- DeepSeek Answer Synthesizer：可选使用 DeepSeek 生成最终中文回答，失败时自动 fallback。
- Trace Viewer：前端可视化展示 Router、Planner、Executor、Synthesizer 和 Evaluation 执行链路。
- Run / Trace Persistence：使用 SQLite 持久化历史 run、step 和 tool call，支持链路回查。
- Evaluation v1：基于工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时给出质量评分。
- Evidence Chain：将 log/config/git/rag/evaluation 输出整理为证据项、根因候选和 rule-based 置信度。
- Prompt Versioning：Answer Synthesizer 记录 `synthesizer_prompt_v1` / `fallback_prompt_v1` 到 Trace，支持回答策略回溯。
- Docker + CI：提供 Docker Compose 本地全栈启动和 GitHub Actions CI。

## Architecture

```text
User Query
-> Router
-> Planner
-> LangGraph Executor
-> Tools / RAG
-> Trace
-> Answer Synthesizer
-> Evaluation
-> Evidence Chain
-> Response / Trace Viewer
```

关键边界：

- DeepSeek 不控制 Router、Planner 或 Tool Selection，只在 Answer Synthesizer 阶段基于已有证据生成中文回答。
- Tools 当前通过 Adapter 调用本地 Mock API，Mock API 只读取本地样例日志、配置和 Git 数据；知识库仍通过本地 RAG 检索。后续可替换为真实企业 API Adapter。
- Trace 记录每个执行阶段，包括 stage 输出、latency、tool calls、skipped nodes、retry、fallback、prompt_version 和 synthesizer 元数据。
- Evaluation 在回答生成之后运行，不参与 Agent 决策，只用于质量评估和展示。
- Evidence Chain 在 Evaluation 之后运行，只基于已有工具结果、知识库结果和评估结果生成可解释证据与置信度，不调用 LLM。

更多架构说明见 [docs/architecture.md](docs/architecture.md)。

## Tech Stack

Backend:

- FastAPI
- Python
- LangGraph
- SQLite
- SQLAlchemy
- Pytest

LLM:

- DeepSeek API with fallback

Frontend:

- Next.js
- TypeScript
- TailwindCSS

DevOps:

- Docker Compose
- GitHub Actions

## Quick Start

后端：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

前端：

```bash
cd apps/web
npm install
npm run dev
```

Docker：

```bash
cp .env.example .env
docker compose up --build
```

默认地址：

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

默认 `LLM_ENABLED=false`，不需要 DeepSeek API Key 也可以运行完整 fallback 链路。开启 DeepSeek 时，只在本地 `.env` 中设置：

```bash
LLM_ENABLED=true
DEEPSEEK_API_KEY=your_api_key_here
```

不要提交 `.env` 或真实 API Key。

## DeepSeek Answer Synthesizer

DeepSeek API 当前只用于最终回答生成，也就是 Answer Synthesizer 阶段。Router 分类、Planner steps、LangGraph 工具编排和 Tool Selection 仍由确定性代码控制，DeepSeek 只能基于已有工具结果、RAG 文档和 trace 摘要组织更自然的中文回答。

DeepSeek 默认关闭。没有 API Key、网络异常或模型调用失败时，系统会自动使用 fallback answer，并在响应和 trace 中记录 `answer_source=fallback`、`llm_used=false` 和对应错误信息。

## Demo Queries

简单问答：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是配置中心？"}'
```

预期效果：

- Router 输出 `simple_qa`
- Planner 生成知识检索计划
- RAG 返回本地知识库片段
- Trace Viewer 展示 log/config/git 节点被跳过
- 最终返回中文知识问答

复杂排障：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```

预期效果：

- Router 输出 `complex_troubleshooting`
- Planner 生成日志、配置、Git 和 RAG 检索计划
- LangGraph Executor 执行工具节点并记录 trace
- Answer Synthesizer 汇总证据生成中文排障报告
- Evaluation v1 返回质量评分、问题和建议
- Evidence Chain 返回 evidence_items、root_cause_candidates 和 overall_confidence

更多 demo 步骤见 [docs/week1-demo.md](docs/week1-demo.md)。

最终演示脚本：

```bash
python scripts/demo_final.py
```

完整演示流程见 [docs/final-demo.md](docs/final-demo.md)。

## Screenshots / Demo

当前仓库暂未提交截图，避免编造展示素材。建议后续补充：

- Chat UI
- Trace Viewer
- Evaluation Panel

## Current Scope

当前项目是可复现 MVP：

- 使用 Mock API Server 模拟日志平台、配置中心和 Git 平台，底层只读本地样例数据。
- 使用 Adapter 隔离平台访问，工具链面向统一 `AdapterResult`，保留未来接入真实 API 的扩展边界。
- 支持 DeepSeek 可选接入，默认关闭并自动 fallback。
- 不包含真实日志平台、真实配置中心、真实 Git API 或真实企业系统 API。
- 不包含 Redis、Postgres 或复杂生产部署方案。

## Future Work

- RealLogAPIAdapter
- RealConfigCenterAdapter
- RealGitAPIAdapter
- Trace 历史页
- LLM Judge / Human Review
- 权限控制
- 更完整的部署方案

## CI

GitHub Actions CI 包含后端和前端两个 job：

- 后端安装 `requirements.txt` 并执行 `python -m pytest`
- 前端在 `apps/web` 下执行 `npm ci` 和 `npm run lint`

PR 需要保持 CI 通过。

## Interview Materials

- [docs/project-pitch.md](docs/project-pitch.md)：简历和面试介绍话术。
- [docs/interview-notes.md](docs/interview-notes.md)：架构讲解、演示路径和边界说明。
- [docs/interview-script.md](docs/interview-script.md)：30 秒、1 分钟、3 分钟面试讲稿和常见追问。
- [docs/release-v0.2.0.md](docs/release-v0.2.0.md)：v0.2.0 最终验收清单。
