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

- Router：v0.2.0 支持 Prompt Engineering + JSON intent 输出，并保留 rule-based fallback。
- Planner：v0.2.0 支持结构化 JSON plan 输出，并保留确定性 fallback。
- LangGraph Executor：在 Executor 内部编排工具节点，支持条件执行、retry、fallback 和节点 trace。
- Tools：提供 `log_tool`、`config_tool`、`git_tool` 和本地 `rag_retriever`。
- Mock API Server：提供 `/mock/logs`、`/mock/configs`、`/mock/git/commits`，模拟日志平台、配置中心和 Git 平台。
- API Adapter：通过本地 Mock API 隔离样例数据和未来真实系统 API。
- OpenAI-Compatible LLM Provider：支持 DeepSeek/OpenAI-compatible endpoint 和本地 mock provider。
- DeepSeek Answer Synthesizer：可选使用 DeepSeek 生成最终中文排障报告，失败时自动 fallback。
- Trace Viewer：前端可视化展示 Router、Planner、Executor、Synthesizer 和 Evaluation 执行链路。
- Run / Trace Persistence：使用 SQLite 持久化历史 run、step 和 tool call，支持链路回查。
- Evaluation v1：基于工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时给出质量评分。
- RAG Pipeline：支持本地 Markdown 入库、结构化 chunk metadata、确定性向量检索、keyword fallback、hybrid retrieval、召回评估和 grounding guard。
- RAG Grounding v0.3.0：新增 `apps/api/app/kb` 本地排障知识库、关键词检索、evidence 构造和 grounded answer trace。
- Evidence Chain：将 log/config/git/rag/evaluation 输出整理为证据项、根因候选和 rule-based 置信度。
- Prompt Versioning：Router、Planner、Answer Synthesizer 记录 `prompt_name`、`prompt_version`、`model`、`raw_llm_output`、`parsed_output` 和错误信息到 Trace，支持策略回溯。
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

默认 `LLM_ENABLED=false`，不需要 DeepSeek API Key 也可以运行完整 fallback 链路。开启 DeepSeek / OpenAI-compatible provider 时，只在本地 `.env` 中设置：

```bash
LLM_ENABLED=true
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_TIMEOUT_SECONDS=15
```

兼容旧变量 `DEEPSEEK_API_KEY`；如果同时存在，优先使用 `LLM_API_KEY`。不要提交 `.env` 或真实 API Key。

切换到本地 mock provider：

```bash
LLM_PROVIDER=mock
LLM_MODEL=mock-json-model
```

mock provider 不访问网络，适合 Router / Planner 的 prompt JSON 调试和单元测试。

## v0.2.0 Prompt Engineering

本轮改造把 Chapter 2「提示学习与思维链」落到工程边界内：

- `app/prompts/router_prompt.txt` 约束 Router 只输出 intent/confidence/reason JSON。
- `app/prompts/planner_prompt.txt` 约束 Planner 只输出 task_type/steps JSON，并且工具只能来自白名单。
- `app/prompts/answer_synthesizer_prompt.txt` 约束最终回答只能基于 Tools 和 RAG evidence，证据不足时必须说明当前证据不足。
- `app/prompts/log_analysis_prompt.txt`、`config_diff_prompt.txt`、`git_change_prompt.txt` 为后续工具内证据分析预留领域 prompt。

LLM 在 Router/Planner 中只是可选结构化生成层；当 LLM 不可用、JSON 解析失败、超时、置信度过低或工具越权时，系统会回到现有 rule-based / deterministic fallback。

新增 provider 目录：

```text
app/llms/
  base.py
  openai_compatible.py
  mock_provider.py
```

同时保留 `apps/api/app/llms/` 和 `apps/api/app/prompts/` 兼容目录，便于后续迁移到 monorepo API layout。

## DeepSeek Answer Synthesizer

DeepSeek API 当前只用于最终回答生成；v0.2.0 额外提供 OpenAI-compatible provider 能力，用于受控的结构化 Router / Planner JSON 生成和 Answer Synthesizer。

