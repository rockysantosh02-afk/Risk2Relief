"""SQLAlchemy 2.x persistence models for Simulation Runs and Safety Events."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class SimulationRun(Base, TimestampMixin):
    """Execution record for digital-twin physics & structural risk simulations."""

    __tablename__ = "simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("simulation_scenarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    step_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    peak_risk_level: Mapped[str] = mapped_column(String(32), default="LOW", nullable=False, index=True)
    peak_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_risk_level: Mapped[str] = mapped_column(String(32), default="LOW", nullable=False)
    final_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    worst_stability_status: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    summary_metrics_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    step_results_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building")
    safety_events: Mapped[List["SafetyEvent"]] = relationship(
        "SafetyEvent", back_populates="simulation_run", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_simulation_runs_bld_risk", "building_id", "peak_risk_level"),
        Index("ix_simulation_runs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SimulationRun(id={self.id}, scenario='{self.scenario_type}', risk='{self.peak_risk_level}')>"


class SafetyEvent(Base, TimestampMixin):
    """Safety event or threshold trip logged during simulations or telemetry monitoring."""

    __tablename__ = "safety_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    simulation_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), default="WARNING", nullable=False, index=True)
    trigger_source: Mapped[str] = mapped_column(String(64), default="SIMULATION_ENGINE", nullable=False)
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    building: Mapped["Building"] = relationship("Building")
    simulation_run: Mapped[Optional["SimulationRun"]] = relationship("SimulationRun", back_populates="safety_events")

    __table_args__ = (
        Index("ix_safety_events_bld_sev", "building_id", "severity"),
    )

    def __repr__(self) -> str:
        return f"<SafetyEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"
