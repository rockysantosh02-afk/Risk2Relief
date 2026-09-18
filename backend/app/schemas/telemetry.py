"""Pydantic v2 schemas for Telemetry ingestion, readings, batches, and quality tracking."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SourceTypeEnum(str, Enum):
    STRAIN_GAUGE = "STRAIN_GAUGE"
    ACCELEROMETER = "ACCELEROMETER"
    TEMPERATURE = "TEMPERATURE"
    LOAD_SENSOR = "LOAD_SENSOR"
    INCLINOMETER = "INCLINOMETER"
    PRESSURE = "PRESSURE"
    AIR_QUALITY = "AIR_QUALITY"
    SIMULATOR = "SIMULATOR"


class QualityEnum(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    STALE = "STALE"
    DUPLICATE = "DUPLICATE"
    ANOMALOUS = "ANOMALOUS"
    MISSING = "MISSING"


class TelemetrySourceBase(BaseModel):
    source_identifier: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    source_type: SourceTypeEnum = Field(default=SourceTypeEnum.STRAIN_GAUGE)
    status: str = Field(default="ONLINE")
    reliability_score: float = Field(ge=0.0, le=1.0, default=1.0)
    sampling_rate_hz: float = Field(gt=0.0, default=10.0)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TelemetrySourceCreate(TelemetrySourceBase):
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID] = None
    structural_node_id: Optional[uuid.UUID] = None


class TelemetrySourceResponse(TelemetrySourceBase):
    id: uuid.UUID
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID]
    structural_node_id: Optional[uuid.UUID]
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryReadingBase(BaseModel):
    metric: str = Field(min_length=1, max_length=64)
    value: float
    unit: str = Field(min_length=1, max_length=32)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = Field(min_length=1, max_length=64)
    quality: QualityEnum = Field(default=QualityEnum.VALID)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TelemetryReadingCreate(TelemetryReadingBase):
    source_id: uuid.UUID
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None


class TelemetryReadingResponse(TelemetryReadingBase):
    id: uuid.UUID
    source_id: uuid.UUID
    building_id: uuid.UUID
    zone_id: Optional[uuid.UUID]
    batch_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryBatchCreate(BaseModel):
    batch_identifier: str = Field(min_length=1, max_length=64)
    building_id: uuid.UUID
    readings: List[TelemetryReadingBase] = Field(default_factory=list)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TelemetryBatchResponse(BaseModel):
    id: uuid.UUID
    batch_identifier: str
    building_id: uuid.UUID
    source_count: int
    readings_count: int
    status: str
    ingested_at: datetime
    processing_duration_ms: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryQualityResponse(BaseModel):
    id: uuid.UUID
    reading_id: Optional[uuid.UUID]
    source_id: uuid.UUID
    flagged_quality: QualityEnum
    anomaly_score: Optional[float]
    reason: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryFilterParams(BaseModel):
    building_id: uuid.UUID
    metric: Optional[str] = None
    source_id: Optional[uuid.UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    quality: Optional[QualityEnum] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class IngestionStatisticsResponse(BaseModel):
    total_received: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicate: int = 0
    stale: int = 0
    invalid: int = 0
    anomalous: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class AggregationQueryRequest(BaseModel):
    building_id: uuid.UUID
    metric: str
    bucket: str = Field(default="1m", description="1s, 10s, 1m, 5m, 15m")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    baseline_value: Optional[float] = None


class SourceHealthResponse(BaseModel):
    source_id: uuid.UUID
    source_identifier: str
    status: str
    last_seen: Optional[datetime]
    freshness_seconds: Optional[float]
    total_readings: int
    valid_readings: int
    error_readings: int
    duplicate_readings: int
    anomalous_readings: int
    error_rate: float
    duplicate_rate: float
    anomaly_rate: float
    availability: float
    reliability_score: float
    is_healthy: bool
    explanation: Dict[str, Any]

