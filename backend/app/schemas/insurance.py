"""Pydantic v2 schemas for Risk2Relief Parametric Insurance and Consensus domain."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class InsurancePolicyBase(BaseModel):
    policy_number: str = Field(..., description="Unique policy identifier, e.g. R2R-POL-2026-001")
    policyholder_name: str = Field(..., description="Name of policyholder")
    policyholder_type: str = Field("FARMER", description="FARMER, GIG_WORKER, COOPERATIVE, MUNICIPALITY")
    location_name: str = Field(..., description="Protected zone / region")
    covered_event: str = Field("FLASH_FLOOD", description="FLASH_FLOOD, EXTREME_RAINFALL, HEATWAVE, DROUGHT")
    metric: str = Field("rainfall_24h", description="rainfall_24h, temperature_max")
    operator: str = Field(">=", description=">=, >, <=, <, ==")
    threshold: float = Field(..., description="Parametric trigger threshold, e.g. 150.0")
    payout_amount: float = Field(..., description="Fixed automated payout in currency units")
    currency: str = Field("INR", description="Currency symbol: INR, USD")
    active: bool = True
    effective_from: datetime
    effective_to: datetime
    wallet_id: str = Field(..., description="Simulated digital wallet ID, e.g. SIM-WALLET-FARMER-001")
    metadata_json: Optional[Dict[str, Any]] = None


class InsurancePolicyCreate(InsurancePolicyBase):
    pass


class InsurancePolicyResponse(InsurancePolicyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsensusDecisionResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    event_identifier: str
    metric: str
    eligible_source_count: int
    independent_source_count: int
    consensus_value: Optional[float]
    consensus_method: str
    agreement_score: float
    confidence: float
    status: str
    outliers: List[Dict[str, Any]] = []
    rejected_sources: List[Dict[str, Any]] = []
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class TriggerEvaluationResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    policy_id: uuid.UUID
    policy_number: Optional[str] = None
    event_identifier: str
    observed_value: float
    threshold: float
    operator: str
    triggered: bool
    difference: float
    reason: str
    payout_amount: float = 0.0
    currency: str = "INR"
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class SettlementResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    settlement_id: str
    policy_id: uuid.UUID
    policy_number: Optional[str] = None
    event_identifier: str
    settlement_key: str
    wallet_id: str
    amount: float
    currency: str
    transaction_id: str
    status: str
    failure_reason: Optional[str] = None
    is_simulation: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PipelineStageResult(BaseModel):
    stage: str
    status: str
    title: str
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DemoScenarioResponse(BaseModel):
    scenario_name: str
    scenario_id: str
    description: str
    event_identifier: str
    observations: List[Dict[str, Any]]
    validation_status: str
    anomaly_detection: Dict[str, Any]
    source_independence: Dict[str, Any]
    consensus: ConsensusDecisionResponse
    trigger_evaluation: Optional[TriggerEvaluationResponse] = None
    settlement: Optional[SettlementResponse] = None
    pipeline_stages: List[PipelineStageResult]
    audit_trail: List[Dict[str, Any]]
    execution_duration_ms: float
    is_simulation: bool = True
    summary_message: str


class DashboardSummaryResponse(BaseModel):
    active_policies: int
    climate_events_count: int
    validated_observations_count: int
    triggered_payouts_count: int
    total_simulated_payout_inr: float
    settlement_success_rate: float
    average_settlement_time_ms: float
    active_climate_sources_count: int
    recent_events: List[Dict[str, Any]] = []
    recent_settlements: List[SettlementResponse] = []
    system_status: str = "OPERATIONAL"
    simulation_mode: bool = True
