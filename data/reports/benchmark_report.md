# Benchmark Report

- Generated at: `2026-07-08T07:52:55.442935+00:00`
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
| `avg_latency_ms` | 1014.12 |
| `p50_latency_ms` | 1005.53 |
| `p95_latency_ms` | 1114.45 |
| `p99_latency_ms` | 1164.26 |
| `rag_latency_ms.avg` | 93.56 |
| `executor_latency_ms.avg` | 221.33 |
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
| `avg_latency_ms` | 1071.57 |
| `p50_latency_ms` | 1021.07 |
| `p95_latency_ms` | 1161.15 |
| `p99_latency_ms` | 1173.6 |
| `rag_latency_ms.avg` | 94.0 |
| `executor_latency_ms.avg` | 230.0 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 3 |

### Complex Troubleshooting - Order 500

- Query: `为什么订单接口报500？配置改了但没有生效，应该怎么排查？`
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
| `avg_latency_ms` | 978.64 |
| `p50_latency_ms` | 992.61 |
| `p95_latency_ms` | 1016.05 |
| `p99_latency_ms` | 1018.13 |
| `rag_latency_ms.avg` | 93.33 |
| `executor_latency_ms.avg` | 229.33 |
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
| `avg_latency_ms` | 992.14 |
| `p50_latency_ms` | 986.83 |
| `p95_latency_ms` | 1003.66 |
| `p99_latency_ms` | 1005.16 |
| `rag_latency_ms.avg` | 93.33 |
| `executor_latency_ms.avg` | 204.67 |
| `trace_write_latency_ms.avg` | N/A |
| `llm_used_count` | 0 |
| `llm_disabled_count` | 3 |

## Notes

- `rag_latency_ms`, `executor_latency_ms`, and `trace_write_latency_ms` are reported only when present in the `/chat` response or trace.
- `N/A` means the benchmark script did not receive that field from the current response schema.
- Default local runs usually use fallback because `LLM_ENABLED=false`.
