"""Configuration & simulation scenario domain SQLAlchemy 2.x models.

Defines BuildingConfiguration, GravityConfiguration, SafetyThresholdConfiguration,
EnvironmentalConfiguration, and SimulationScenario.
Enforces hard safety invariants: in-silico simulation isolation and zero hardware actuation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
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
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BuildingConfiguration(Base, TimestampMixin):
    """Operational parameters and timezones for a building."""

    __tablename__ = "building_configurations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    telemetry_buffer_size: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    alarm_notification_channels: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    config_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        UniqueConstraint("building_id", "version", name="uq_building_config_version"),
    )

    def __repr__(self) -> str:
        return f"<BuildingConfiguration(id={self.id}, building_id={self.building_id}, v={self.version})>"


class GravityConfiguration(Base, TimestampMixin):
    """Digital-twin in-silico gravitational offset simulation configuration.

    SYSTEM SAFETY BOUNDARY:
    This model configures purely mathematical simulations of load mitigation.
    Hardware actuation is permanently forbidden by system invariants.
    """

    __tablename__ = "gravity_configurations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    simulation_model: Mapped[str] = mapped_column(
        String(64), default="DISTRIBUTED_VECTOR_FIELD_V1", nullable=False
    )
    target_gravity_offset_percentage: Mapped[float] = mapped_column(
        Float, default=15.0, nullable=False
    )  # e.g. 15% virtual load mitigation
    max_compensation_kn: Mapped[float] = mapped_column(Float, default=5000.0, nullable=False)
    field_distribution_algorithm: Mapped[str] = mapped_column(
        String(64), default="OPTIMAL_SHEAR_BALANCING", nullable=False
    )
    # Hard safety invariants
    in_silico_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hardware_actuation_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    damping_factor: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    parameters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        UniqueConstraint("building_id", "version", name="uq_gravity_config_version"),
    )

    def __repr__(self) -> str:
        return f"<GravityConfiguration(id={self.id}, building_id={self.building_id}, v={self.version})>"


class SafetyThresholdConfiguration(Base, TimestampMixin):
    """Engineering thresholds for structural load warnings and interlock trips."""

    __tablename__ = "safety_threshold_configurations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    max_tensile_stress_mpa: Mapped[float] = mapped_column(Float, default=400.0, nullable=False)
    max_compressive_stress_mpa: Mapped[float] = mapped_column(Float, default=450.0, nullable=False)
    max_deflection_mm: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    max_vibration_amplitude_g: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    warning_threshold_percentage: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)
    interlock_trip_threshold_percentage: Mapped[float] = mapped_column(Float, default=90.0, nullable=False)
    auto_trip_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    interlock_action: Mapped[str] = mapped_column(
        String(64), default="SAFE_CONTAINMENT", nullable=False
    )

    def __repr__(self) -> str:
        return f"<SafetyThresholdConfiguration(id={self.id}, building_id={self.building_id})>"


class EnvironmentalConfiguration(Base, TimestampMixin):
    """Ambient environmental bounds and seismic zone properties."""

    __tablename__ = "environmental_configurations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    ambient_temp_min_c: Mapped[float] = mapped_column(Float, default=-20.0, nullable=False)
    ambient_temp_max_c: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    max_wind_speed_mps: Mapped[float] = mapped_column(Float, default=35.0, nullable=False)
    seismic_zone_code: Mapped[str] = mapped_column(String(32), default="ZONE_IV", nullable=False)
    thermal_expansion_coefficient: Mapped[float] = mapped_column(Float, default=0.000012, nullable=False)

    def __repr__(self) -> str:
        return f"<EnvironmentalConfiguration(id={self.id}, building_id={self.building_id})>"


class SimulationScenario(Base, TimestampMixin):
    """Simulated disturbance scenarios for digital-twin resilience testing."""

    __tablename__ = "simulation_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # NORMAL, NODE_FAILURE, FIELD_IMBALANCE, STRUCTURAL_OVERLOAD, TELEMETRY_FAILURE, POWER_FAILURE, EMERGENCY
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    injected_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    expected_behavior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_scenarios_bld_active", "building_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<SimulationScenario(id={self.id}, name='{self.name}', type='{self.scenario_type}', active={self.is_active})>"
