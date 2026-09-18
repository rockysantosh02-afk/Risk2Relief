"""Pydantic v2 schemas for Safety State Machine, Incidents, and Failure Injection."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.safety.state_machine import SafetyState


class SafetyStateTransitionRequest(BaseModel):
    """Input payload to evaluate safety state machine transitions."""
    gravity_stability: str = Field(default="NORMAL")
    structural_risk: str = Field(default="LOW")
    telemetry_reliability: float = Field(default=1.0, ge=0.0, le=1.0)
    power_state: str = Field(default="NOMINAL")
    communication_state: str = Field(default="CONNECTED")
    environmental_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_maintenance_mode: bool = False


class SafetyStateTransitionResponse(BaseModel):
    id: uuid.UUID
    building_id: uuid.UUID
    from_state: str
    to_state: str
    trigger_reason: str
    inputs_snapshot_json: Optional[Dict[str, Any]]
    transitioned_at: datetime
    is_valid_transition: bool

    model_config = ConfigDict(from_attributes=True)


class IncidentBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    severity: str = Field(default="MEDIUM", max_length=32)
    status: str = Field(default="OPEN", max_length=32)
    affected_zone_id: Optional[uuid.UUID] = None
    initial_safety_state: str = Field(default="NORMAL")
    escalated_safety_state: str = Field(default="WARNING")
    root_cause: Optional[str] = None
    evidence_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recommended_simulated_response: Optional[str] = None


class IncidentCreate(IncidentBase):
    building_id: uuid.UUID
    incident_code: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    root_cause: Optional[str] = None
    recommended_simulated_response: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IncidentResponse(IncidentBase):
    id: uuid.UUID
    building_id: uuid.UUID
    incident_code: str
    opened_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FailureInjectionRequest(BaseModel):
    scenario: str = Field(default="sensor_failure")
    initial_safety_state: str = Field(default="NORMAL")


class FailureInjectionResponse(BaseModel):
    scenario: str
    detected: bool
    detection_latency_ms: float
    initial_safety_state: str
    resulting_safety_state: str
    safety_response_appropriate: bool
    data_integrity_preserved: bool
    recovery_successful: bool
    duplicate_prevented: bool
    data_loss_count: int
    details: Dict[str, Any]
    safety_disclaimer: str
