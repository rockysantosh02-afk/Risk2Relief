"""Pydantic v2 schemas for Configuration and Simulation Scenarios.

Enforces system invariants:
- in_silico_only MUST be True.
- hardware_actuation_enabled MUST be False.
- warning_threshold_percentage MUST be strictly less than interlock_trip_threshold_percentage.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScenarioTypeEnum(str, Enum):
    NORMAL = "NORMAL"
    NODE_FAILURE = "NODE_FAILURE"
    FIELD_IMBALANCE = "FIELD_IMBALANCE"
    STRUCTURAL_OVERLOAD = "STRUCTURAL_OVERLOAD"
    TELEMETRY_FAILURE = "TELEMETRY_FAILURE"
    POWER_FAILURE = "POWER_FAILURE"
    EMERGENCY = "EMERGENCY"


class BuildingConfigBase(BaseModel):
    timezone: str = Field(default="UTC")
    data_retention_days: int = Field(ge=1, le=3650, default=90)
    telemetry_buffer_size: int = Field(ge=10, le=100000, default=1000)
    alarm_notification_channels: Optional[List[str]] = Field(default_factory=list)
    config_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BuildingConfigCreate(BuildingConfigBase):
    building_id: uuid.UUID


class BuildingConfigResponse(BuildingConfigBase):
    id: uuid.UUID
    building_id: uuid.UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GravityConfigBase(BaseModel):
    simulation_model: str = Field(default="DISTRIBUTED_VECTOR_FIELD_V1")
    target_gravity_offset_percentage: float = Field(ge=0.0, le=50.0, default=15.0)
    max_compensation_kn: float = Field(ge=0.0, default=5000.0)
    field_distribution_algorithm: str = Field(default="OPTIMAL_SHEAR_BALANCING")
    in_silico_only: Literal[True] = Field(
        default=True, description="Safety invariant: must remain True"
    )
    hardware_actuation_enabled: bool = Field(
        default=False, description="Safety invariant: must remain False"
    )
    damping_factor: float = Field(ge=0.0, le=1.0, default=0.05)
    parameters_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("hardware_actuation_enabled")
    @classmethod
    def validate_no_hardware_actuation(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("Safety boundary violated: hardware actuation cannot be enabled")
        return v


class GravityConfigCreate(GravityConfigBase):
    building_id: uuid.UUID


class GravityConfigResponse(GravityConfigBase):
    id: uuid.UUID
    building_id: uuid.UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyThresholdBase(BaseModel):
    max_tensile_stress_mpa: float = Field(gt=0.0, default=400.0)
    max_compressive_stress_mpa: float = Field(gt=0.0, default=450.0)
    max_deflection_mm: float = Field(gt=0.0, default=15.0)
    max_vibration_amplitude_g: float = Field(gt=0.0, default=0.5)
    warning_threshold_percentage: float = Field(ge=10.0, le=95.0, default=75.0)
    interlock_trip_threshold_percentage: float = Field(ge=50.0, le=100.0, default=90.0)
    auto_trip_enabled: bool = Field(default=True)
    interlock_action: str = Field(default="SAFE_CONTAINMENT")

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "SafetyThresholdBase":
        if self.warning_threshold_percentage >= self.interlock_trip_threshold_percentage:
            raise ValueError("warning_threshold_percentage must be strictly less than interlock_trip_threshold_percentage")
        return self


class SafetyThresholdCreate(SafetyThresholdBase):
    building_id: uuid.UUID


class SafetyThresholdResponse(SafetyThresholdBase):
    id: uuid.UUID
    building_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnvironmentalConfigBase(BaseModel):
    ambient_temp_min_c: float = Field(default=-20.0)
    ambient_temp_max_c: float = Field(default=50.0)
    max_wind_speed_mps: float = Field(ge=0.0, default=35.0)
    seismic_zone_code: str = Field(default="ZONE_IV")
    thermal_expansion_coefficient: float = Field(default=0.000012)

    @model_validator(mode="after")
    def validate_temp_range(self) -> "EnvironmentalConfigBase":
        if self.ambient_temp_min_c >= self.ambient_temp_max_c:
            raise ValueError("ambient_temp_min_c must be less than ambient_temp_max_c")
        return self


class EnvironmentalConfigCreate(EnvironmentalConfigBase):
    building_id: uuid.UUID


class EnvironmentalConfigResponse(EnvironmentalConfigBase):
    id: uuid.UUID
    building_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationScenarioBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scenario_type: ScenarioTypeEnum = Field(default=ScenarioTypeEnum.NORMAL)
    duration_seconds: int = Field(gt=0, default=300)
    severity: str = Field(default="MEDIUM")
    injected_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expected_behavior: Optional[str] = None


class SimulationScenarioCreate(SimulationScenarioBase):
    building_id: uuid.UUID


class SimulationScenarioResponse(SimulationScenarioBase):
    id: uuid.UUID
    building_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
