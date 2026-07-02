from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.rag.evaluation import evaluate_cases, load_eval_cases

CASES_PATH = ROOT / "eval" / "rag_v030_eval_cases.jsonl"


def main() -> None:
    cases = load_eval_cases(CASES_PATH)
    metrics = evaluate_cases(cases, top_k=5, retrieval_type="hybrid", baseline_retrieval_type="keyword")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
