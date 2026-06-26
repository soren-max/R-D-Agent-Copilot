# Project Pitch

## 30 秒介绍

R&D Agent Copilot 是一个面向研发排障场景的 AI Agent 系统。它把一次问题请求拆成 Router、Planner、LangGraph Executor、Tools / RAG、Trace、Answer Synthesizer 和 Evaluation 等阶段，支持知识问答、日志排查、配置差异分析、Git 变更定位和中文排障报告生成。项目重点不是让大模型控制所有流程，而是把工具执行链路做成可测试、可追踪、可回退的工程化 MVP。

## 1 分钟介绍

这个项目模拟研发同学排查线上问题时的工作流：先判断用户是在问知识问题还是复杂故障，再生成结构化计划，然后用 LangGraph 编排日志、配置、Git 和 RAG 工具收集证据。所有工具当前读取本地样例数据，保证 demo 和测试稳定。DeepSeek 只作为最终 Answer Synthesizer，把已有证据组织成中文排障报告，不能控制 Router、Planner 或工具选择。系统还记录完整 Trace，前端 Trace Viewer 可以展示每个阶段的执行过程，Evaluation v1 会对工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时进行评分。它适合展示我对 Agent 架构边界、工具调用、可观测性、评估和工程交付的理解。

## 技术亮点

- 确定性 Agent 主链路：Router、Planner、Executor 和工具选择不由 LLM 控制，便于测试和回归。
- LangGraph 工具编排：在 Executor 内部负责条件执行、retry、fallback、skipped nodes 和节点级 trace。
- Adapter 边界：Tools 通过 LocalAdapter 读取本地数据，未来可以替换真实日志平台、配置中心和 Git API。
- Trace Viewer：前端展示 Router、Planner、LangGraph Executor、Synthesizer 和 Evaluation 的执行链路。
- Evaluation v1：用 rule-based 指标量化 Agent 执行质量，为后续 LLM Judge 或人工评审预留入口。
- 工程化交付：提供 FastAPI 后端、Next.js 前端、SQLite 持久化、Docker Compose 和 GitHub Actions CI。

## 面试官可能追问

### 1. 为什么 DeepSeek 不控制 Planner？

因为 Planner 决定工具调用链路，如果让 LLM 直接控制，结果会更难复现，也更难测试和回滚。本项目把 DeepSeek 放在最终 Answer Synthesizer，只基于 Router、Planner、工具结果、RAG 和 Trace 生成中文表达，避免 LLM 绕过工具证据或修改执行计划。

### 2. 为什么先用 LocalAdapter？

LocalAdapter 可以让 demo、测试和 CI 不依赖真实企业系统，也不会触碰真实日志、配置或代码平台。它同时定义了工具访问数据源的边界，后续替换成 RealLogAPIAdapter、RealConfigCenterAdapter 或 RealGitAPIAdapter 时，不需要重写 Router、Planner、LangGraph 或前端 Trace Viewer。

### 3. LangGraph 在项目中负责什么？

LangGraph 只在 Executor 内部负责工具节点编排，包括根据 Planner steps 条件执行节点、记录跳过节点、处理 retry 和 fallback，并把节点执行元数据写入 Trace。它不负责意图分类，不生成计划，也不生成最终回答。

### 4. Evaluation v1 有什么意义？

Evaluation v1 让系统不只是返回答案，还能解释这次 Agent 执行质量如何。它会评估工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时，用于前端展示和后续迭代。当前用 rule-based 方式，是为了保证本地可复现、CI 稳定和评分可解释。

### 5. 如何替换成真实企业 API？

保留 Tool 的输入输出契约，把当前 LocalAdapter 替换为真实 Adapter，例如 RealLogAPIAdapter、RealConfigCenterAdapter 和 RealGitAPIAdapter。真实 Adapter 负责鉴权、请求、超时、错误处理和数据标准化，向上仍返回统一结果。这样 Router、Planner、Executor、Trace、Evaluation 和前端展示都可以尽量保持不变。
