"""Pydantic v2 schemas for Structural and Anti-Gravity Nodes."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class NodeTypeEnum(str, Enum):
    COLUMN = "COLUMN"
    BEAM = "BEAM"
    SLAB = "SLAB"
    FOUNDATION = "FOUNDATION"
    SENSOR_NODE = "SENSOR_NODE"
    OTHER = "OTHER"


class AntiGravityNodeStateEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"
    SIMULATED = "SIMULATED"


class StructuralNodeBase(BaseModel):
    node_code: str = Field(min_length=1, max_length=64)
    node_type: NodeTypeEnum = Field(default=NodeTypeEnum.COLUMN)
    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    position_z: float = Field(default=0.0)
    health_status: str = Field(default="OPTIMAL")
    baseline_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    node_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class StructuralNodeCreate(StructuralNodeBase):
    building_id: uuid.UUID
    floor_id: uuid.UUID
    zone_id: uuid.UUID


class StructuralNodeResponse(StructuralNodeBase):
    id: uuid.UUID
    building_id: uuid.UUID
    floor_id: uuid.UUID
    zone_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AntiGravityNodeBase(BaseModel):
    node_identifier: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    position_z: float = Field(default=0.0)
    nominal_field_strength_kn: float = Field(ge=0.0, default=500.0)
    operating_state: AntiGravityNodeStateEnum = Field(default=AntiGravityNodeStateEnum.SIMULATED)
    health_score: float = Field(ge=0.0, le=100.0, default=100.0)
    efficiency: float = Field(ge=0.0, le=1.0, default=1.0)
    simulation_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    configuration_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AntiGravityNodeCreate(AntiGravityNodeBase):
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID] = None


class AntiGravityNodeResponse(AntiGravityNodeBase):
    id: uuid.UUID
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID]
    is_simulated: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
