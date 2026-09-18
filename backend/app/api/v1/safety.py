"""API v1 Safety State Machine & Controlled Failure Injection Endpoints."""

import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.safety_service import SafetyService
from app.schemas.safety import (
    SafetyStateTransitionRequest,
    SafetyStateTransitionResponse,
    FailureInjectionRequest,
    FailureInjectionResponse,
    IncidentResponse,
)

router = APIRouter(prefix="/safety", tags=["Safety & Resilience"])


@router.post(
    "/{building_id}/transition",
    summary="Evaluate & Trigger Safety State Transition",
    description="Deterministically evaluates multi-modal inputs, logs audit records, and escalates incidents when degraded.",
)
async def evaluate_safety_transition(
    building_id: uuid.UUID,
    request: SafetyStateTransitionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = SafetyService(db)
    try:
        eval_res, inc, alert = await service.evaluate_and_transition(building_id, request)
        return {
            "evaluation": {
                "from_state": eval_res.from_state.value,
                "to_state": eval_res.to_state.value,
                "is_transition_triggered": eval_res.is_transition_triggered,
                "is_valid_transition": eval_res.is_valid_transition,
                "trigger_reason": eval_res.trigger_reason,
                "evidence": eval_res.evidence,
                "timestamp": eval_res.timestamp.isoformat(),
            },
            "incident": IncidentResponse.model_validate(inc) if inc else None,
            "alert": {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "message": alert.message,
                "recommended_simulated_action": alert.recommended_simulated_action,
            } if alert else None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{building_id}/state",
    summary="Get Current Building Safety State",
    description="Returns the active operational state (NORMAL, WARNING, DEGRADED, EMERGENCY, RECOVERY, MAINTENANCE).",
)
async def get_current_safety_state(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    service = SafetyService(db)
    current_state = await service.safety_repo.get_current_safety_state(building_id)
    return {
        "building_id": str(building_id),
        "safety_state": current_state,
    }


@router.get(
    "/{building_id}/transitions",
    response_model=List[SafetyStateTransitionResponse],
    summary="Get Safety State Transition Audit History",
)
async def get_transition_history(
    building_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[SafetyStateTransitionResponse]:
    service = SafetyService(db)
    records = await service.get_transition_history(building_id, limit=limit)
    return [SafetyStateTransitionResponse.model_validate(r) for r in records]


@router.post(
    "/failure-injection",
    response_model=FailureInjectionResponse,
    summary="Execute Controlled In-Silico Failure Injection",
    description="Simulates fault modes (sensor, duplicate, corrupted, network, node, overload, etc.) to verify resilience.",
)
async def execute_failure_injection(
    request: FailureInjectionRequest,
) -> FailureInjectionResponse:
    # Failure injection runs purely in-silico in-memory
    service = SafetyService(None)
    try:
        res = service.run_failure_injection(request.scenario, request.initial_safety_state)
        return FailureInjectionResponse(
            scenario=res.scenario.value,
            detected=res.detected,
            detection_latency_ms=res.detection_latency_ms,
            initial_safety_state=res.initial_safety_state.value,
            resulting_safety_state=res.resulting_safety_state.value,
            safety_response_appropriate=res.safety_response_appropriate,
            data_integrity_preserved=res.data_integrity_preserved,
            recovery_successful=res.recovery_successful,
            duplicate_prevented=res.duplicate_prevented,
            data_loss_count=res.data_loss_count,
            details=res.details,
            safety_disclaimer=res.safety_disclaimer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
