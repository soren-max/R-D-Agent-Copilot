# Demo Guide

本 demo 使用本地样例日志、配置、Git 和知识库数据，适合无真实企业 API、无 DeepSeek API Key 的本地验收和面试展示。

## Demo Case 1：简单问答

请求：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是配置中心？"}'
```

预期：

- `route.type = simple_qa`
- `tool_results` 包含 `rag_retriever`
- `trace.executor.engine = langgraph`
- `answer_source = fallback` 或 `llm`
- `trace.executor.skipped_nodes` 包含 log/config/git 节点
- 前端 Trace Viewer 展示 RAG 工具结果和跳过的工具节点

## Demo Case 2：复杂排障

请求：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```

预期：

- `route.type = complex_troubleshooting`
- `tool_results` 包含 `log_tool`、`config_tool`、`git_tool`、`rag_retriever`
- trace 记录 LangGraph node
- answer 包含初步判断、工具证据、建议处理方式
- `trace.executor.engine = langgraph`
- Evaluation Panel 展示工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时评分

## Demo Case 3：LLM fallback

当 `LLM_ENABLED=false` 或缺少 `DEEPSEEK_API_KEY` 时：

- 系统自动使用 fallback answer
- `/chat` 不崩溃
- `answer_source = fallback`
- `llm_used = false`
- `trace.synthesizer.engine = fallback`

这条路径适合无 API Key 的本地验收和 CI 测试。

## Demo Case 4：LLM enabled

如果本地 `.env` 设置：

```bash
LLM_ENABLED=true
DEEPSEEK_API_KEY=your_key_here
```

则 Answer Synthesizer 会尝试调用 DeepSeek API，把工具结果、RAG 文档和 trace 摘要组织成更自然的中文回答。

注意：不要提交真实 key。真实 key 只应放在本地 `.env`，`.env` 已被 `.gitignore` 忽略。

## Local Demo Script

启动服务后运行：

```bash
python scripts/demo_week1.py
```

脚本会发送 simple QA 和 complex troubleshooting 两个请求，并打印：

- answer
- answer_source
- route.type
- tool_names
- trace.executor.engine
- trace.synthesizer.engine

## Frontend Demo

启动后端：

```bash
uvicorn main:app --reload
```

启动前端：

```bash
cd apps/web
npm run dev
```

访问：

```text
http://127.0.0.1:3000
```

建议演示顺序：

1. 输入“什么是配置中心？”，展示 simple QA、RAG 结果和 skipped nodes。
2. 输入“为什么订单接口报500？”，展示复杂排障、工具结果、Trace Viewer 和 Evaluation Panel。
3. 说明 DeepSeek 默认关闭，系统仍能通过 fallback answer 完成演示。

## 面试讲解话术

这个项目是一个面向研发排障场景的 AI Agent 系统。我没有一开始就让大模型控制全部流程，而是先用确定性规则实现 Router、Planner、Executor 和工具调用闭环。流程稳定后，再引入 LangGraph 作为执行编排层，负责工具节点的条件执行、失败重试和 trace 记录。DeepSeek API 只接在最终回答生成器，用来把日志、配置、代码变更和 RAG 证据组织成中文排障报告。这样既能利用大模型生成能力，又能保证 Agent 主链路可测试、可追踪、可回退。
