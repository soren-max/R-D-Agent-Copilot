"""Run Week1 local demo requests against a running /chat server."""

from __future__ import annotations

import json
from urllib import error, request


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


def print_case(name: str, query: str, data: dict) -> None:
    tool_names = [
        result.get("tool_name") or result.get("tool")
        for result in data.get("tool_results", [])
    ]
    print(f"\n=== {name}: {query} ===")
    print("answer:")
    print(data.get("answer", ""))
    print("\nanswer_source:", data.get("answer_source"))
    print("route.type:", data.get("route", {}).get("type"))
    print("tool_names:", tool_names)
    print("trace.executor.engine:", trace_stage(data, "executor").get("engine"))
    print("trace.synthesizer.engine:", trace_stage(data, "synthesizer").get("engine"))


def main() -> None:
    try:
        for name, query in CASES:
            print_case(name, query, post_chat(query))
    except error.URLError as exc:
        print("Local server is not reachable.")
        print("Start it with: uvicorn main:app --reload")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
