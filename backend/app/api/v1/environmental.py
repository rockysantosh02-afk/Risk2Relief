"""API v1 Environmental Monitoring and Hazard Assessment Endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.environmental_service import EnvironmentalService
from app.schemas.environmental import (
    EnvironmentalStateResponse,
    EnvironmentalAssessRequest,
    EnvironmentalAssessResponse,
)

router = APIRouter(prefix="/environmental", tags=["Environmental Monitoring"])


@router.get(
    "/{building_id}/state",
    response_model=EnvironmentalStateResponse,
    summary="Get Environmental Monitoring State",
    description="Retrieve ambient temperature, relative humidity, wind speed, seismic acceleration, and hazard levels.",
)
async def get_environmental_state(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EnvironmentalStateResponse:
    service = EnvironmentalService(db)
    try:
        return await service.get_environmental_state(building_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{building_id}/assess",
    response_model=EnvironmentalAssessResponse,
    summary="Assess Environmental Hazards",
    description="Evaluate ambient temperature, wind gusts, and seismic PGA against building design criteria.",
)
async def assess_environmental_hazards(
    building_id: uuid.UUID,
    request: EnvironmentalAssessRequest,
    db: AsyncSession = Depends(get_db),
) -> EnvironmentalAssessResponse:
    service = EnvironmentalService(db)
    request.building_id = building_id
    try:
        return await service.assess_environmental_hazard(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
