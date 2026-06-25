"""Run Day5 LangGraph demo requests against a local /chat server."""

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
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def executor_trace(data: dict) -> dict:
    for step in data.get("trace", {}).get("steps", []):
        if step.get("stage") == "executor":
            return step
    return {}


def main() -> None:
    for name, query in CASES:
        data = post_chat(query)
        print(f"\n=== {name}: {query} ===")
        print("answer:")
        print(data.get("answer", ""))
        print("\nroute:")
        print(json.dumps(data.get("route", {}), ensure_ascii=False, indent=2))
        print("\ntool_results:")
        print(json.dumps(data.get("tool_results", []), ensure_ascii=False, indent=2))
        print("\ntrace.executor:")
        print(json.dumps(executor_trace(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
