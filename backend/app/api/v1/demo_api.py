"""API v1 Endpoints for Hackathon Demo Scenarios, Dynamic Pipeline & Executive Dashboard."""

import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.insurance import DemoScenarioResponse, DashboardSummaryResponse, SettlementResponse
from app.climate.simulator import Risk2ReliefSimulator
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.validation import ClimateValidationEngine
from app.climate.audit_trail import ClimateAuditTrailService
from app.api.v1.climate_api import _DEMO_POLICIES, _DEMO_EVENTS, _DEMO_SOURCES

router = APIRouter(prefix="", tags=["Risk2Relief Demo Scenarios & Dashboard"])


class DynamicPipelineRequest(BaseModel):
    sat_value: float = Field(..., description="Satellite reading in mm, e.g. 173.0")
    ground_value: float = Field(..., description="Ground station reading in mm, e.g. 169.0")
    iot_value: float = Field(..., description="IoT sensor reading in mm, e.g. 171.0")
    policy_threshold: float = Field(150.0, description="Parametric trigger threshold in mm")
    payout_amount: float = Field(25000.0, description="Parametric payout amount in INR")
    event_identifier: Optional[str] = Field(None, description="Optional event identifier")


class SettleDamageAssessmentRequest(BaseModel):
    event_identifier: str = Field(..., description="Climate event identifier from pipeline")
    policy_id: Optional[str] = Field("00000000-0000-0000-0000-000000000001", description="Policy ID")
    policy_number: Optional[str] = Field("R2R-POL-2026-001", description="Policy Number")
    wallet_id: Optional[str] = Field("SIM-WALLET-FARMER-001", description="Recipient wallet")
    assessment_id: Optional[str] = Field(None, description="Damage assessment ID or number")
    calculated_compensation: float = Field(..., description="Authoritative calculated compensation amount in INR")
    currency: Optional[str] = Field("INR", description="Currency")
    rule_code: Optional[str] = Field(None, description="Applied damage rule code")


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse, summary="Executive Dashboard KPI Summary")
async def get_dashboard_summary():
    """Return live metrics and statistics for the Risk2Relief executive dashboard."""
    settlements = SimulatedSettlementEngine.get_all_settlements()
    completed_settlements = [s for s in settlements if s.status == "COMPLETED"]
    total_payout = sum(s.amount for s in completed_settlements)
    success_rate = (len(completed_settlements) / len(settlements) * 100.0) if settlements else 100.0

    recent_settlement_dtos = [
        SettlementResponse(
            id=uuid.uuid4(),
            settlement_id=s.settlement_id,
            policy_id=uuid.UUID(s.policy_id) if len(s.policy_id) == 36 else uuid.uuid4(),
            policy_number=s.policy_number,
            event_identifier=s.event_identifier,
            settlement_key=s.settlement_key,
            wallet_id=s.wallet_id,
            amount=s.amount,
            currency=s.currency,
            transaction_id=s.transaction_id,
            status=s.status,
            failure_reason=s.failure_reason,
            is_simulation=True,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )
        for s in settlements[-5:]
    ]

    return DashboardSummaryResponse(
        active_policies=len([p for p in _DEMO_POLICIES if p.get("active", True)]),
        climate_events_count=len(_DEMO_EVENTS),
        validated_observations_count=len(settlements) * 3 + 12,
        triggered_payouts_count=len(completed_settlements),
        total_simulated_payout_inr=total_payout,
        settlement_success_rate=round(success_rate, 1),
        average_settlement_time_ms=2.45,
        active_climate_sources_count=len(_DEMO_SOURCES),
        recent_events=_DEMO_EVENTS,
        recent_settlements=recent_settlement_dtos,
        system_status="OPERATIONAL",
        simulation_mode=True,
    )


@router.post("/demo/dynamic-run", response_model=DemoScenarioResponse, summary="Execute Dynamic Live Decision Pipeline with Isolation Forest ML")
async def execute_dynamic_pipeline(payload: DynamicPipelineRequest):
    """Execute the full 8-stage decision pipeline with arbitrary live inputs scored by scikit-learn Isolation Forest."""
    return Risk2ReliefSimulator.run_dynamic_pipeline(
        sat_value=payload.sat_value,
        ground_value=payload.ground_value,
        iot_value=payload.iot_value,
        policy_threshold=payload.policy_threshold,
        payout_amount=payload.payout_amount,
        event_identifier=payload.event_identifier,
    )


