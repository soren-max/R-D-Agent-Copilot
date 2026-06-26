# R&D Agent Copilot Web

Trace Viewer 前端工程骨架，基于 Next.js、TypeScript 和 TailwindCSS。

当前页面可以调用本地 FastAPI 后端 `POST /chat`，展示 Agent 回答、Evaluation 质量评分、路由类型、Planner steps、工具结果摘要和 Trace Viewer。

## 安装依赖

```bash
npm install
```

## 启动开发服务

```bash
npm run dev
```

默认访问：

```text
http://127.0.0.1:3000
```

## 环境变量

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

该变量只用于后续 `/chat` API 集成。不要在前端环境变量中放置 API Key 或任何密钥。

## Docker

前端容器由仓库根目录的 `docker-compose.yml` 构建和启动：

```bash
cd ../..
cp .env.example .env
docker compose up --build
```

默认访问：

```text
http://127.0.0.1:3000
```

容器内使用生产模式启动 Next.js，并通过 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` 访问本地 FastAPI 后端。

## Trace Viewer

Trace Viewer 用于展示 Agent 执行链路，帮助演示一次 `/chat` 请求如何经过 Router、Planner、LangGraph Executor 和 Synthesizer。

当前展示内容包括：

- Router、Planner、Executor、Synthesizer 阶段时间线
- LangGraph executor engine、graph_name 和 fallback 状态
- tool_calls 工具调用列表
- skipped_nodes 跳过节点列表
- retry、latency、source 等执行元数据
- Synthesizer 的 DeepSeek / 规则兜底状态
- Evaluation stage 的 rule_based 引擎、overall_score 和 latency_ms

## Evaluation 展示

Evaluation 面板展示 Agent 质量评分、工具成功率、Trace 完整性、知识库相关性、回答证据性、响应耗时评分、发现的问题和优化建议。

如果后端响应中没有 `evaluation` 字段，页面会显示“暂无评估结果”，不影响回答和 Trace Viewer 展示。

## 本地验收

先启动后端：

```bash
uvicorn main:app --reload
```

再启动前端：

```bash
npm run dev
```

在页面输入：

```text
什么是配置中心？
```

预期看到简单问答结果和 `rag_retriever` 工具结果。

再输入：

```text
为什么订单接口报500？
```

预期看到复杂排障结果和 `log_tool`、`config_tool`、`git_tool`、`rag_retriever` 工具结果。
同时应看到 Evaluation 面板中的 Agent 质量评分和指标明细。
