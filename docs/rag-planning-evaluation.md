# RAG and Planning Evaluation

This project keeps evaluation local and deterministic. The goal is to show whether the current Agent Harness can repeatedly retrieve expected evidence and produce expected Router / Planner outputs without using DeepSeek or any external API.

## Scope

The PR2 evaluation layer covers two surfaces:

- RAG retrieval quality against Markdown files in `data/docs/`.
- Planning quality for the deterministic `IntentRouter` and `Planner`.

It does not execute LangGraph, call tools, call DeepSeek, connect a vector database, or connect real Git / log / config systems.

## RAG Eval Set

Cases live in:

```text
eval/rag_eval_cases.jsonl
```

Each case records:

```text
id
query
expected_sources
expected_keywords
expected_doc_type
expected_grounding_status
```

The case set covers configuration center concepts, config hot update, order-service 500, payment timeout, retry settings, log fields, and troubleshooting runbook steps.

Run:

```bash
python scripts/eval_rag.py
```

Outputs:

```text
data/reports/rag_eval_result.json
data/reports/rag_eval_report.md
data/reports/rag_eval_failed_cases.json
data/reports/bad_cases.json
```

Metrics:

- `Recall@3`: whether an expected source appears in the top 3 documents.
- `Recall@5`: whether an expected source appears in the top 5 documents.
- `Precision@3`: relevant retrieved documents in the top 3 divided by retrieved top-3 count.
- `MRR`: reciprocal rank of the first expected source.
- `Hit Rate`: full case pass rate across source, keywords, doc type, and grounding status.
- `grounding_pass_rate`: whether the retriever grounding status matches the expected status.
- `average_latency_ms`: local retrieval latency measured by the script.

## Planning Eval Set

Cases live in:

```text
eval/planning_eval_cases.jsonl
```

Each case records:

```text
id
query
expected_route
expected_tools
expected_step_keywords
```

The case set covers simple QA, log analysis, config diff, Git change analysis, deployment issues, and one intentionally strict complex query that is useful for bad case replay if the current Router classifies it as procedural QA.

Run:

```bash
python scripts/eval_planning.py
```

Outputs:

```text
data/reports/planning_eval_result.json
data/reports/planning_eval_report.md
data/reports/bad_cases.json
```

Metrics:

- `route_accuracy`: percentage of cases where Router output matches `expected_route`.
- `tool_selection_accuracy`: percentage of cases where Planner tools exactly match expected tools.
- `step_coverage`: average keyword coverage across generated plan steps.
- `missing_tool_cases`: cases where expected tools are absent.
- `bad_cases`: cases with route mismatch, tool mismatch, or incomplete step coverage.

## Bad Case Replay

Both scripts merge failures into one stable file:

```json
{
  "rag_failed_cases": [],
  "planning_failed_cases": []
}
```

This file is meant for regression review. If a future Router, Planner, or RAG change fixes a failure, rerun the scripts and compare the failed case lists. The scripts never edit Router / Planner logic themselves.

## Interview Demo Use

A concise interview explanation:

```text
This project is not only a one-shot Agent demo. I added local RAG and Planning evaluation scripts. RAG evaluation checks expected source recall, keyword evidence, doc type, grounding status, and latency. Planning evaluation checks whether the deterministic Router and Planner choose the expected route, tools, and step coverage. Failed cases are written into a stable bad_cases.json file so regressions can be replayed instead of discussed by memory.
```

## Limits

The metrics are local harness metrics only. They depend on the small sample knowledge base and deterministic Router / Planner rules. They do not claim production recall, online latency, or real enterprise system correctness.
