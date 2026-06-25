# v0.1.0 Release Checklist

## 1. Release Goal

v0.1.0 是 R&D Agent Copilot 的第一周稳定版本，目标是完成一个可运行、可测试、可追踪的 Agent 排障后端闭环。

这个版本聚焦后端 Agent 主链路：用户请求进入 `/chat` 后，依次经过 Router、Planner、Executor、LangGraph 工具节点、Trace 和 Answer Synthesizer，最终返回中文排障回答和完整内存 trace。

## 2. Completed Features

- Router：`simple_qa` / `complex_troubleshooting` 分类
- Planner：结构化任务规划
- Local Tools：log / config / git 工具
- Local RAG：本地知识库检索
- LangGraph Execution Layer：工具节点执行编排
- Conditional Tool Execution：按计划执行工具
- Retry / Fallback：工具失败不影响主流程
- Trace：router / planner / executor / synthesizer 全链路记录
- DeepSeek Answer Synthesizer：可选 LLM 最终回答生成
- LLM fallback：无 key 或失败时自动回退

## 3. Not Included Yet

- Frontend UI
- Trace Viewer
- Database persistence
- Redis cache
- Real Git API
- Real log platform API
- Real config center API
- Evaluation dashboard
- LLM Router / LLM Planner

## 4. Acceptance Checklist

- [ ] `python -m pytest` 全部通过
- [ ] `/chat` simple_qa 正常
- [ ] `/chat` complex_troubleshooting 正常
- [ ] `LLM_ENABLED=false` fallback 正常
- [ ] 缺少 `DEEPSEEK_API_KEY` 不崩溃
- [ ] `.env` 未提交
- [ ] `.env.example` 不包含真实 key
- [ ] README 包含 Quick Start
- [ ] `docs/week1-demo.md` 可复现 demo
- [ ] `AGENTS.md` 规则仍然有效

## 5. Demo Commands

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

## 6. Next Week Plan

- Day8：Trace Viewer 前端页面
- Day9：Evaluation v1
- Day10：真实 API adapter 抽象
- Day11：配置中心 / 日志平台 mock API server
- Day12：Docker Compose
- Day13：简历 README 包装
- Day14：最终 demo 和面试讲解稿
