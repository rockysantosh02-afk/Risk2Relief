"""Pydantic v2 schemas for Building, Floor, and Zone hierarchy."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ZoneBase(BaseModel):
    zone_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    zone_type: str = Field(default="CORE")
    area_sqm: float = Field(ge=0.0, default=0.0)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ZoneCreate(ZoneBase):
    pass


class ZoneResponse(ZoneBase):
    id: uuid.UUID
    floor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FloorBase(BaseModel):
    floor_number: int
    name: str = Field(min_length=1, max_length=128)
    elevation_meters: float = Field(default=0.0)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FloorCreate(FloorBase):
    pass


class FloorResponse(FloorBase):
    id: uuid.UUID
    building_id: uuid.UUID
    zones: List[ZoneResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildingBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    description: Optional[str] = None
    location: Optional[str] = None
    status: str = Field(default="OPERATIONAL")
    number_of_floors: int = Field(ge=1, default=1)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    number_of_floors: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None


class BuildingResponse(BuildingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildingHierarchyResponse(BuildingResponse):
    floors: List[FloorResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
