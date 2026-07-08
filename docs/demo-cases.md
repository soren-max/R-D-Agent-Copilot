# Demo Cases and Benchmark

This document defines the fixed interview demo path for R&D Agent Copilot. All cases use local sample data and the local `/chat` API. They are meant to prove reproducibility, not production performance.

## How To Run

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Run the benchmark:

```bash
python scripts/benchmark_chat.py --runs 3
```

Default outputs:

- `data/reports/benchmark_result.json`
- `data/reports/benchmark_report.md`

The benchmark reports only fields returned by `/chat` or trace. Missing fields are shown as `N/A`.

## Case 1: Simple QA - Config Center

- Case file: `data/demo_cases/case_simple_config_center.json`
- Input query: `什么是配置中心？`
- Expected route: `simple_qa`
- Expected plan steps: `retrieve_knowledge`
- Expected tools: `rag_retriever`
- Expected skipped nodes: `log_tool`, `config_tool`, `git_tool`
- Expected RAG source: `data/docs/config-center.md`
- Expected grounding: `grounded`
- Expected answer behavior: explain config center from local knowledge evidence.
- Expected evaluation: trace completeness and RAG relevance should be visible in the response evaluation.

Interview script:

> This case shows the lightweight knowledge QA path. Router classifies the query as `simple_qa`, Planner creates only one RAG step, and LangGraph records skipped operational tools. This proves the Agent does not call every tool blindly.

## Case 2: Complex Troubleshooting - Order 500

- Case file: `data/demo_cases/case_order_500.json`
- Input query: `为什么订单接口报500？配置改了但没有生效，应该怎么排查？`
- Expected route: `complex_troubleshooting`
- Expected plan steps: `query_logs`, `check_config`, `analyze_git_diff`, `retrieve_knowledge`
- Expected tools: `log_tool`, `config_tool`, `git_tool`, `rag_retriever`
- Expected skipped nodes: none
- Expected RAG sources: `data/docs/order-service-faq.md`, `data/docs/service-logs.md`, `data/docs/troubleshooting-guide.md`
- Expected evidence keywords: `500`, `order-service`, `payment.timeout`, `trace_id`
- Expected trace/export result: executor stage should include LangGraph engine metadata, tool calls, tool latency, RAG metadata, and fallback status.
- Expected answer behavior: produce a Chinese troubleshooting report based on local tool and RAG evidence.

Interview script:

> This is the main demo. It shows the full harness: Router detects troubleshooting intent, Planner creates deterministic steps, LangGraph executes local tools and RAG, and Trace records each node. The important point is that LLM is only the final expression layer; it does not choose tools.

## Case 3: Insufficient Evidence / Grounding Fallback

- Case file: `data/demo_cases/case_insufficient_evidence.json`
- Input query: `项目里没有覆盖的某个未知系统故障应该怎么处理？`
- Expected route: `complex_troubleshooting`
- Expected tools: `log_tool`, `config_tool`, `git_tool`, `rag_retriever`
- Expected grounding: `insufficient_evidence` or fallback when evidence is not enough.
- Expected RAG sources: no required source.
- Expected answer behavior: avoid inventing a root cause and ask for more logs, config, or documentation.
- Expected trace/export result: response should expose answer source, LLM usage state, executor metadata, and grounding status when available.

Interview script:

> This case demonstrates the project boundary. When the local evidence is insufficient, the system should not pretend it knows the root cause. It should return an evidence-insufficient fallback and make that visible in Trace.

## Benchmark Metrics

`scripts/benchmark_chat.py` records:

- `total_requests`
- `success_count`
- `success_rate`
- `fallback_rate`
- `avg_latency_ms`
- `p50_latency_ms`
- `p95_latency_ms`
- `p99_latency_ms`
- `rag_latency_ms` when available
- `executor_latency_ms` when available
- `trace_write_latency_ms` when available
- `llm_used_count`
- `llm_disabled_count`

These metrics are local demo measurements. They should not be described as production latency, capacity, or SLA.