DeepSeek API 当前通过 OpenAI-compatible provider 接入。Router 和 Planner 可在 `LLM_ENABLED=true` 时尝试结构化 JSON 输出，但 Tool Selection 仍被 Planner 解析器和工具白名单约束；LangGraph 工具编排仍在 Executor 内部执行。Answer Synthesizer 只能基于已有工具结果、RAG 文档和 trace 摘要组织中文排障报告。

DeepSeek 默认关闭。没有 API Key、网络异常或模型调用失败时，系统会自动使用 fallback answer，并在响应和 trace 中记录 `answer_source=fallback`、`llm_used=false` 和对应错误信息。

## Agent Streaming

`POST /chat` 仍然是标准同步接口，返回完整回答、工具结果、Trace 和 Evaluation。

`GET /chat/stream?query=...` 提供 SSE 执行状态流，用于前端实时展示 Agent 进度。当前 streaming 聚焦 Router、Planner、LangGraph Tool、Synthesizer 和 Evaluation 的执行事件，不做 DeepSeek token 级逐字输出。

前端会优先展示实时执行流；如果 SSE 失败，会提示“流式执行失败，已切换为普通请求。”并 fallback 到 `/chat`。

## RAG Pipeline

RAG 只读取 `data/docs/*.md`，通过 Markdown 标题、段落和代码块边界生成 chunk，并为每个 chunk 保留 `source`、`title`、`section`、`chunk_id`、`doc_type` 和 `updated_at` metadata。检索层提供 deterministic local vector search、keyword fallback 和 hybrid retrieval，不调用外部向量库、embedding 服务或企业 API。

v0.3.0 额外提供一条更简单、更容易审计的本地关键词 RAG 链路，位于：

```text
apps/api/app/rag/
  loader.py
  chunker.py
  query_rewrite.py
  keyword_search.py
  retriever.py
  evidence.py
  grounding.py
  evaluation.py
```

这条链路只读取本地 Markdown，不接向量数据库，不调用外部 embedding 服务。Chunk 结构固定包含：

```text
chunk_id
source
title
content
keywords
```

关键词检索支持 `top_k`，同时覆盖英文错误短语和中文排障关键词。无匹配时返回空列表，并将 grounding 标记为 `insufficient_evidence`。

v0.3.1/v0.3.2 增加低成本高收益的 Query Rewrite、Hybrid Search 和 RAG Evaluation：

- Query Rewrite：把中文排障表达扩展成可检索的英文错误短语，例如“端口被占用”扩展为 `port already in use`、`failed to start`、`listen port`。
- Hybrid Search：keyword hits 保精准，local token-vector hits 保召回，merge 后按 `chunk_id` 去重并返回 top_k。
- Evaluation：提供 Recall@5、Keyword Hit Rate、Grounding Score、No Evidence Rejection Accuracy、MRR 和 failed_cases，便于持续改知识库和 rewrite 规则。

v0.4.0 增加 Rerank + Grounding Check，目标不是让答案更长，而是让答案更可信：

```text
retrieved_chunks
-> evidence builder
-> reranker
-> answer synthesizer
-> grounding checker
-> final report + unsupported_claims + trace
```

新增模块：

```text
apps/api/app/rag/
  schemas.py
  reranker.py
  claim_extractor.py
  grounding_checker.py
```

关键输出：

- `rerank_results`：记录 chunk 原始分、rerank 分和 final score。
- `grounded_claims`：最终报告中能被 evidence 支撑的 claim。
- `unsupported_claims`：最终报告中未找到 evidence 支撑的 claim。
- `grounding_check.grounding_score`：claim-level grounded ratio。
- Trace 新增 `grounding_checker` stage，便于回看答案可信度。

## Planning Evaluation

v0.5.0 增加 Agent Planning Evaluation，用于评估 Router / Planner 是否选对意图、工具和步骤，让复杂 Agent 的规划质量可量化、可回放。

核心文件：

```text
evaluation/
  plan_quality.py
  planning_eval.py
  bad_case_replay.py

data/eval/
  planning_cases.jsonl
  planning_eval_report.md
  bad_cases.jsonl
  bad_case_replay_report.md
```

运行规划评估：

```bash
python -m evaluation.planning_eval
```

