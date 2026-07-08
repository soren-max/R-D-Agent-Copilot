# Benchmark Report

- Generated at: `2026-07-08T08:20:09.052372+00:00`
- Base URL: `http://127.0.0.1:8000`
- Runs per case: `3`
- Scope: local demo benchmark only. These numbers do not represent production performance.

## Summary

| Metric | Value |
| --- | ---: |
| `total_requests` | 9 |
| `success_count` | 9 |
| `success_rate` | 1.0 |
| `fallback_rate` | 1.0 |
| `avg_latency_ms` | 1137.8 |
| `p50_latency_ms` | 1106.99 |
| `p95_latency_ms` | 1231.12 |
| `p99_latency_ms` | 1253.22 |
| `rag_latency_ms.avg` | 93.89 |
| `executor_latency_ms.avg` | 278.67 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 9 |

## Cases

### Simple QA - Config Center

- Query: `什么是配置中心？`
- Latest route: `simple_qa` / `knowledge_qa`
- Latest tools: `rag_retriever`
- Latest skipped nodes: `log_tool, config_tool, git_tool`
- Latest grounding status: `grounded`
- Latest answer source: `fallback`
- Latest LLM error: `llm_disabled`

| Metric | Value |
| --- | ---: |
| `total_requests` | 3 |
| `success_count` | 3 |
| `success_rate` | 1.0 |
| `fallback_rate` | 1.0 |
| `avg_latency_ms` | 1124.41 |
| `p50_latency_ms` | 1106.99 |
| `p95_latency_ms` | 1167.02 |
| `p99_latency_ms` | 1172.36 |
| `rag_latency_ms.avg` | 94.0 |
| `executor_latency_ms.avg` | 241.33 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 3 |

### Complex Troubleshooting - Order 500

- Query: `为什么订单接口报500？配置改了但没有生效，应该怎么排查？`
- Latest route: `complex_troubleshooting` / `config_diff`
- Latest tools: `config_tool, rag_retriever`
- Latest skipped nodes: `log_tool, git_tool`
- Latest grounding status: `grounded`
- Latest answer source: `fallback`
- Latest LLM error: `llm_disabled`

| Metric | Value |
| --- | ---: |
| `total_requests` | 3 |
| `success_count` | 3 |
| `success_rate` | 1.0 |
| `fallback_rate` | 1.0 |
| `avg_latency_ms` | 1210.47 |
| `p50_latency_ms` | 1189.69 |
| `p95_latency_ms` | 1251.84 |
| `p99_latency_ms` | 1257.36 |
| `rag_latency_ms.avg` | 93.33 |
| `executor_latency_ms.avg` | 373.33 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 3 |

### Insufficient Evidence

- Query: `项目里没有覆盖的某个未知系统故障应该怎么处理？`
- Latest route: `simple_qa` / `knowledge_qa`
- Latest tools: `rag_retriever`
- Latest skipped nodes: `log_tool, config_tool, git_tool`
- Latest grounding status: `grounded`
- Latest answer source: `fallback`
- Latest LLM error: `llm_disabled`

| Metric | Value |
| --- | ---: |
| `total_requests` | 3 |
| `success_count` | 3 |
| `success_rate` | 1.0 |
| `fallback_rate` | 1.0 |
| `avg_latency_ms` | 1078.5 |
| `p50_latency_ms` | 1080.49 |
| `p95_latency_ms` | 1082.76 |
| `p99_latency_ms` | 1082.96 |
| `rag_latency_ms.avg` | 94.33 |
| `executor_latency_ms.avg` | 221.33 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 3 |

## Notes

- `rag_latency_ms`, `executor_latency_ms`, and `trace_write_latency_ms` are reported only when present in the `/chat` response or trace.
- `N/A` means the benchmark script did not receive that field from the current response schema.
- Default local runs usually use fallback because `LLM_ENABLED=false`.
