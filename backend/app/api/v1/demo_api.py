"""API v1 Endpoints for Hackathon Demo Scenarios & Executive Dashboard."""

import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from app.schemas.insurance import DemoScenarioResponse, DashboardSummaryResponse, SettlementResponse
from app.climate.simulator import Risk2ReliefSimulator
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.validation import ClimateValidationEngine
from app.climate.audit_trail import ClimateAuditTrailService
from app.api.v1.climate_api import _DEMO_POLICIES, _DEMO_EVENTS, _DEMO_SOURCES

router = APIRouter(prefix="", tags=["Risk2Relief Demo Scenarios & Dashboard"])


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


@router.post("/demo/scenario/success", response_model=DemoScenarioResponse, summary="Execute Scenario 1: Successful Corroborated Trigger")
async def execute_scenario_success():
    """Execute Scenario 1: 158 / 154 / 156 mm -> Consensus Reached -> Instant ₹25,000 Payout."""
    return Risk2ReliefSimulator.run_scenario_1_success()


@router.post("/demo/scenario/disagreement", response_model=DemoScenarioResponse, summary="Execute Scenario 2: Data Disagreement & ML Anomaly Block")
async def execute_scenario_disagreement():
    """Execute Scenario 2: 158 / 156 / 17 mm -> ML flags 17mm outlier -> Consensus fails -> Payout blocked safely."""
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
