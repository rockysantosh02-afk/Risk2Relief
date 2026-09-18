"""API v1 Incident Management Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.safety_service import SafetyService
from app.schemas.safety import IncidentCreate, IncidentUpdate, IncidentResponse

router = APIRouter(prefix="/incidents", tags=["Incidents & Containment"])


@router.get(
    "",
    response_model=List[IncidentResponse],
    summary="List Safety Incidents",
    description="Retrieve incidents filtered by building, lifecycle status, or severity.",
)
async def list_incidents(
    building_id: uuid.UUID = Query(...),
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[IncidentResponse]:
    service = SafetyService(db)
    incidents = await service.list_incidents(
        building_id=building_id, status=status, severity=severity, limit=limit
    )
    return [IncidentResponse.model_validate(i) for i in incidents]


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Incident",
    description="Register a manual or programmatic safety incident and generate simulated containment recommendations.",
)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    service = SafetyService(db)
    try:
        created = await service.create_incident(data)
        return IncidentResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get Incident Details",
)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    service = SafetyService(db)
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    return IncidentResponse.model_validate(incident)


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update Incident Status or Resolution",
)
async def update_incident(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    service = SafetyService(db)
    updated = await service.update_incident(incident_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    return IncidentResponse.model_validate(updated)
