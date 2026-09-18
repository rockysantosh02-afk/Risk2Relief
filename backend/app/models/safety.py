"""SQLAlchemy 2.x persistence models for Safety State Transitions and Incidents."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Incident(Base, TimestampMixin):
    """Auditable structural safety, telemetry, or digital-twin incident."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", nullable=False, index=True
    )  # OPEN, INVESTIGATING, MITIGATED, RESOLVED, CLOSED
    affected_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    initial_safety_state: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    escalated_safety_state: Mapped[str] = mapped_column(String(32), default="WARNING", nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    recommended_simulated_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building")
    zone: Mapped[Optional["BuildingZone"]] = relationship("BuildingZone")

    __table_args__ = (
        Index("ix_incidents_bld_status", "building_id", "status"),
        Index("ix_incidents_bld_severity", "building_id", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, code='{self.incident_code}', severity='{self.severity}', status='{self.status}')>"


class SafetyStateTransitionRecord(Base, TimestampMixin):
    """Complete audit log for deterministic safety state machine transitions."""

    __tablename__ = "safety_state_transitions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    to_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trigger_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs_snapshot_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    is_valid_transition: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    building: Mapped["Building"] = relationship("Building")

    __table_args__ = (
        Index("ix_state_transitions_bld_time", "building_id", "transitioned_at"),
    )

    def __repr__(self) -> str:
        return f"<SafetyStateTransitionRecord({self.from_state} -> {self.to_state}, reason='{self.trigger_reason}')>"