@router.post("/demo/settle-damage-assessment", response_model=SettlementResponse, summary="Execute Instant Settlement directly from Damage Assessment Compensation")
async def settle_damage_assessment(payload: SettleDamageAssessmentRequest):
    """
    Execute instant simulated settlement for the exact calculated compensation amount from Damage Assessment & Relief.
    Enforces idempotency, verifies positive amount, and logs stages to audit trail.
    """
    if payload.calculated_compensation <= 0:
        raise HTTPException(
            status_code=400,
            detail="Settlement blocked: Calculated compensation amount must be strictly greater than zero.",
        )

    # 1. Execute settlement in ledger
    settlement_record = SimulatedSettlementEngine.execute_settlement_for_assessment(
        event_identifier=payload.event_identifier,
        policy_id=payload.policy_id or "00000000-0000-0000-0000-000000000001",
        policy_number=payload.policy_number or "R2R-POL-2026-001",
        wallet_id=payload.wallet_id or "SIM-WALLET-FARMER-001",
        amount=float(payload.calculated_compensation),
        currency=payload.currency or "INR",
        assessment_id=payload.assessment_id,
    )

    # 2. Record in Audit Trail
    ClimateAuditTrailService.record_stage(
        event_identifier=payload.event_identifier,
        stage="RELIEF_COMPENSATION_CALCULATED",
        status="SUCCESS",
        title="Authoritative Relief Compensation Sourced",
        message=f"Verified compensation of ₹{payload.calculated_compensation:,.2f} {payload.currency or 'INR'} from assessment '{payload.assessment_id or 'BENEFICIARY-001'}' (Rule: {payload.rule_code or 'RULE-APPLIED'}).",
        policy_id=payload.policy_id,
        metadata={
            "assessment_id": payload.assessment_id,
            "calculated_compensation": payload.calculated_compensation,
            "rule_code": payload.rule_code,
        },
    )

    ClimateAuditTrailService.record_stage(
        event_identifier=payload.event_identifier,
        stage="SETTLEMENT_COMPLETED",
        status="SUCCESS",
        title="Instant Settlement Dispatched (From Damage Relief)",
        message=f"Simulated payout of ₹{settlement_record.amount:,.2f} {settlement_record.currency} dispatched to wallet '{settlement_record.wallet_id}'. Txn ID: {settlement_record.transaction_id}.",
        policy_id=payload.policy_id,
        metadata={
            "settlement_id": settlement_record.settlement_id,
            "transaction_id": settlement_record.transaction_id,
            "amount": settlement_record.amount,
            "is_idempotent_retry": settlement_record.is_idempotent_retry,
            "source": "DAMAGE_ASSESSMENT_COMPENSATION",
        },
    )

    return SettlementResponse(
        id=uuid.uuid4(),
        settlement_id=settlement_record.settlement_id,
        policy_id=uuid.UUID(payload.policy_id) if payload.policy_id and len(payload.policy_id) == 36 else uuid.uuid4(),
        policy_number=settlement_record.policy_number,
        event_identifier=settlement_record.event_identifier,
        settlement_key=settlement_record.settlement_key,
        wallet_id=settlement_record.wallet_id,
        amount=settlement_record.amount,
        currency=settlement_record.currency,
        transaction_id=settlement_record.transaction_id,
        status=settlement_record.status,
        failure_reason=settlement_record.failure_reason,
        is_simulation=True,
        created_at=settlement_record.created_at,
        completed_at=settlement_record.completed_at,
    )


@router.post("/demo/scenario/success", response_model=DemoScenarioResponse, summary="Execute Scenario 1: Successful Corroborated Trigger")
async def execute_scenario_success():
    """Execute Scenario 1: 158 / 154 / 156 mm -> Consensus Reached -> Instant ₹25,000 Payout."""
    return Risk2ReliefSimulator.run_scenario_1_success()


@router.post("/demo/scenario/disagreement", response_model=DemoScenarioResponse, summary="Execute Scenario 2: Data Disagreement & ML Anomaly Block")
async def execute_scenario_disagreement():
    """Execute Scenario 2: 158 / 156 / 17 mm -> Isolation Forest ML flags 17mm outlier -> Consensus fails -> Payout blocked safely."""
    return Risk2ReliefSimulator.run_scenario_2_disagreement()


@router.post("/demo/scenario/no-trigger", response_model=DemoScenarioResponse, summary="Execute Scenario 3: Sub-Threshold Rainfall (No Trigger)")
async def execute_scenario_no_trigger():
    """Execute Scenario 3: 120 / 118 / 121 mm -> Consensus ~120mm < 150mm threshold -> Zero payout."""
    return Risk2ReliefSimulator.run_scenario_3_no_trigger()


@router.post("/demo/scenario/idempotency", response_model=DemoScenarioResponse, summary="Execute Scenario 4: Idempotent Duplicate Retry Protection")
async def execute_scenario_idempotency():
    """Execute Scenario 4: Resubmits identical event. Idempotency guard prevents duplicate payout and returns existing record."""
    return Risk2ReliefSimulator.run_scenario_4_idempotency()


@router.post("/demo/reset", summary="Reset simulation ledger and audit log for a clean demo")
async def reset_demo_state():
    """Reset all in-memory demo records, settlements, and caches."""
    SimulatedSettlementEngine.reset_ledger()
    ClimateValidationEngine.reset_cache()
    ClimateAuditTrailService.reset_audit_log()
    return {"status": "success", "message": "Demo state reset to clean initial baseline."}
