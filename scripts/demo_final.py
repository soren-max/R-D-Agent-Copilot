"""Run the final demo requests against a local R&D Agent Copilot backend."""

from __future__ import annotations

import json
from urllib import error, request


API_BASE_URL = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE_URL}/chat"
CASES = [
    ("simple_qa", "什么是配置中心？"),
    ("complex_troubleshooting", "为什么订单接口报500？"),
]


def post_chat(query: str) -> dict:
    payload = json.dumps({"query": query}).encode("utf-8")
    req = request.Request(
        CHAT_URL,
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


def planner_steps(data: dict) -> list[str]:
    steps = data.get("plan", {}).get("steps", [])
    result = []
    for step in steps:
        step_id = step.get("id")
        tool = step.get("tool")
        action = step.get("action")
        description = step.get("description")
        result.append(f"{step_id}. {action} [{tool}] - {description}")
    return result


def tool_names(data: dict) -> list[str]:
    return [
        result.get("tool_name") or result.get("tool") or "unknown_tool"
        for result in data.get("tool_results", [])
    ]


def print_case(name: str, query: str, data: dict) -> None:
    print(f"\n=== {name}: {query} ===")
    print("run_id:", data.get("run_id"))
    print("answer:")
    print(data.get("answer", ""))
    print("\nanswer_source:", data.get("answer_source"))
    print("route.type:", data.get("route", {}).get("type"))
    print("planner steps:")
    for step in planner_steps(data):
        print(f"- {step}")
    print("tool names:", tool_names(data))
    print("trace.executor.engine:", trace_stage(data, "executor").get("engine"))
    print("evaluation.overall_score:", (data.get("evaluation") or {}).get("overall_score"))


def main() -> None:
    try:
        for name, query in CASES:
            print_case(name, query, post_chat(query))
    except (error.URLError, TimeoutError, ConnectionError):
        print("请先启动后端：uvicorn main:app --reload")


if __name__ == "__main__":
    main()
