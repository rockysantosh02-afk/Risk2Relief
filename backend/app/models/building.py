"""Building domain SQLAlchemy 2.x models.

Defines Building, BuildingFloor, BuildingZone, StructuralNode, and AntiGravityNode.
Includes strict digital-twin in-silico invariants for anti-gravity simulation.
"""

import uuid
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
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Building(Base, TimestampMixin):
    """Monitored facility domain model."""

    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPERATIONAL", nullable=False)
    number_of_floors: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    floors: Mapped[List["BuildingFloor"]] = relationship(
        "BuildingFloor", back_populates="building", cascade="all, delete-orphan", order_by="BuildingFloor.floor_number", lazy="selectin"
    )
    structural_nodes: Mapped[List["StructuralNode"]] = relationship(
        "StructuralNode", back_populates="building", cascade="all, delete-orphan", lazy="selectin"
    )
    antigravity_nodes: Mapped[List["AntiGravityNode"]] = relationship(
        "AntiGravityNode", back_populates="building", cascade="all, delete-orphan", lazy="selectin"
    )
    telemetry_sources: Mapped[List["TelemetrySource"]] = relationship(
        "TelemetrySource", back_populates="building", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Building(id={self.id}, code='{self.code}', name='{self.name}')>"


class BuildingFloor(Base, TimestampMixin):
    """Building floor level hierarchy."""

    __tablename__ = "building_floors"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    elevation_meters: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="floors")
    zones: Mapped[List["BuildingZone"]] = relationship(
        "BuildingZone", back_populates="floor", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("building_id", "floor_number", name="uq_building_floor_number"),
    )

    def __repr__(self) -> str:
        return f"<BuildingFloor(id={self.id}, floor_number={self.floor_number}, name='{self.name}')>"


class BuildingZone(Base, TimestampMixin):
    """Structural/functional zone within a floor."""

    __tablename__ = "building_zones"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(64), default="CORE", nullable=False)
    area_sqm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    floor: Mapped["BuildingFloor"] = relationship("BuildingFloor", back_populates="zones")
    structural_nodes: Mapped[List["StructuralNode"]] = relationship(
        "StructuralNode", back_populates="zone", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("floor_id", "zone_code", name="uq_floor_zone_code"),
    )

    def __repr__(self) -> str:
        return f"<BuildingZone(id={self.id}, zone_code='{self.zone_code}', name='{self.name}')>"


class StructuralNode(Base, TimestampMixin):
    """Physical or monitored structural element (column, beam, slab, foundation)."""

    __tablename__ = "structural_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(
        String(32), default="COLUMN", nullable=False
    )  # COLUMN, BEAM, SLAB, FOUNDATION, SENSOR_NODE, OTHER
    position_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_z: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    health_status: Mapped[str] = mapped_column(String(32), default="OPTIMAL", nullable=False)
    baseline_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    node_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="structural_nodes")
    zone: Mapped["BuildingZone"] = relationship("BuildingZone", back_populates="structural_nodes")

    __table_args__ = (
        UniqueConstraint("zone_id", "node_code", name="uq_zone_structural_node_code"),
        Index("ix_structural_nodes_type_health", "node_type", "health_status"),
    )

    def __repr__(self) -> str:
        return f"<StructuralNode(id={self.id}, code='{self.node_code}', type='{self.node_type}')>"


class AntiGravityNode(Base, TimestampMixin):
    """Digital-twin simulated anti-gravity compensation node.

    SYSTEM SAFETY BOUNDARY:
    This model represents a purely IN-SILICO mathematical node used for structural
    stress offload simulations in the digital twin. It DOES NOT control or connect
    to real-world physical gravity actuators.
    """

    __tablename__ = "antigravity_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    node_identifier: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    position_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_z: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    nominal_field_strength_kn: Mapped[float] = mapped_column(
        Float, default=500.0, nullable=False
    )  # Simulated load offset capacity
    operating_state: Mapped[str] = mapped_column(
        String(32), default="SIMULATED", nullable=False
    )  # ACTIVE, DEGRADED, FAILED, MAINTENANCE, SIMULATED
    health_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    efficiency: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(
        String(8), default="true", nullable=False
    )  # Hard invariant: strictly simulated
    simulation_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    configuration_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="antigravity_nodes")

    __table_args__ = (
        Index("ix_ag_nodes_building_state", "building_id", "operating_state"),
    )

    def __repr__(self) -> str:
        return f"<AntiGravityNode(id={self.id}, identifier='{self.node_identifier}', state='{self.operating_state}')>"
