from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.persistence.database import init_db
from app.persistence.models import AgentRun, AgentStep, ToolCall


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _run_to_dict(run: AgentRun, include_children: bool = False) -> dict[str, Any]:
    data = {
        "id": run.id,
        "run_id": run.run_id,
        "query": run.query,
        "route_type": run.route_type,
        "answer_source": run.answer_source,
        "llm_used": run.llm_used,
        "status": run.status,
        "total_latency_ms": run.total_latency_ms,
        "created_at": _serialize_datetime(run.created_at),
    }
    if include_children:
        data["steps"] = [_step_to_dict(step) for step in run.steps]
        data["tool_calls"] = [_tool_call_to_dict(tool_call) for tool_call in run.tool_calls]
    return data


def _step_to_dict(step: AgentStep) -> dict[str, Any]:
    return {
        "id": step.id,
        "run_id": step.run_id,
        "stage": step.stage,
        "engine": step.engine,
        "input_json": step.input_json,
        "output_json": step.output_json,
        "latency_ms": step.latency_ms,
        "status": step.status,
        "created_at": _serialize_datetime(step.created_at),
    }


def _tool_call_to_dict(tool_call: ToolCall) -> dict[str, Any]:
    return {
        "id": tool_call.id,
        "run_id": tool_call.run_id,
        "step_id": tool_call.step_id,
        "node": tool_call.node,
        "tool_name": tool_call.tool_name,
        "status": tool_call.status,
        "source": tool_call.source,
        "confidence": tool_call.confidence,
        "retry_count": tool_call.retry_count,
        "error": tool_call.error,
        "latency_ms": tool_call.latency_ms,
        "result_json": tool_call.result_json,
        "created_at": _serialize_datetime(tool_call.created_at),
    }


class RunRepository:
    def __init__(
        self,
        database_url: str | None = None,
        session_factory: sessionmaker | Callable[[], Session] | None = None,
    ) -> None:
        if session_factory is not None:
            self._session_factory = session_factory
            return

        engine = init_db(database_url)
        self._session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

    def create_run(
        self,
        *,
        run_id: str,
        query: str,
        route_type: str | None = None,
        answer_source: str | None = None,
        llm_used: bool = False,
        status: str = "success",
        total_latency_ms: float | None = None,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            run = AgentRun(
                run_id=run_id,
                query=query,
                route_type=route_type,
                answer_source=answer_source,
                llm_used=llm_used,
                status=status,
                total_latency_ms=total_latency_ms,
            )
            session.add(run)
            session.commit()
            return _run_to_dict(run)

    def create_step(
        self,
        *,
        run_id: str,
        stage: str,
        engine: str | None = None,
        input_json: dict | list | None = None,
        output_json: dict | list | None = None,
        latency_ms: float | None = None,
        status: str = "success",
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            step = AgentStep(
                run_id=run_id,
                stage=stage,
                engine=engine,
                input_json=input_json,
                output_json=output_json,
                latency_ms=latency_ms,
                status=status,
            )
            session.add(step)
            session.commit()
            return _step_to_dict(step)

    def create_tool_call(
        self,
        *,
        run_id: str,
        tool_name: str,
        step_id: int | None = None,
        node: str | None = None,
        status: str = "success",
        source: str | None = None,
        confidence: float | None = None,
        retry_count: int = 0,
        error: str | None = None,
        latency_ms: float | None = None,
        result_json: dict | list | None = None,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            tool_call = ToolCall(
                run_id=run_id,
                step_id=step_id,
                node=node,
                tool_name=tool_name,
                status=status,
                source=source,
                confidence=confidence,
                retry_count=retry_count,
                error=error,
                latency_ms=latency_ms,
                result_json=result_json,
            )
            session.add(tool_call)
            session.commit()
            return _tool_call_to_dict(tool_call)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            statement = (
                select(AgentRun)
                .where(AgentRun.run_id == run_id)
                .options(selectinload(AgentRun.steps), selectinload(AgentRun.tool_calls))
            )
            run = session.execute(statement).scalar_one_or_none()
            if run is None:
                return None
            return _run_to_dict(run, include_children=True)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            statement = select(AgentRun).order_by(AgentRun.created_at.desc(), AgentRun.id.desc()).limit(limit)
            runs = session.execute(statement).scalars().all()
            return [_run_to_dict(run) for run in runs]
