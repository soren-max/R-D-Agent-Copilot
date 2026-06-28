# Architecture

## 1. System Overview

R&D Agent Copilot 是一个 AI 研发排障智能助手，用于模拟研发场景中的常见问题处理流程。当前目标不是接入真实生产系统，而是建立一个可测试、可追踪、可回退、可评估的 Agent MVP。

系统覆盖以下能力：

- 业务知识问答
- 日志排查
- 配置差异分析
- Git 变更分析
- 知识库辅助解释
- 最终中文排障报告生成
- 前端 Trace Viewer
- Run / Trace 持久化
- Agent 执行质量评估

所有工具数据来自本地确定性样例，便于 demo、测试和 review。

## 2. Core Flow

```text
User Query
-> Router
-> Planner
-> LangGraph Executor
-> Tools / RAG
-> Trace
-> Answer Synthesizer
-> Evaluation
-> Response / Trace Viewer
```

这个流程保证每次 `/chat` 请求都会先经过确定性的分类、规划和工具执行，再进入最终回答生成。DeepSeek 如果启用，也只在 Answer Synthesizer 阶段基于已有结果生成中文表达。

## 3. Module Responsibility

Router：
只负责把用户问题分类为 `simple_qa` 或 `complex_troubleshooting`。Router 不调用工具，不生成最终答案，也不拆解任务。

Planner：
只负责根据 `query` 和 Router 输出生成结构化执行计划。简单问答会规划 `retrieve_knowledge`，复杂排障会规划日志、配置、Git 和 RAG 检索步骤。

Executor：
只负责执行 Planner 给出的计划，不重新规划，不修改 Planner 输出，也不生成最终答案。

LangGraph：
只负责 Executor 内部工具节点编排、条件执行、retry、fallback。它不替代 Router 或 Planner。

Tools：
通过 Adapter 层访问日志、配置和 Git 提交记录。当前 Adapter 调用本地 Mock API Server：`/mock/logs`、`/mock/configs`、`/mock/git/commits`，由 Mock API 读取本地确定性样例数据，保持 demo 可复现。Tools 不调用 LLM，不访问真实外部系统，不生成最终答案。

API Adapter：
封装系统数据访问边界，当前包括 `LocalLogAdapter`、`LocalConfigAdapter` 和 `LocalGitAdapter`。Adapter 返回统一 `AdapterResult`，用于隔离本地 Mock API 和未来真实 API。后续可以扩展 `RealLogAPIAdapter`、`RealConfigCenterAdapter` 和 `RealGitAPIAdapter`，但不应改变 Router、Planner、Executor、LangGraph、RAG、Trace 或前端 Trace Viewer 的职责。

RAG：
只做本地知识库检索，返回相关文档片段和来源，不生成最终答案。

DeepSeek：
只用于 Answer Synthesizer，不控制 Router / Planner / Tool Selection。它只能基于已有工具结果、RAG 文档和 trace 摘要组织中文回答。

Trace：
记录全链路可观测信息，包括 trace id、stage 输出、latency、LangGraph tool calls、skipped nodes、fallback 状态、prompt_version 和 synthesizer 元数据。

Prompt Versioning：
Answer Synthesizer 的 DeepSeek prompt 与 fallback prompt 使用显式版本号管理，当前为 `synthesizer_prompt_v1` 和 `fallback_prompt_v1`。每次请求都会在 synthesizer trace step 中记录 `prompt_version`，历史 Run 回放可据此还原回答生成策略。

Persistence：
使用 SQLite 保存 run、step 和 tool call 数据，默认数据库为 `data/runs.db`。持久化层只保存执行结果，不参与 Router、Planner、Tool Selection 或最终回答生成。

Evaluation：
在回答生成之后读取 route、plan、tool_results、trace 和 answer，输出 rule-based 质量评分。Evaluation 不参与 Agent 决策，只用于展示执行质量和后续优化方向。

Trace Viewer：
Next.js 前端展示 Chat UI、Agent 回答、Planner steps、工具结果、Trace 时间线和 Evaluation Panel。前端不保存或暴露任何 API Key。

## 4. Why This Design

- 先确定性闭环，后引入 LLM：先保证 Router、Planner、Executor、Tools、Trace 能稳定运行，再把 LLM 放到最末端做语言生成。
- 先纯 Python 验证 Agent 流程，再接 LangGraph：Day1 先验证 Agent 主链路，Day4 以后再把 Executor 内部工具编排迁移到 LangGraph。
- LLM 只负责语言生成，避免影响工具执行稳定性：DeepSeek 不参与工具选择，不修改 Planner 输出，也不能绕过 LangGraph。
- Adapter 隔离数据源，保持 Agent 主链路稳定：Tools 面向统一 AdapterResult，当前 Adapter 调用本地 Mock API Server 保证 demo 和测试稳定，未来替换真实系统 API 时不需要改动 Router、Planner、LangGraph 或前端 Trace Viewer。
- Evaluation 独立于执行链路：先完成回答，再评估质量，避免评分逻辑反过来影响 Router、Planner 或工具执行。
- 每个 PR 单独模块，方便 review 和回滚：工具数据、RAG、LangGraph、DeepSeek、文档和回归测试都按清晰目标拆分。
