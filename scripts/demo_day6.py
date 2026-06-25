"""Run Day6 DeepSeek answer synthesizer demo requests against local /chat."""

from __future__ import annotations

import json
from urllib import request


API_URL = "http://127.0.0.1:8000/chat"
CASES = [
    ("simple_qa", "什么是配置中心？"),
    ("complex_troubleshooting", "为什么订单接口报500？"),
]


def post_chat(query: str) -> dict:
    payload = json.dumps({"query": query}).encode("utf-8")
    req = request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def trace_stage(data: dict, stage: str) -> dict:
    for step in data.get("trace", {}).get("steps", []):
        if step.get("stage") == stage:
            return step
    return {}


def main() -> None:
    for name, query in CASES:
        data = post_chat(query)
        print(f"\n=== {name}: {query} ===")
        print("answer:")
        print(data.get("answer", ""))
        print("\nanswer_source:", data.get("answer_source"))
        print("llm_used:", data.get("llm_used"))
        print("llm_error:", data.get("llm_error"))
        print("\ntrace.synthesizer:")
        print(json.dumps(trace_stage(data, "synthesizer"), ensure_ascii=False, indent=2))
        print("\ntrace.executor.engine:", trace_stage(data, "executor").get("engine"))


if __name__ == "__main__":
    main()
