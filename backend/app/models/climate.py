"""Climate domain SQLAlchemy 2.x models for Risk2Relief.

Defines ClimateSource, ClimateObservation, and ClimateEvent.
Enforces multi-source provenance tracking, source independence grouping, and validation metadata.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    Uuid,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ClimateSource(Base, TimestampMixin):
    """External or virtual climate data provider instance."""

    __tablename__ = "climate_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_identifier: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g., SRC-SAT-001, SRC-GROUND-002, SRC-IOT-003
    provider_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )  # e.g., Copernicus_EU, IMD_Ground_Network, Community_IoT
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # SATELLITE, GROUND_STATION, IOT_SENSOR, WEATHER_API, SIMULATOR
    source_family: Mapped[str] = mapped_column(
        String(64), default="GENERIC", nullable=False
    )  # SATELLITE_RADAR, TIPPING_BUCKET_GAUGE, CAPACITIVE_SENSOR, REANALYSIS_MODEL
    independence_group: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Crucial for anti-correlation: GROUP_COPERNICUS, GROUP_IMD, GROUP_IOT
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ONLINE", nullable=False
    )  # ONLINE, DEGRADED, OFFLINE, CALIBRATING
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    observations: Mapped[List["ClimateObservation"]] = relationship(
        "ClimateObservation", back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_climate_sources_type_group", "source_type", "independence_group"),
    )

    def __repr__(self) -> str:
        return f"<ClimateSource(id={self.id}, identifier='{self.source_identifier}', group='{self.independence_group}')>"


class ClimateObservation(Base, TimestampMixin):
    """Discrete multi-source climate telemetry observation with validation and anomaly grading."""

    __tablename__ = "climate_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("climate_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Reading idempotency token (e.g. OBS-2026-FLOOD-01-A)
    event_identifier: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Associated climate event cycle (e.g. EVT-2026-FLOOD-001)
    metric: Mapped[str] = mapped_column(
        String(64), default="rainfall_24h", nullable=False, index=True
    )  # rainfall_24h, temperature_max, wind_gust_kmh, soil_moisture_pct
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="mm", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality: Mapped[str] = mapped_column(
        String(32), default="VALID", nullable=False, index=True
    )  # VALID, DEGRADED, SUSPECT, INVALID, STALE
    validation_status: Mapped[str] = mapped_column(
        String(32), default="PASSED", nullable=False, index=True
    )  # PASSED, REJECTED, FLAGGED
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    source: Mapped["ClimateSource"] = relationship("ClimateSource", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("source_id", "event_id", name="uq_climate_source_event_id"),
        Index("ix_obs_event_metric_ts", "event_identifier", "metric", "timestamp"),
        Index("ix_obs_source_quality", "source_id", "quality"),
    )

    def __repr__(self) -> str:
        return f"<ClimateObservation(source='{self.source_id}', metric='{self.metric}', value={self.value} {self.unit}, quality='{self.quality}')>"


class ClimateEvent(Base, TimestampMixin):
    """Aggregated geographical climate event being evaluated for parametric insurance."""

    __tablename__ = "climate_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_identifier: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # e.g. EVT-2026-FLOOD-001
    event_type: Mapped[str] = mapped_column(
        String(64), default="FLASH_FLOOD", nullable=False, index=True
    )  # FLASH_FLOOD, EXTREME_RAINFALL, HEATWAVE, DROUGHT, CYCLONE
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="MONITORED", nullable=False, index=True
    )  # MONITORED, TRIGGERED, SETTLED, CONSENSUS_FAILED, RESOLVED
    severity: Mapped[str] = mapped_column(
        String(32), default="MEDIUM", nullable=False, index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    description: Mapped[str] = mapped_column(Text, nullable=False)
    consensus_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consensus_unit: Mapped[str] = mapped_column(String(32), default="mm", nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        Index("ix_climate_events_status_type", "status", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<ClimateEvent(identifier='{self.event_identifier}', type='{self.event_type}', status='{self.status}')>"
