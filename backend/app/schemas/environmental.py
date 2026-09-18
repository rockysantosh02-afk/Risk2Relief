"""Pydantic v2 schemas for Environmental Monitoring and Hazard Assessment."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalStateResponse(BaseModel):
    """Current environmental conditions surrounding a building."""
    building_id: uuid.UUID
    ambient_temperature_c: float
    relative_humidity_percent: float
    wind_speed_mps: float
    seismic_pga_g: float
    air_quality_index: float
    status: str = "NORMAL"
    hazard_level: str = "LOW"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class EnvironmentalAssessRequest(BaseModel):
    """Payload to evaluate environmental hazards against safety codes."""
    building_id: uuid.UUID
    ambient_temperature_c: Optional[float] = 22.0
    relative_humidity_percent: Optional[float] = 50.0
    wind_speed_mps: Optional[float] = 5.0
    seismic_pga_g: Optional[float] = 0.0
    barometric_pressure_hpa: Optional[float] = 1013.25


class EnvironmentalAssessResponse(BaseModel):
    """Evaluation result for environmental hazards."""
    building_id: uuid.UUID
    hazard_level: str                         # LOW, MODERATE, HIGH, CRITICAL
    seismic_risk: str                         # LOW, MODERATE, HIGH, CRITICAL
    thermal_stress_risk: str                  # LOW, ELEVATED
    wind_load_risk: str                       # LOW, ELEVATED
    triggers_emergency: bool
    recommended_containment_actions: List[str]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