运行 bad case replay：

```bash
python -m evaluation.bad_case_replay
```

`data/eval/planning_cases.jsonl` 当前包含 30 条研发排障规划用例，覆盖：

- `knowledge_qa`
- `log_analysis`
- `config_diff`
- `git_change`
- `deployment_issue`
- `safety_risk`

每条 case 包含：

```text
case_id
question
expected_intent
expected_tools
must_have_steps
safety_required
```

Plan Quality Score 由 5 个 rule-based 子分数组成：

```text
plan_quality_score =
  intent_score * 0.25
  + required_tools_score * 0.25
  + step_order_score * 0.20
  + completeness_score * 0.20
  + safety_score * 0.10
```

输出字段包括：

- `missing_tools`
- `extra_tools`
- `wrong_order_steps`
- `failure_reasons`
- `plan_quality_score`

Bad Case Replay 会把失败 case 保存到 `data/eval/bad_cases.jsonl`，重新运行后输出 `fixed` / `still_failed` 到 `bad_case_replay_report.md`。

当前 v0.5.0 本地规划评估结果：

```text
total_cases: 30
router_intent_accuracy: 1.0
required_tools_hit_rate: 1.0
step_order_accuracy: 1.0
safety_tool_recall: 1.0
average_plan_quality_score: 1.0
failed_cases: 0
```

### v0.5.0 Changelog

- Added rule-based Planning Evaluation for Router and Planner.
- Added Plan Quality Score with intent, tools, order, completeness, and safety dimensions.
- Added 30 local planning eval cases for R&D troubleshooting scenarios.
- Added Bad Case Replay with `fixed` / `still_failed` status.
- Added planning eval fields to Trace schema for report and replay diagnostics.

运行 v0.3 RAG 评估：

```bash
python scripts/eval_v030_rag.py
```

当前 20 条本地评估用例结果：

```text
Recall@5: 0.6667 -> 1.0
Grounding Score: 0.7 -> 1.0
No Evidence Rejection Accuracy: 1.0
MRR: 0.9722
```

其中 baseline 为关闭 Query Rewrite 的 keyword 检索；当前结果为 Query Rewrite + Hybrid Search。

当前建议的 RAG 演进顺序：

1. Query Rewrite：成本低，能明显改善中文口语化问题的召回。
2. RAG Evaluation：让召回质量可量化，避免只凭主观 demo 判断。
3. Hybrid Search：已完成本地 keyword + token-vector merge，覆盖语义相近但关键词不一致的问题。
4. Rerank：已完成轻量本地 reranker，对 top-N 候选做更精细排序。
5. Grounding Check：已完成 claim-level checker，检查答案句子是否能被 evidence 支撑。

## Knowledge Base

v0.3.0 知识库目录：

```text
apps/api/app/kb/
  deployment_guide.md
  redis_common_issues.md
  nginx_error_guide.md
  database_slow_query.md
  ci_cd_failure_cases.md
  git_rollback_playbook.md
```

新增知识文档时：

1. 在 `apps/api/app/kb/` 添加 `.md` 文件。
2. 用一级标题写清文档主题。
3. 用二级标题拆分故障场景。
4. 在正文中写入用户可能提问的中英文关键词，例如 `port already in use`、`502`、`慢查询`、`连接池`。
5. 不要写真实内部域名、密钥、客户数据或生产日志原文。

## Grounding Mechanism

v0.3.0 的 grounding 规则：

- Retriever 返回相关 chunks。
- Query Rewrite 先扩展中英文排障关键词，再执行关键词检索。
- Evidence Builder 将 chunks 转成 `source`、`chunk_id`、`content_excerpt`、`score`。
- Reranker 对候选 chunks 重新排序，并记录 `rerank_results`。
- Grounding Checker 从最终报告抽取 claims，检查每条 claim 是否有 evidence overlap。
- Trace 在 executor stage 记录 `query`、`rewritten_queries`、`query_expansions`、`retrieved_chunks`、`rerank_results`、`evidence`、`grounding_status`、`no_evidence_reason`。
- Trace 在 grounding_checker stage 记录 `grounded_claims`、`unsupported_claims` 和 `claim_grounding_score`。
- Answer Synthesizer 只能基于 Tools 和 RAG evidence 输出中文排障报告。
- evidence 为空时，必须输出“当前证据不足”。
- 不允许编造日志、配置、Git 变更或命令执行结果。

