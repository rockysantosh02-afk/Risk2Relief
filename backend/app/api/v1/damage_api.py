"""FastAPI REST API router for Damage Assessment & Dynamic Compensation Rules.

Adheres strictly to: Router -> Service -> Database/Rule Configuration.
Guarantees pure backend calculation and deterministic validation.
"""

from __future__ import annotations
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.damage_assessment import (
    DamageAssessmentCalculateRequest,
    DamageAssessmentCalculationResponse,
    DamageAssessmentCreate,
    DamageAssessmentResponse,
    DamageCompensationRuleResponse,
)
from app.services.compensation_service import DamageCompensationService

router = APIRouter(tags=["Damage Assessment & Compensation Rules"])


@router.post(
    "/damage-assessments/calculate",
    response_model=DamageAssessmentCalculationResponse,
    summary="Calculate compensation preview for damage assessment",
)
async def calculate_damage_compensation(request: DamageAssessmentCalculateRequest):
    """
    Validate dynamic inputs, normalize units (cents -> acres), select applicable compensation rule,
    and compute deterministic payout with backend cap enforcement.
    """
    try:
        breakdown = DamageCompensationService.calculate_compensation(request)
        return DamageAssessmentCalculationResponse(
            status="SUCCESS",
            breakdown=breakdown,
            is_simulation=True,
            disclaimer="SIMULATION MODE — NO REAL MONEY MOVED",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to calculate damage assessment: {str(exc)}",
        )


@router.post(
    "/damage-assessments",
    response_model=DamageAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and record a new damage assessment",
)
async def create_damage_assessment(assessment_in: DamageAssessmentCreate):
    """
    Validate, calculate compensation, log to decision audit trail, and persist victim damage assessment.
    """
    try:
        return DamageCompensationService.record_assessment(assessment_in)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record damage assessment: {str(exc)}",
        )


@router.get(
    "/damage-assessments",
    response_model=List[DamageAssessmentResponse],
    summary="List all registered damage assessments",
)
async def list_damage_assessments():
    """Retrieve all submitted damage assessments."""
    return DamageCompensationService.get_all_assessments()


@router.get(
    "/damage-assessments/{assessment_id}",
    response_model=DamageAssessmentResponse,
    summary="Retrieve single damage assessment by ID",
)
async def get_damage_assessment(assessment_id: uuid.UUID):
    """Retrieve details for a specific damage assessment record."""
    assessment = DamageCompensationService.get_assessment_by_id(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Damage assessment with ID '{assessment_id}' not found.",
        )
    return assessment


@router.get(
    "/damage-rules",
    response_model=List[DamageCompensationRuleResponse],
    summary="List all active compensation rules",
)
async def list_damage_rules():
    """Return all active, auditable compensation rules across occupations and climate events."""
    return DamageCompensationService.get_all_rules()


@router.get(
    "/damage-rules/{rule_code}",
    response_model=DamageCompensationRuleResponse,
    summary="Retrieve a specific compensation rule by rule code",
)
async def get_damage_rule(rule_code: str):
    """Retrieve details and rate configuration for a specific rule code."""
    rule = DamageCompensationService.get_rule_by_code(rule_code)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compensation rule with code '{rule_code}' not found.",
        )
    return DamageCompensationRuleResponse(**rule)
