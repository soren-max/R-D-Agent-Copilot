"""Benchmark fixed demo cases against a local /chat endpoint."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = ROOT / "data" / "reports" / "benchmark_result.json"
DEFAULT_OUTPUT_MD = ROOT / "data" / "reports" / "benchmark_report.md"

DEMO_CASES = [
    {
        "id": "simple_qa",
        "name": "Simple QA - Config Center",
        "query": "什么是配置中心？",
    },
    {
        "id": "complex_troubleshooting",
        "name": "Complex Troubleshooting - Order 500",
        "query": "为什么订单接口报500？配置改了但没有生效，应该怎么排查？",
    },
    {
        "id": "insufficient_evidence",
        "name": "Insufficient Evidence",
        "query": "项目里没有覆盖的某个未知系统故障应该怎么处理？",
    },
]


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    rank = (len(ordered) - 1) * percent
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def post_chat(base_url: str, query: str, timeout: int = 60) -> tuple[dict[str, Any] | None, int | None, str]:
    payload = json.dumps({"query": query}, ensure_ascii=False).encode("utf-8")
    url = f"{base_url.rstrip('/')}/chat"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        opener = request.build_opener(request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body), resp.status, ""
    except error.HTTPError as exc:
        return None, exc.code, f"http_error:{exc.code}"
    except (error.URLError, TimeoutError, ConnectionError) as exc:
        return None, None, f"connection_error:{type(exc).__name__}"
    except json.JSONDecodeError:
        return None, None, "invalid_json_response"


def trace_stage(response: dict[str, Any], stage: str) -> dict[str, Any]:
    for step in response.get("trace", {}).get("steps", []) or []:
        if step.get("stage") == stage:
            return step
    return {}


def extract_tool_names(response: dict[str, Any]) -> list[str]:
    return [
        str(result.get("tool_name") or result.get("tool") or "")
        for result in response.get("tool_results", []) or []
        if result.get("tool_name") or result.get("tool")
    ]


def extract_skipped_nodes(response: dict[str, Any]) -> list[str]:
    executor = trace_stage(response, "executor")
    return [
        str(node.get("tool_name") or node.get("node") or "")
        for node in executor.get("skipped_nodes", []) or []
        if node.get("tool_name") or node.get("node")
    ]


def extract_rag_latency(response: dict[str, Any]) -> int | None:
    executor = trace_stage(response, "executor")
    value = executor.get("retrieval_latency_ms")
    if isinstance(value, (int, float)):
        return int(value)
    for call in executor.get("tool_calls", []) or []:
        value = call.get("retrieval_latency_ms")
        if isinstance(value, (int, float)):
            return int(value)
    return None


def extract_grounding_status(response: dict[str, Any]) -> str:
    executor = trace_stage(response, "executor")
    if executor.get("grounding_status"):
        return str(executor["grounding_status"])
    for result in response.get("tool_results", []) or []:
        metadata = result.get("rag_metadata") or {}
        if metadata.get("grounding_status"):
            return str(metadata["grounding_status"])
    return ""


def run_once(base_url: str, case: dict[str, str], run_index: int) -> dict[str, Any]:
    started_at = time.perf_counter()
    response, status_code, error_code = post_chat(base_url, case["query"])
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

    if response is None:
        return {
            "case_id": case["id"],
            "case_name": case["name"],
            "run_index": run_index,
            "query": case["query"],
            "success": False,
            "status_code": status_code,
            "error_code": error_code,
            "latency_ms": latency_ms,
        }

    route = response.get("route") or {}
    executor = trace_stage(response, "executor")
    trace_write_latency_ms = None
    return {
        "case_id": case["id"],
        "case_name": case["name"],
        "run_index": run_index,
        "query": case["query"],
        "success": status_code == 200 and bool(response.get("answer")),
        "status_code": status_code,
        "error_code": "",
        "latency_ms": latency_ms,
        "run_id": response.get("run_id"),
        "answer_source": response.get("answer_source"),
        "llm_used": response.get("llm_used"),
        "llm_error": response.get("llm_error"),
        "route_type": route.get("type"),
        "route_intent": route.get("intent"),
        "tools": extract_tool_names(response),
        "skipped_nodes": extract_skipped_nodes(response),
        "grounding_status": extract_grounding_status(response),
        "rag_latency_ms": extract_rag_latency(response),
        "executor_latency_ms": executor.get("latency_ms") if executor else None,
        "trace_write_latency_ms": trace_write_latency_ms,
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    success_count = sum(1 for item in runs if item.get("success") is True)
    latencies = [float(item["latency_ms"]) for item in runs if item.get("success") and isinstance(item.get("latency_ms"), (int, float))]
    fallback_count = sum(1 for item in runs if item.get("answer_source") == "fallback")
    llm_used_count = sum(1 for item in runs if item.get("llm_used") is True)
    llm_disabled_count = sum(1 for item in runs if item.get("llm_error") == "llm_disabled")

    return {
        "total_requests": total,
        "success_count": success_count,
        "success_rate": round(success_count / total, 4) if total else 0.0,
        "fallback_rate": round(fallback_count / total, 4) if total else 0.0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
        "p50_latency_ms": percentile(latencies, 0.50),
        "p95_latency_ms": percentile(latencies, 0.95),
        "p99_latency_ms": percentile(latencies, 0.99),
        "rag_latency_ms": summarize_optional_metric(runs, "rag_latency_ms"),
        "executor_latency_ms": summarize_optional_metric(runs, "executor_latency_ms"),
        "trace_write_latency_ms": summarize_optional_metric(runs, "trace_write_latency_ms"),
        "llm_used_count": llm_used_count,
        "llm_disabled_count": llm_disabled_count,
    }


def summarize_optional_metric(runs: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(item[key]) for item in runs if isinstance(item.get(key), (int, float))]
    return {
        "avg": round(statistics.mean(values), 2) if values else None,
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
    }


def summarize_by_case(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in DEMO_CASES:
        case_runs = [item for item in runs if item.get("case_id") == case["id"]]
        case_summary = summarize(case_runs)
        latest_success = next((item for item in reversed(case_runs) if item.get("success")), {})
        results.append({
            "case_id": case["id"],
            "case_name": case["name"],
            "query": case["query"],
            "summary": case_summary,
            "latest_route_type": latest_success.get("route_type"),
            "latest_route_intent": latest_success.get("route_intent"),
            "latest_tools": latest_success.get("tools", []),
            "latest_skipped_nodes": latest_success.get("skipped_nodes", []),
            "latest_grounding_status": latest_success.get("grounding_status", ""),
            "latest_answer_source": latest_success.get("answer_source"),
            "latest_llm_error": latest_success.get("llm_error"),
        })
    return results


def format_value(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, float):
        return str(round(value, 4))
    return str(value)


def metric_table(summary: dict[str, Any]) -> str:
    rows = [
        ("total_requests", summary.get("total_requests")),
        ("success_count", summary.get("success_count")),
        ("success_rate", summary.get("success_rate")),
        ("fallback_rate", summary.get("fallback_rate")),
        ("avg_latency_ms", summary.get("avg_latency_ms")),
        ("p50_latency_ms", summary.get("p50_latency_ms")),
        ("p95_latency_ms", summary.get("p95_latency_ms")),
        ("p99_latency_ms", summary.get("p99_latency_ms")),
        ("rag_latency_ms.avg", (summary.get("rag_latency_ms") or {}).get("avg")),
        ("executor_latency_ms.avg", (summary.get("executor_latency_ms") or {}).get("avg")),
        ("trace_write_latency_ms.avg", (summary.get("trace_write_latency_ms") or {}).get("avg")),
        ("llm_used_count", summary.get("llm_used_count")),
        ("llm_disabled_count", summary.get("llm_disabled_count")),
    ]
    lines = ["| Metric | Value |", "| --- | ---: |"]
    lines.extend(f"| `{name}` | {format_value(value)} |" for name, value in rows)
    return "\n".join(lines)


def build_markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Report",
        "",
        f"- Generated at: `{result['generated_at']}`",
        f"- Base URL: `{result['base_url']}`",
        f"- Runs per case: `{result['runs_per_case']}`",
        "- Scope: local demo benchmark only. These numbers do not represent production performance.",
        "",
        "## Summary",
        "",
        metric_table(result["summary"]),
        "",
        "## Cases",
        "",
    ]
    for case in result["cases"]:
        lines.extend([
            f"### {case['case_name']}",
            "",
            f"- Query: `{case['query']}`",
            f"- Latest route: `{format_value(case.get('latest_route_type'))}` / `{format_value(case.get('latest_route_intent'))}`",
            f"- Latest tools: `{', '.join(case.get('latest_tools') or []) or 'N/A'}`",
            f"- Latest skipped nodes: `{', '.join(case.get('latest_skipped_nodes') or []) or 'N/A'}`",
            f"- Latest grounding status: `{format_value(case.get('latest_grounding_status'))}`",
            f"- Latest answer source: `{format_value(case.get('latest_answer_source'))}`",
            f"- Latest LLM error: `{format_value(case.get('latest_llm_error'))}`",
            "",
            metric_table(case["summary"]),
            "",
        ])
    lines.extend([
        "## Notes",
        "",
        "- `rag_latency_ms`, `executor_latency_ms`, and `trace_write_latency_ms` are reported only when present in the `/chat` response or trace.",
        "- `N/A` means the benchmark script did not receive that field from the current response schema.",
        "- Default local runs usually use fallback because `LLM_ENABLED=false`.",
        "",
    ])
    return "\n".join(lines)


def run_benchmark(base_url: str, runs_per_case: int) -> dict[str, Any]:
    raw_runs: list[dict[str, Any]] = []
    for case in DEMO_CASES:
        for run_index in range(1, runs_per_case + 1):
            raw_runs.append(run_once(base_url, case, run_index))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url.rstrip("/"),
        "runs_per_case": runs_per_case,
        "summary": summarize(raw_runs),
        "cases": summarize_by_case(raw_runs),
        "raw_runs": raw_runs,
    }


def write_reports(result: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(build_markdown_report(result), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark fixed demo cases against POST /chat.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runs = max(1, args.runs)
    result = run_benchmark(args.base_url, runs)
    write_reports(result, Path(args.output_json), Path(args.output_md))

    if result["summary"]["success_count"] == 0:
        print(
            "Benchmark could not reach the local backend. "
            f"Start it with: uvicorn main:app --reload --port 8000\n"
            f"Reports were still written to {args.output_json} and {args.output_md}."
        )
        return 1

    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
