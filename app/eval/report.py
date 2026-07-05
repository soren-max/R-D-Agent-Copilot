"""Evaluation v2 report serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path

from app.eval.schemas import EvaluationReportV2


def save_evaluation_report_v2(report: EvaluationReportV2, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def summarize_evaluation_reports_v2(reports: list[EvaluationReportV2]) -> dict[str, object]:
    total = len(reports)
    if total == 0:
        return {"run_count": 0, "average_overall": 0.0}
    return {
        "run_count": total,
        "average_overall": round(sum(report.overall for report in reports) / total, 4),
        "average_tool_success_rate": round(sum(report.tool.tool_success_rate for report in reports) / total, 4),
        "total_tool_errors": sum(report.tool.tool_error_count for report in reports),
        "total_memory_risks": sum(report.memory.memory_misused_as_current_fact_count for report in reports),
        "total_stale_checkpoints": sum(report.resume.stale_checkpoint_count for report in reports),
    }
