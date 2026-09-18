"""Pydantic v2 schemas for Risk2Relief Climate domain."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ClimateSourceBase(BaseModel):
    source_identifier: str = Field(..., description="Unique source code, e.g. SRC-SAT-001")
    provider_name: str = Field(..., description="Data provider or organization")
    source_name: str = Field(..., description="Human readable name")
    source_type: str = Field("SATELLITE", description="SATELLITE, GROUND_STATION, IOT_SENSOR, WEATHER_API, SIMULATOR")
    source_family: str = Field("GENERIC", description="Sensor mechanism or satellite family")
    independence_group: str = Field(..., description="Grouping for correlation tracking, e.g. GROUP_COPERNICUS")
    location_name: str = Field(..., description="Geographical coverage area")
    latitude: float = 0.0
    longitude: float = 0.0
    reliability_score: float = Field(0.95, ge=0.0, le=1.0)
    status: str = "ONLINE"
    metadata_json: Optional[Dict[str, Any]] = None


class ClimateSourceCreate(ClimateSourceBase):
    pass


class ClimateSourceResponse(ClimateSourceBase):
    id: uuid.UUID
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClimateObservationBase(BaseModel):
    source_identifier: Optional[str] = None
    source_id: Optional[uuid.UUID] = None
    event_id: str = Field(..., description="Unique observation ID, e.g. OBS-2026-001-A")
    event_identifier: str = Field(..., description="Parent climate event code, e.g. EVT-2026-FLOOD-001")
    metric: str = Field("rainfall_24h", description="rainfall_24h, temperature_max, etc.")
    value: float = Field(..., description="Measured reading value")
    unit: str = Field("mm", description="Engineering unit: mm, C, km/h")
    timestamp: datetime = Field(..., description="Observation timestamp")
    latitude: float = 0.0
    longitude: float = 0.0
    metadata_json: Optional[Dict[str, Any]] = None


class ClimateObservationCreate(ClimateObservationBase):
    pass


class ClimateObservationResponse(ClimateObservationBase):
    id: uuid.UUID
    source_id: uuid.UUID
    quality: str = "VALID"
    validation_status: str = "PASSED"
    anomaly_score: float = 0.0
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClimateEventBase(BaseModel):
    event_identifier: str = Field(..., description="Unique event identifier, e.g. EVT-2026-FLOOD-001")
    event_type: str = Field("FLASH_FLOOD", description="FLASH_FLOOD, EXTREME_RAINFALL, HEATWAVE, DROUGHT")
    location_name: str = Field(..., description="Region / District name")
    latitude: float = 0.0
    longitude: float = 0.0
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "MONITORED"
    severity: str = "MEDIUM"
    description: str = ""
    consensus_value: Optional[float] = None
    consensus_unit: str = "mm"
    source_count: int = 0
    independent_source_count: int = 0
    metadata_json: Optional[Dict[str, Any]] = None


class ClimateEventCreate(ClimateEventBase):
    pass


class ClimateEventResponse(ClimateEventBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClimateValidationResult(BaseModel):
    is_valid: bool
    quality: str
    error_code: Optional[str] = None
    reason: str
    validated_at: datetime
