# Final Project Summary

## 项目定位

R-D-Agent-Copilot 是一个 R&D Troubleshooting Agent Harness，用于演示研发排障 Agent 的工程化主链路、证据治理、可恢复执行和可解释评测。它不是生产日志平台或真实配置中心，而是一个可运行、可测试、可追踪、默认无需真实 LLM API Key 的 backend MVP。

## 主链路

```text
User Query
-> Router
-> Planner
-> LangGraph Executor
-> Tool Gateway
-> Tools/RAG
-> Trace
-> Context Manager
-> Answer Synthesizer
-> Evaluation v2
-> Evidence Chain
```

DeepSeek / OpenAI-compatible LLM 只允许用于最终 Answer Synthesizer，不能控制 Router、Planner、工具选择、Memory freshness 或 Resume 判断。

## 已完成能力

- Context Manager：把 prompt 输入升级为分层 `ContextPackage`。
- Tool Gateway：把 log/config/git/rag 工具调用收口到统一边界。
- Incident Memory：让历史排障结论可召回，并以 freshness 标记约束使用范围。
- Checkpoint / Resume：让 run 状态可恢复，只恢复 pending steps。
- Evaluation v2：形成可解释指标和稳定最终报告 schema。
- Provider Governance：让最终报告可版本化、可追踪、可 fallback、可 schema 校验。
- Runtime Hardening：补齐 provider timeout、retry、fallback、circuit breaker、token/cost metrics 和限流。
- RAG Pipeline v2：补齐 layered chunking、cleaning / dedup、keyword rerank 和 precision / recall evaluation。
- Production Readiness：补齐结构化日志、统一异常返回、request_id、Docker Compose 和 release checklist。

## 核心模块

- Router：只做 deterministic 意图分类，不调用 LLM、不调用工具、不生成最终答案。
- Planner：只基于 query 和 route 创建 deterministic plan，不调用 LLM、不接受模型选择工具。
- Executor：只执行 Planner 输出的步骤，不重规划。
- Tool Gateway：统一注册、参数校验、重复调用检查、策略检查、结果包装和 trace metadata。
- RAG：只做本地知识库检索，不生成最终答案。
- Context Manager：把 system_prefix、current_query、route_plan、tool_evidence、rag_evidence、incident_memory、run_history 组织为 ContextPackage，并记录压缩 metadata。
- Incident Memory：把历史排障结论沉淀为结构化参考，带 freshness 状态，不替代当前 evidence。
- Checkpoint / Resume：保存 run 状态，只恢复 pending steps，不让 LLM 判断恢复点。
- Answer Synthesizer：基于已有 evidence 生成最终中文报告，支持 prompt version、provider metadata、schema validation 和 fallback。
- Evaluation v2：按 Context、Tool、RAG、Memory、Resume、Evidence、Provider 拆分指标。
- Runtime Hardening：治理 provider timeout、retry、fallback、circuit breaker、token/cost metrics 和限流。
- RAG Pipeline v2：按文档类型分层切片，清洗去重，规则重排，并输出 precision / recall / source coverage 指标。
- Production Readiness：结构化日志、统一错误返回、`request_id` 透传、Docker Compose 和 release checklist。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

默认 `.env.example` 保持：

```bash
DEEPSEEK_API_KEY=
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
LLM_ENABLED=false
```

## 跑测试

```bash
pytest -q
```

本阶段重点测试：

```bash
pytest tests/test_prompt_provider_governance.py -q
pytest tests/test_evaluation_v2.py -q
```

## Demo 演示步骤

1. 启动 API。
2. 调用 `POST /chat`，输入“为什么订单接口报500？”。
3. 展示 Router、Planner、Executor、Tool/RAG、Synthesizer、Evaluation、Evidence trace。
4. 展示 Context metadata、Tool Gateway metadata、Incident Memory historical reference、Checkpoint 状态。
5. 展示 Answer Synthesizer 的 `provider_metadata` 和 schema-valid `parsed_output`。
6. 运行 `pytest -q` 证明默认 `LLM_ENABLED=false` 仍可运行。

## 面试讲解提纲

- 这是一个 R&D Troubleshooting Agent Harness，不是单纯 chatbot。
- 主链路保持工程边界：Router 分类、Planner 规划、Executor 执行、Tools/RAG 取证、Synthesizer 最终报告。
- LLM 只用于最终 Answer Synthesizer，不参与 Router、Planner 或工具选择。
- Context Manager 解决 prompt 堆叠问题；Tool Gateway 解决工具边界问题；Incident Memory 解决历史经验沉淀问题；Checkpoint / Resume 解决 run 可恢复问题；Evaluation v2 解决可解释评测问题。
- Prompt / Provider Governance 让最终报告可版本化、可追踪、可 fallback、可 schema 校验。