Grounded answer 的 fallback 报告结构固定为：

```text
初步判断
证据
排查步骤
风险提示
```

当检索结果为空，或最高分低于阈值时，系统会把 `grounding_status` 标记为 `insufficient_evidence`。Answer Synthesizer 在该状态下不会调用 DeepSeek 编造答案，而是返回“当前知识库证据不足，建议补充日志、配置或相关文档后再判断。”

### RAG Design Details

Chunk strategy:

- Ingestion scans `data/docs/*.md` and splits by Markdown heading, paragraph, and fenced-code boundaries first, so chunks do not cut through sections or code blocks.
- Target chunk size is 650 tokens with 100-token overlap for oversized blocks. The current sample docs mostly stay below the limit, but the splitter is ready for longer documents.
- Chunk metadata is attached at ingestion time: `source`, `title`, `section`, `chunk_id`, `doc_type`, and `updated_at`. This lets the UI and trace show where every answer fragment came from.

Vector retrieval:

- The vector layer is intentionally local and deterministic. It uses token hashing embeddings and an in-memory cosine index instead of downloading models or connecting to a hosted vector database.
- This keeps tests reproducible and avoids violating the current project boundary. The retrieval contract still mirrors a vector DB surface: `top_k`, `score_threshold`, metadata filter, score, source, section, chunk id, and retrieval type.
- A lexical-overlap gate is applied before cosine ranking to avoid hash-collision false positives on unrelated queries.

Hybrid retrieval:

- Hybrid mode runs vector retrieval and keyword retrieval, merges scores, deduplicates by `chunk_id`, and sorts by final score.
- If the vector index is unavailable, retrieval automatically falls back to keyword search and records `fallback_used=true`.
- Returned documents include `retrieval_type` as `vector`, `keyword`, or `hybrid`, so trace and frontend panels can explain how evidence was found.

Recall evaluation:

- `eval/rag_eval_cases.jsonl` defines deterministic cases with `query`, `expected_sources`, and `expected_keywords`.
- `scripts/eval_rag.py` reports `Recall@3`, `Recall@5`, `Hit Rate`, `MRR`, `average_latency_ms`, and `failed_cases`.
- Low-score cases are written to `data/reports/rag_eval_failed_cases.json` for targeted knowledge-base or retriever tuning.

Hallucination control:

- RAG evidence is treated as insufficient when no documents pass retrieval or the top score is below the configured threshold.
- The grounding status is propagated through `tool_results`, executor trace, and the frontend RAG Panel.
- The Answer Synthesizer checks `grounding_status` before any LLM call. If evidence is insufficient, it returns the fixed safe answer and does not call DeepSeek.

运行 RAG 召回评估：

```bash
python scripts/eval_rag.py
```

脚本读取 `eval/rag_eval_cases.jsonl`，输出 `Recall@3`、`Recall@5`、`Hit Rate`、`MRR`、`average_latency_ms` 和 `failed_cases`，并将低分样本写入 `data/reports/rag_eval_failed_cases.json`。

## Grounding Guard

- 检索为空或最高分低于阈值时，设置 `grounding_status = insufficient_evidence`。
- Answer Synthesizer 在证据不足时不调用 DeepSeek，返回固定安全回答。
- grounding_status 通过 tool_results、executor trace 和前端 RAG Panel 展示。

## LLM Usage Tracking

系统会在 Answer Synthesizer 阶段记录 DeepSeek 调用的 token usage、LLM latency 和 estimated cost，并返回到 `/chat` 的 `llm_usage` 字段，同时写入 Trace 的 synthesizer step。

如果 API response 包含 usage，系统使用真实 token usage；如果没有 usage，则按字符数粗略估算 token。成本估算只用于本地演示，不作为真实计费依据；当前价格常量为演示占位值，未联网查询价格。LLM disabled 或 fallback 时 token 和 cost 为 0。

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
