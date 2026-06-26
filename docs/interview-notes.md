# Interview Notes

## 项目一句话

R&D Agent Copilot 是一个面向研发排障场景的 AI Agent MVP，用确定性 Router / Planner / Executor 和本地工具证据生成可追踪、可回退、可评估的中文排障回答。

## 架构图文字版

```text
User Query
-> FastAPI /chat
-> Router(simple_qa | complex_troubleshooting)
-> Planner(structured steps)
-> Executor
-> LangGraph Tool Nodes(log / config / git / rag)
-> Trace(stage output, latency, tool calls, retry, fallback)
-> Answer Synthesizer(DeepSeek optional, fallback default)
-> Evaluation v1(rule-based quality score)
-> Response
-> Trace Viewer
```

## 关键技术点

- Agent 边界：Router 只分类，Planner 只规划，Executor 只执行，Tools 只读取数据，Synthesizer 只生成最终回答。
- LLM 安全边界：DeepSeek 默认关闭，只在最终回答阶段使用，不控制工具选择和执行计划。
- LangGraph 执行层：负责工具节点编排、条件执行、retry、fallback 和节点 trace。
- LocalAdapter：把工具和数据源隔离，当前读取本地样例数据，未来可替换真实 API。
- Trace：每次请求返回完整执行链路，包含 stage、latency、tool calls、skipped nodes 和 fallback 信息。
- Persistence：SQLite 持久化 run、step 和 tool call，便于后续历史链路回查。
- Evaluation：rule-based 评分让 Agent 质量可解释、可展示、可持续优化。
- DevOps：Docker Compose 支持本地全栈 demo，GitHub Actions 执行后端测试和前端 typecheck。

## 可演示路径

1. 启动后端：

```bash
uvicorn main:app --reload
```

2. 启动前端：

```bash
cd apps/web
npm run dev
```

3. 演示简单问答：

```text
什么是配置中心？
```

观察点：

- Router 选择 simple_qa
- RAG 返回知识库结果
- Trace Viewer 展示非必要工具节点被跳过

4. 演示复杂排障：

```text
为什么订单接口报500？
```

观察点：

- Router 选择 complex_troubleshooting
- Planner 输出日志、配置、Git 和 RAG 步骤
- LangGraph 执行工具节点
- 最终回答引用工具证据
- Evaluation Panel 展示质量评分和建议

5. 演示 fallback 边界：

```text
LLM_ENABLED=false
```

观察点：

- 没有 DeepSeek API Key 也能返回回答
- Trace 中可看到 synthesizer 使用 fallback

## 不夸大的边界说明

当前项目使用本地样例数据模拟研发排障，不声称真实上线或服务真实企业用户。

当前项目已经展示了 Agent 主链路、Trace Viewer、Evaluation、SQLite 持久化、Docker Compose 和 CI，但仍属于可复现 MVP：

- 日志、配置、Git 数据来自 `data/` 下的本地样例。
- Adapter 当前是 LocalAdapter，不调用真实企业系统。
- DeepSeek 是可选最终回答生成器，默认关闭。
- Evaluation v1 是 rule-based，不是完整 LLM Judge。
- 部署方案面向本地 demo 和开发流程，不是生产级高可用架构。
