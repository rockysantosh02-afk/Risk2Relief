"""API v1 Digital-Twin Simulation & Physics Engine Endpoints."""

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.simulation_engine import SimulationEngineService
from app.services.simulation_service import SimulationResultService
from app.schemas.simulation import (
    SimulationStatusResponse,
    SimulationExecuteRequest,
    SimulationRunResponse,
    SimulationRunDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.physics.gravity_engine import (
    PureGravityEngine,
    Coordinate3D,
    GravityNodeState,
    FieldEvaluationPoint,
)

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.get(
    "/status",
    response_model=SimulationStatusResponse,
    summary="Get Digital-Twin Simulation Status & Safety Invariants",
    description="Returns the status of the physics simulation subsystem and validates hardware isolation barriers.",
)
async def get_simulation_status() -> SimulationStatusResponse:
    service = SimulationEngineService()
    return service.get_status()


@router.post(
    "/{building_id}/execute",
    response_model=SimulationRunDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute In-Silico Physics Simulation Run",
    description="Runs a multi-step digital-twin physics simulation under specified disturbance scenarios and persists results.",
)
async def execute_simulation_run(
    building_id: uuid.UUID,
    request: SimulationExecuteRequest,
    db: AsyncSession = Depends(get_db),
) -> SimulationRunDetailResponse:
    service = SimulationResultService(db)
    try:
        run = await service.execute_and_persist_run(building_id=building_id, request=request)
        return SimulationRunDetailResponse.model_validate(run)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/runs",
    response_model=PaginatedResponse[SimulationRunResponse],
    summary="List Simulation Runs",
    description="Retrieve paginated history of executed digital-twin simulation runs.",
)
async def list_simulation_runs(
    building_id: Optional[uuid.UUID] = Query(default=None),
    scenario_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SimulationRunResponse]:
    service = SimulationResultService(db)
    runs = await service.list_runs(building_id=building_id, scenario_type=scenario_type, limit=limit)
    total = len(runs)
    return PaginatedResponse.create(
        items=[SimulationRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=SimulationRunDetailResponse,
    summary="Get Simulation Run Details",
    description="Retrieve full step-by-step telemetry snapshots and generated safety events for a simulation run.",
)
async def get_simulation_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SimulationRunDetailResponse:
    service = SimulationResultService(db)
    run = await service.get_run_details(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SimulationRun {run_id} not found")
    return SimulationRunDetailResponse.model_validate(run)


@router.post(
    "/gravity/field",
    summary="Calculate 3D Gravitational Field Superposition",
    description="Pure mathematical computation of spatial field attenuation and offset percentages over evaluation coordinates.",
)
async def calculate_gravity_field(
    nodes: List[Dict[str, Any]],
    eval_points: List[Dict[str, Any]],
    target_offset_percentage: float = Query(default=15.0, ge=0.0, le=50.0),
) -> Dict[str, Any]:
    """Pure computational gravity field calculation endpoint."""
    node_states = [
        GravityNodeState(
            node_id=n.get("node_id", f"node-{idx}"),
            identifier=n.get("identifier", f"AG-{idx}"),
            position=Coordinate3D(
                x=float(n.get("x", 0.0)),
                y=float(n.get("y", 0.0)),
                z=float(n.get("z", 0.0)),
            ),
            nominal_capacity_kn=float(n.get("capacity_kn", 600.0)),
            operating_state="ACTIVE" if n.get("is_active", True) else "FAILED",
            health_score=float(n.get("health_score", 100.0)),
            efficiency=float(n.get("efficiency", 1.0)),
        )
        for idx, n in enumerate(nodes)
    ]

    points = [
        FieldEvaluationPoint(
            point_id=p.get("point_id", f"pt-{idx}"),
            position=Coordinate3D(
                x=float(p.get("x", 0.0)),
                y=float(p.get("y", 0.0)),
                z=float(p.get("z", 0.0)),
            ),
        )
        for idx, p in enumerate(eval_points)
    ]

    field_state = PureGravityEngine.calculate_field(
        node_states, points, target_offset_percentage=target_offset_percentage
    )

    return {
        "mean_offset_percentage": field_state.mean_offset_percentage,
        "target_deviation_percentage": field_state.target_deviation_percentage,
        "field_uniformity": field_state.field_uniformity,
        "point_count": len(field_state.evaluation_points),
        "active_nodes": len([n for n in node_states if n.is_active]),
        "total_compensation_kn": field_state.total_field_relief_kn,
        "disclaimer": "In-silico pure mathematical calculation. No physical hardware commanded.",
    }

