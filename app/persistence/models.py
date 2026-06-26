from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    route_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    total_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentStep.id",
        primaryjoin="AgentRun.run_id == AgentStep.run_id",
    )
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ToolCall.id",
        primaryjoin="AgentRun.run_id == ToolCall.run_id",
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("agent_runs.run_id"),
        index=True,
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    run: Mapped[AgentRun] = relationship(back_populates="steps")
    tool_calls: Mapped[list["ToolCall"]] = relationship(back_populates="step")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("agent_runs.run_id"),
        index=True,
        nullable=False,
    )
    step_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("agent_steps.id"),
        nullable=True,
    )
    node: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    run: Mapped[AgentRun] = relationship(back_populates="tool_calls")
    step: Mapped[AgentStep | None] = relationship(back_populates="tool_calls")
