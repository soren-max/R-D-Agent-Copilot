from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.chat import chat_endpoint
from app.core.models import ChatRequest, ToolCallRecord
from app.resume import CheckpointStore, ResumeService, RunCheckpoint, check_checkpoint_drift
from main import app


def _checkpoint(**overrides):
    data = {
        "run_id": "run-1",
        "query": "为什么订单接口报500？",
        "route": {"type": "complex_troubleshooting"},
        "plan": {
            "plan_type": "troubleshooting_plan",
            "task_type": "log_analysis",
            "steps": [
                {"id": 1, "action": "query_logs", "tool": "log_tool", "description": "查日志"},
                {"id": 2, "action": "retrieve_knowledge", "tool": "rag_retriever", "description": "查知识库"},
            ],
        },
        "completed_steps": [1],
        "pending_steps": [2],
        "tool_evidence_summary": "log evidence",
        "rag_evidence_summary": "",
        "context_metadata": {"total_chars_after": 100},
        "status": "resumable",
    }
    data.update(overrides)
    return RunCheckpoint(**data)


def test_can_create_run_checkpoint():
    checkpoint = _checkpoint()

    assert checkpoint.run_id == "run-1"
    assert checkpoint.completed_steps == [1]
    assert checkpoint.pending_steps == [2]


def test_checkpoint_store_save_get_list_latest(tmp_path):
    store = CheckpointStore(tmp_path / "checkpoints.json")
    first = _checkpoint(run_id="run-1", status="completed", pending_steps=[])
    second = _checkpoint(run_id="run-2", status="resumable", pending_steps=[2])

    store.save(first)
    store.save(second)

    assert store.get("run-1").status == "completed"
    assert [item.run_id for item in store.list_recent(limit=2)] == ["run-2", "run-1"]
    assert store.latest_resumable().run_id == "run-2"
    assert store.update_status("run-2", "completed").status == "completed"


def test_chat_run_writes_completed_checkpoint(monkeypatch, tmp_path):
    checkpoint_file = tmp_path / "checkpoints.json"
    monkeypatch.setenv("CHECKPOINT_FILE", str(checkpoint_file))
    monkeypatch.setenv("INCIDENT_MEMORY_FILE", str(tmp_path / "memory.json"))
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    checkpoint = CheckpointStore(checkpoint_file).get(data["trace"]["trace_id"])
    synthesizer_step = [step for step in data["trace"]["steps"] if step["stage"] == "synthesizer"][0]

    assert checkpoint is not None
    assert checkpoint.status == "completed"
    assert checkpoint.pending_steps == []
    assert checkpoint.context_metadata
    assert synthesizer_step["checkpoint_created"] is True


def test_resumable_checkpoint_can_save_last_error(tmp_path):
    store = CheckpointStore(tmp_path / "checkpoints.json")
    checkpoint = _checkpoint(status="resumable", last_error="log_tool:file_not_found")

    store.save(checkpoint)

    saved = store.get("run-1")
    assert saved.status == "resumable"
    assert saved.last_error == "log_tool:file_not_found"


class FakeExecutor:
    def __init__(self):
        self.executed_step_ids = []

    def execute(self, query, plan):
        self.executed_step_ids = [step.id for step in plan.steps]
        return [
            ToolCallRecord(
                step_id=step.id,
                action=step.action,
                node="fake_node",
                tool=step.tool,
                tool_name=step.tool,
                description=step.description,
                result="ok",
                confidence=0.8,
                source="unit_test",
                status="success",
            )
            for step in plan.steps
        ]


def test_resume_by_run_id_does_not_repeat_completed_steps(tmp_path):
    store = CheckpointStore(tmp_path / "checkpoints.json")
    store.save(_checkpoint(completed_steps=[1], pending_steps=[2]))
    executor = FakeExecutor()

    result = ResumeService(store=store, executor=executor).resume_by_run_id("run-1")

    assert executor.executed_step_ids == [2]
    assert result["status"] == "completed"
    assert result["resumed_completed_steps_count"] == 2
    assert result["trace_events"][0]["event"] == "resume_started"
    assert result["trace_events"][-1]["event"] == "resume_completed"


def test_pending_steps_empty_returns_already_completed():
    checkpoint = _checkpoint(completed_steps=[1, 2], pending_steps=[], status="completed")

    result = check_checkpoint_drift(checkpoint)

    assert result.status == "already_completed"


def test_old_checkpoint_is_stale():
    old_time = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    checkpoint = _checkpoint(updated_at=old_time)

    result = check_checkpoint_drift(checkpoint)

    assert result.status == "stale_checkpoint"


def test_get_run_checkpoint_endpoint(monkeypatch, tmp_path):
    checkpoint_file = tmp_path / "checkpoints.json"
    monkeypatch.setenv("CHECKPOINT_FILE", str(checkpoint_file))
    CheckpointStore(checkpoint_file).save(_checkpoint(run_id="api-run"))

    response = TestClient(app).get("/runs/api-run/checkpoint")

    assert response.status_code == 200
    assert response.json()["checkpoint"]["run_id"] == "api-run"


def test_continue_run_endpoint_resumes_checkpoint(monkeypatch, tmp_path):
    checkpoint_file = tmp_path / "checkpoints.json"
    monkeypatch.setenv("CHECKPOINT_FILE", str(checkpoint_file))
    CheckpointStore(checkpoint_file).save(_checkpoint(run_id="api-run"))

    response = TestClient(app).post("/runs/api-run/continue")

    assert response.status_code == 200
    assert response.json()["resume_from_run_id"] == "api-run"
    assert response.json()["trace_events"][0]["event"] == "resume_started"


def test_llm_disabled_full_chain_checkpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("CHECKPOINT_FILE", str(tmp_path / "checkpoints.json"))
    monkeypatch.setenv("INCIDENT_MEMORY_FILE", str(tmp_path / "memory.json"))
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()

    assert data["answer_source"] == "fallback"
    assert CheckpointStore(tmp_path / "checkpoints.json").get(data["trace"]["trace_id"]).status == "completed"
