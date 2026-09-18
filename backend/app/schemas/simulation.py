"""Pydantic v2 schemas for Digital-Twin Simulation Runs, Safety Events, and Risk Assessments."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.physics.structural_risk import RiskLevel
from app.physics.stability import StabilityStatus


class SafetyBoundaryStatus(BaseModel):
    subsystem: str = "physics_simulation_digital_twin"
    simulation_only: bool = True
    hardware_actuators_allowed: bool = False
    gravity_modifying_hardware_allowed: bool = False
    direct_control_commands_allowed: bool = False
    interlock_state: str = "ACTIVE"


class SimulationStatusResponse(BaseModel):
    status: str
    mode: str = "in-silico-only"
    active_monitored_zones: int = 4
    safety_boundary: SafetyBoundaryStatus


class SafetyEventBase(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    severity: str = Field(default="WARNING", max_length=32)
    trigger_source: str = Field(default="SIMULATION_ENGINE", max_length=64)
    details_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SafetyEventCreate(SafetyEventBase):
    building_id: uuid.UUID
    simulation_run_id: Optional[uuid.UUID] = None
    detected_at: Optional[datetime] = None


class SafetyEventResponse(SafetyEventBase):
    id: uuid.UUID
    building_id: uuid.UUID
    simulation_run_id: Optional[uuid.UUID]
    detected_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationExecuteRequest(BaseModel):
    """Parameters to trigger an in-silico simulation run."""
    scenario_type: str = Field(default="NORMAL")
    step_count: int = Field(default=5, ge=1, le=100)
    step_duration_seconds: float = Field(default=1.0, gt=0.0, le=60.0)
    target_offset_percentage: float = Field(default=15.0, ge=0.0, le=50.0)
    custom_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SimulationRunBase(BaseModel):
    scenario_type: str
    status: str = Field(default="COMPLETED")
    duration_seconds: float = 0.0
    step_count: int = 1
    peak_risk_level: str = "LOW"
    peak_risk_score: float = 0.0
    final_risk_level: str = "LOW"
    final_risk_score: float = 0.0
    worst_stability_status: str = "NORMAL"
    summary_metrics_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SimulationRunCreate(SimulationRunBase):
    building_id: uuid.UUID
    scenario_id: Optional[uuid.UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    step_results_json: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class SimulationRunResponse(SimulationRunBase):
    id: uuid.UUID
    building_id: uuid.UUID
    scenario_id: Optional[uuid.UUID]
    start_time: datetime
    end_time: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationRunDetailResponse(SimulationRunResponse):
    step_results_json: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    safety_events: List[SafetyEventResponse] = Field(default_factory=list)
