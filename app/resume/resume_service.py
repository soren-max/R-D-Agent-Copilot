"""Resume service built on existing Executor behavior."""

from __future__ import annotations

from typing import Any

from app.agent.executor import Executor
from app.core.logging import log_event
from app.core.models import Plan
from app.resume.checkpoint_store import CheckpointStore
from app.resume.drift import check_checkpoint_drift


class ResumeService:
    """Continue a checkpoint by executing only pending plan steps."""

    def __init__(
        self,
        store: CheckpointStore | None = None,
        executor: Executor | None = None,
    ) -> None:
        self.store = store or CheckpointStore()
        self.executor = executor or Executor()

    def resume_by_run_id(self, run_id: str) -> dict[str, Any]:
        checkpoint = self.store.get(run_id)
        if checkpoint is None:
            log_event(
                event="resume_checkpoint_not_found",
                stage="resume",
                error_code="CHECKPOINT_NOT_FOUND",
                message=run_id,
            )
            return {
                "status": "not_found",
                "resume_reason": "checkpoint_not_found",
                "trace_events": [],
            }

        drift = check_checkpoint_drift(checkpoint)
        if drift.status != "resumable":
            log_event(event="resume_skipped", stage="resume", run_id=checkpoint.run_id, message=drift.reason)
            return {
                "status": drift.status,
                "resume_reason": drift.reason,
                "checkpoint": checkpoint.model_dump(),
                "trace_events": [],
            }

        trace_events = [{
            "event": "resume_started",
            "resume_from_run_id": checkpoint.run_id,
            "completed_steps_count": len(checkpoint.completed_steps),
            "pending_steps_count": len(checkpoint.pending_steps),
        }]
        log_event(event="resume_started", stage="resume", run_id=checkpoint.run_id, message="Resume started")
        pending_plan = self._pending_plan(checkpoint.plan, checkpoint.pending_steps)
        results = self.executor.execute(checkpoint.query, pending_plan)
        completed_now = [result.step_id for result in results if result.status in {"success", "partial_success"}]
        completed_steps = sorted(set(checkpoint.completed_steps + completed_now))
        all_step_ids = [step.get("id") for step in checkpoint.plan.get("steps", []) if step.get("id") is not None]
        checkpoint.completed_steps = completed_steps
        checkpoint.pending_steps = [step_id for step_id in all_step_ids if step_id not in completed_steps]
        checkpoint.status = "completed" if not checkpoint.pending_steps else "resumable"
        if any(result.status == "failed" for result in results):
            checkpoint.status = "resumable"
            checkpoint.last_error = ";".join(result.error for result in results if result.error)
        self.store.save(checkpoint)
        log_event(event="resume_completed", stage="resume", run_id=checkpoint.run_id, message=checkpoint.status)
        trace_events.append({
            "event": "resume_completed",
            "resume_from_run_id": checkpoint.run_id,
            "completed_steps_count": len(checkpoint.completed_steps),
            "pending_steps_count": len(checkpoint.pending_steps),
        })
        return {
            "status": checkpoint.status,
            "resume_reason": "pending_steps_executed",
            "resume_from_run_id": checkpoint.run_id,
            "resumed_completed_steps_count": len(checkpoint.completed_steps),
            "resumed_pending_steps_count": len(checkpoint.pending_steps),
            "tool_results": [result.model_dump() for result in results],
            "checkpoint": checkpoint.model_dump(),
            "trace_events": trace_events,
        }

    def resume_latest(self) -> dict[str, Any]:
        checkpoint = self.store.latest_resumable()
        if checkpoint is None:
            log_event(
                event="resume_checkpoint_not_found",
                stage="resume",
                error_code="CHECKPOINT_NOT_FOUND",
                message="no_resumable_checkpoint",
            )
            return {"status": "not_found", "resume_reason": "no_resumable_checkpoint", "trace_events": []}
        return self.resume_by_run_id(checkpoint.run_id)

    def _pending_plan(self, plan: dict[str, Any], pending_steps: list[int]) -> Plan:
        pending = [
            step for step in plan.get("steps", [])
            if step.get("id") in set(pending_steps)
        ]
        return Plan(
            plan_type=plan.get("plan_type", "troubleshooting_plan"),
            task_type=plan.get("task_type", plan.get("plan_type", "troubleshooting_plan")),
            steps=pending,
        )
