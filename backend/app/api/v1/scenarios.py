"""API v1 Simulation Scenario Management Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.simulation_scenario_service import SimulationScenarioService
from app.schemas.configuration import SimulationScenarioCreate, SimulationScenarioResponse

router = APIRouter(prefix="/scenarios", tags=["Simulation Scenarios"])


@router.get(
    "",
    response_model=List[SimulationScenarioResponse],
    summary="List Simulation Scenarios",
)
async def list_scenarios(
    building_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> List[SimulationScenarioResponse]:
    service = SimulationScenarioService(db)
    scenarios = await service.list_scenarios(building_id)
    return [SimulationScenarioResponse.model_validate(s) for s in scenarios]


@router.post(
    "",
    response_model=SimulationScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Simulation Scenario",
)
async def create_scenario(
    data: SimulationScenarioCreate,
    db: AsyncSession = Depends(get_db),
) -> SimulationScenarioResponse:
    service = SimulationScenarioService(db)
    try:
        created = await service.create_scenario(data)
        return SimulationScenarioResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{scenario_id}",
    response_model=SimulationScenarioResponse,
    summary="Get Simulation Scenario Details",
)
async def get_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SimulationScenarioResponse:
    service = SimulationScenarioService(db)
    sc = await service.get_scenario(scenario_id)
    if not sc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SimulationScenario {scenario_id} not found")
    return SimulationScenarioResponse.model_validate(sc)


@router.post(
    "/{scenario_id}/activate",
    response_model=SimulationScenarioResponse,
    summary="Activate Simulation Scenario in Building",
)
async def activate_scenario(
    scenario_id: uuid.UUID,
    building_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> SimulationScenarioResponse:
    service = SimulationScenarioService(db)
    try:
        activated = await service.activate_scenario(scenario_id, building_id)
        return SimulationScenarioResponse.model_validate(activated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
