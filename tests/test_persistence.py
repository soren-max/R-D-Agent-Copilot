from pathlib import Path

from sqlalchemy import inspect

from app.persistence.database import DEFAULT_DATABASE_URL, init_db
from app.persistence.repositories import RunRepository


def test_database_can_initialize(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'runs.db'}"

    engine = init_db(database_url)

    inspector = inspect(engine)
    assert {"agent_runs", "agent_steps", "tool_calls"}.issubset(set(inspector.get_table_names()))


def test_create_run(tmp_path):
    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")

    run = repo.create_run(
        run_id="run-1",
        query="为什么订单接口报500？",
        route_type="complex_troubleshooting",
        answer_source="fallback",
        llm_used=False,
        status="success",
        total_latency_ms=42.5,
    )

    assert run["run_id"] == "run-1"
    assert run["query"] == "为什么订单接口报500？"
    assert run["route_type"] == "complex_troubleshooting"
    assert run["llm_used"] is False
    assert run["status"] == "success"


def test_create_step(tmp_path):
    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    repo.create_run(run_id="run-1", query="query")

    step = repo.create_step(
        run_id="run-1",
        stage="executor",
        engine="langgraph",
        input_json={"plan": ["log_tool"]},
        output_json={"tool_results": [{"tool": "log_tool"}]},
        latency_ms=10,
        status="success",
    )

    assert step["run_id"] == "run-1"
    assert step["stage"] == "executor"
    assert step["engine"] == "langgraph"
    assert step["input_json"] == {"plan": ["log_tool"]}


def test_create_tool_call(tmp_path):
    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    repo.create_run(run_id="run-1", query="query")
    step = repo.create_step(run_id="run-1", stage="executor", engine="langgraph")

    tool_call = repo.create_tool_call(
        run_id="run-1",
        step_id=step["id"],
        node="log_tool_node",
        tool_name="log_tool",
        status="success",
        source="local_sample",
        confidence=0.9,
        retry_count=1,
        latency_ms=5,
        result_json={"matched": True},
    )

    assert tool_call["run_id"] == "run-1"
    assert tool_call["step_id"] == step["id"]
    assert tool_call["tool_name"] == "log_tool"
    assert tool_call["retry_count"] == 1
    assert tool_call["result_json"] == {"matched": True}


def test_get_run_returns_run_with_steps_and_tool_calls(tmp_path):
    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    repo.create_run(run_id="run-1", query="query", route_type="simple_qa")
    step = repo.create_step(run_id="run-1", stage="router", engine="rule_based")
    repo.create_tool_call(run_id="run-1", step_id=step["id"], node="rag_tool_node", tool_name="rag_tool")

    run = repo.get_run("run-1")

    assert run is not None
    assert run["run_id"] == "run-1"
    assert run["steps"][0]["stage"] == "router"
    assert run["tool_calls"][0]["tool_name"] == "rag_tool"


def test_list_runs_returns_recent_runs(tmp_path):
    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    repo.create_run(run_id="run-1", query="first")
    repo.create_run(run_id="run-2", query="second")
    repo.create_run(run_id="run-3", query="third")

    runs = repo.list_runs(limit=2)

    assert [run["run_id"] for run in runs] == ["run-3", "run-2"]


def test_default_database_path_initializes_without_existing_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    repo = RunRepository()
    run = repo.create_run(run_id="default-run", query="query")

    assert DEFAULT_DATABASE_URL == "sqlite:///data/runs.db"
    assert run["run_id"] == "default-run"
    assert Path("data/runs.db").exists()


def test_persistence_does_not_require_deepseek_api(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("LLM_ENABLED", "false")

    repo = RunRepository(database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    run = repo.create_run(run_id="no-llm", query="query", llm_used=False, answer_source="fallback")

    assert run["llm_used"] is False
    assert run["answer_source"] == "fallback"
