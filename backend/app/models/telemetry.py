"""Telemetry domain SQLAlchemy 2.x models.

Defines TelemetrySource, TelemetryBatch, TelemetryReading, and TelemetryQualityRecord.
Includes optimized composite indexes for time-series aggregation and duplicate detection.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Float,
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


class TelemetrySource(Base, TimestampMixin):
    """Physical or virtual sensor reporting telemetry into the platform."""

    __tablename__ = "telemetry_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_identifier: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # STRAIN_GAUGE, ACCELEROMETER, TEMPERATURE, LOAD_SENSOR, INCLINOMETER, PRESSURE, AIR_QUALITY, SIMULATOR
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    structural_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("structural_nodes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ONLINE", nullable=False
    )  # ONLINE, OFFLINE, CALIBRATING, FAULT
    reliability_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sampling_rate_hz: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="telemetry_sources")
    readings: Mapped[List["TelemetryReading"]] = relationship(
        "TelemetryReading", back_populates="source", cascade="all, delete-orphan"
    )
    quality_records: Mapped[List["TelemetryQualityRecord"]] = relationship(
        "TelemetryQualityRecord", back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_telemetry_sources_bld_type", "building_id", "source_type"),
    )

    def __repr__(self) -> str:
        return f"<TelemetrySource(id={self.id}, identifier='{self.source_identifier}', type='{self.source_type}')>"


class TelemetryBatch(Base, TimestampMixin):
    """Container for high-throughput batch ingestion of sensor packets."""

    __tablename__ = "telemetry_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_identifier: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    readings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="INGESTED", nullable=False
    )  # INGESTED, PROCESSED, ANOMALOUS, PARTIAL
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processing_duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    readings: Mapped[List["TelemetryReading"]] = relationship(
        "TelemetryReading", back_populates="batch"
    )

    def __repr__(self) -> str:
        return f"<TelemetryBatch(id={self.id}, batch_identifier='{self.batch_identifier}', count={self.readings_count})>"


class TelemetryReading(Base, TimestampMixin):
    """Discrete sensor observation with quality classification and idempotency."""

    __tablename__ = "telemetry_readings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telemetry_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telemetry_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metric: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # strain_microstrain, vibration_hz, temperature_c, load_kn, deflection_mm
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Idempotency identifier
    quality: Mapped[str] = mapped_column(
        String(32), default="VALID", nullable=False, index=True
    )  # VALID, INVALID, STALE, DUPLICATE, ANOMALOUS, MISSING
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    source: Mapped["TelemetrySource"] = relationship("TelemetrySource", back_populates="readings")
    batch: Mapped[Optional["TelemetryBatch"]] = relationship("TelemetryBatch", back_populates="readings")
    quality_records: Mapped[List["TelemetryQualityRecord"]] = relationship(
        "TelemetryQualityRecord", back_populates="reading"
    )

    __table_args__ = (
        UniqueConstraint("source_id", "event_id", name="uq_source_event_id"),
        Index("ix_readings_bld_metric_ts", "building_id", "metric", "timestamp"),
        Index("ix_readings_source_ts", "source_id", "timestamp"),
        Index("ix_readings_quality_ts", "quality", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<TelemetryReading(id={self.id}, metric='{self.metric}', value={self.value}, quality='{self.quality}')>"


class TelemetryQualityRecord(Base, TimestampMixin):
    """Audit log of telemetry validation failures and anomalies."""

    __tablename__ = "telemetry_quality_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reading_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telemetry_readings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telemetry_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flagged_quality: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # INVALID, STALE, DUPLICATE, ANOMALOUS, MISSING
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    reading: Mapped[Optional["TelemetryReading"]] = relationship(
        "TelemetryReading", back_populates="quality_records"
    )
    source: Mapped["TelemetrySource"] = relationship("TelemetrySource", back_populates="quality_records")

    def __repr__(self) -> str:
        return f"<TelemetryQualityRecord(id={self.id}, quality='{self.flagged_quality}', reason='{self.reason}')>"
