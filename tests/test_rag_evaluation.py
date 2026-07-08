from pathlib import Path

from scripts.eval_rag import evaluate


def test_rag_evaluation_script_runs_and_writes_failed_cases():
    metrics = evaluate()

    assert set(
        [
            "total_cases",
            "Recall@3",
            "Recall@5",
            "Precision@3",
            "Hit Rate",
            "MRR",
            "grounding_pass_rate",
            "average_latency_ms",
            "failed_cases",
        ]
    ).issubset(metrics)
    assert metrics["total_cases"] >= 15
    assert 0 <= metrics["Recall@3"] <= 1
    assert 0 <= metrics["Recall@5"] <= 1
    assert 0 <= metrics["Precision@3"] <= 1
    assert 0 <= metrics["Hit Rate"] <= 1
    assert 0 <= metrics["MRR"] <= 1
    assert 0 <= metrics["grounding_pass_rate"] <= 1
    assert metrics["average_latency_ms"] >= 0
    assert Path("data/reports/rag_eval_failed_cases.json").exists()
    assert Path("data/reports/rag_eval_result.json").exists()
    assert Path("data/reports/rag_eval_report.md").exists()
