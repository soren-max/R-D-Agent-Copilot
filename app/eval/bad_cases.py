"""Stable bad case replay artifact helpers for local evaluation scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BAD_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "reports" / "bad_cases.json"
BAD_CASE_KEYS = ("rag_failed_cases", "planning_failed_cases")


def load_bad_case_replay(path: Path = BAD_CASES_PATH) -> dict[str, list[dict[str, Any]]]:
    """Load bad case replay data with a stable two-section structure."""

    if not path.exists():
        return {key: [] for key in BAD_CASE_KEYS}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {key: [] for key in BAD_CASE_KEYS}
    return {
        key: list(raw.get(key) or [])
        for key in BAD_CASE_KEYS
    }


def write_bad_case_replay(
    *,
    rag_failed_cases: list[dict[str, Any]] | None = None,
    planning_failed_cases: list[dict[str, Any]] | None = None,
    path: Path = BAD_CASES_PATH,
) -> dict[str, list[dict[str, Any]]]:
    """Merge one evaluation script's failures into the shared replay file."""

    replay = load_bad_case_replay(path)
    if rag_failed_cases is not None:
        replay["rag_failed_cases"] = rag_failed_cases
    if planning_failed_cases is not None:
        replay["planning_failed_cases"] = planning_failed_cases
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(replay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return replay
