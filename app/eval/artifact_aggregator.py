"""Aggregate run artifacts into Evaluation v2 JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.eval.evaluator_v2 import EvaluationV2Evaluator
from app.eval.report import save_evaluation_report_v2, summarize_evaluation_reports_v2
from app.eval.schemas import EvaluationReportV2


class EvaluationArtifactAggregator:
    """Create and persist EvaluationReportV2 artifacts."""

    def __init__(self, artifact_dir: str | Path = "artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.evaluator = EvaluationV2Evaluator()

    def aggregate_run(self, payload: dict[str, Any], save: bool = True) -> EvaluationReportV2:
        report = self.evaluator.evaluate(payload)
        if save:
            run_id = report.run_id or "unknown"
            save_evaluation_report_v2(report, self.artifact_dir / f"evaluation-v2-{run_id}.json")
        return report

    def write_summary(self, reports: list[EvaluationReportV2]) -> dict[str, object]:
        summary = summarize_evaluation_reports_v2(reports)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        (self.artifact_dir / "evaluation-v2-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return summary
