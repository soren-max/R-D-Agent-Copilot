"""Read local evaluation reports for lightweight observability endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]

REPORTS = {
    "planning_eval": ROOT_DIR / "data" / "eval" / "planning_eval_report.md",
    "bad_case_replay": ROOT_DIR / "data" / "eval" / "bad_case_replay_report.md",
    "rag_failed_cases": ROOT_DIR / "data" / "reports" / "rag_eval_failed_cases.json",
}


def build_eval_report_summary(include_content: bool = False) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for name, path in REPORTS.items():
        exists = path.exists()
        item: dict[str, Any] = {
            "path": str(path.relative_to(ROOT_DIR)),
            "exists": exists,
        }
        if exists:
            item["size_bytes"] = path.stat().st_size
            if include_content:
                item["content"] = _read_report(path)
        reports[name] = item
    return {"reports": reports}


def _read_report(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text

