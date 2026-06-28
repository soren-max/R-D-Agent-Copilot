# Final Demo

## 1. Demo Preparation

后端启动：

```bash
uvicorn main:app --reload
```

前端启动：

```bash
cd apps/web
npm run dev
```

Docker 启动：

```bash
docker compose up --build
```

最终 demo 脚本：

```bash
python scripts/demo_final.py
```

如果后端未启动，脚本会提示：

```text
请先启动后端：uvicorn main:app --reload
```

## 2. Demo Flow

1. 打开前端：

```text
http://127.0.0.1:3000
```

2. 输入“什么是配置中心？”

3. 展示 simple_qa、`rag_retriever`、Trace Viewer：

- Router 将请求识别为 `simple_qa`
- Planner 生成知识检索步骤
- LangGraph Executor 执行 RAG 节点并跳过 log / config / git 节点
- Trace Viewer 展示每个阶段的输出和耗时

4. 输入“为什么订单接口报500？”

5. 展示 complex_troubleshooting、log/config/git/rag、LangGraph tool nodes：

- Router 将请求识别为 `complex_troubleshooting`
- Planner 生成日志、配置、Git 和 RAG 检索计划
- LangGraph Executor 执行 `log_tool`、`config_tool`、`git_tool` 和 `rag_retriever`
- Answer Synthesizer 基于工具结果生成中文排障回答

6. 展示 Evaluation 分数：

- Evaluation Panel 展示 `overall_score`
- 展示工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时评分
- 说明 Evaluation 只在回答后评估，不参与 Router、Planner 或 Tool Selection

7. 展示历史 run 查询 API：

- 先从 `/chat` 响应中复制 `run_id`
- 调用 `/runs` 查看最近执行记录
- 调用 `/runs/{run_id}` 查看单次执行的 steps、tool calls 和 evaluation

## 3. API Demo

POST `/chat`：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```

GET `/runs`：

```bash
curl http://127.0.0.1:8000/runs
```

GET `/runs/{run_id}`：

```bash
curl http://127.0.0.1:8000/runs/{run_id}
```

最终脚本 demo：

```bash
python scripts/demo_final.py
```

脚本会依次请求：

- 什么是配置中心？
- 为什么订单接口报500？

并打印：

- `run_id`
- `answer`
- `answer_source`
- `route.type`
- planner steps
- tool names
- `trace.executor.engine`
- `evaluation.overall_score`

## 4. What To Highlight

- 不是聊天套壳：系统不是直接把用户问题丢给 LLM，而是经过 Router、Planner、Executor、Tools、Trace、Synthesizer 和 Evaluation。
- Router / Planner 分层：Router 只分类，Planner 只生成结构化计划，职责边界清晰。
- LangGraph 工具编排：LangGraph 只在 Executor 内部负责编排工具节点、条件执行、retry、fallback 和节点 trace。
- API Adapter 可扩展：当前使用 LocalAdapter 调用本地 Mock API Server，后续可以替换真实日志平台、配置中心和 Git API。
- Trace 持久化：每次 `/chat` 会保存 run、step 和 tool call，支持 `/runs` 和 `/runs/{run_id}` 查询。
- Evaluation 质量评分：回答生成后，用 rule-based 指标评估工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时。
- DeepSeek 只用于最终回答生成：DeepSeek 不控制 Router、Planner 或 Tool Selection，默认关闭并支持 fallback。
