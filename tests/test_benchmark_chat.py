from scripts.benchmark_chat import percentile, summarize, summarize_optional_metric


def test_percentile_handles_small_samples():
    assert percentile([], 0.95) is None
    assert percentile([10.0], 0.95) == 10.0
    assert percentile([10.0, 20.0, 30.0], 0.50) == 20.0


def test_summarize_reports_na_for_missing_optional_metrics():
    runs = [
        {
            "success": True,
            "latency_ms": 100.0,
            "answer_source": "fallback",
            "llm_used": False,
            "llm_error": "llm_disabled",
        },
        {
            "success": True,
            "latency_ms": 200.0,
            "answer_source": "fallback",
            "llm_used": False,
            "llm_error": "llm_disabled",
        },
    ]

    summary = summarize(runs)

    assert summary["total_requests"] == 2
    assert summary["success_count"] == 2
    assert summary["success_rate"] == 1.0
    assert summary["fallback_rate"] == 1.0
    assert summary["avg_latency_ms"] == 150.0
    assert summary["llm_used_count"] == 0
    assert summary["llm_disabled_count"] == 2
    assert summary["trace_write_latency_ms"]["avg"] is None


def test_summarize_optional_metric_uses_only_present_values():
    summary = summarize_optional_metric(
        [
            {"executor_latency_ms": 10},
            {"executor_latency_ms": None},
            {"executor_latency_ms": 30},
        ],
        "executor_latency_ms",
    )

    assert summary["avg"] == 20.0
    assert summary["p50"] == 20.0
