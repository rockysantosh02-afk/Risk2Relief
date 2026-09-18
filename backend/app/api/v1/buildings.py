"""API v1 Building, Floor, Zone, and Node Management Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.building_service import BuildingService
from app.schemas.building import (
    BuildingCreate,
    BuildingUpdate,
    BuildingResponse,
    BuildingHierarchyResponse,
    FloorCreate,
    FloorResponse,
    ZoneCreate,
    ZoneResponse,
)
from app.schemas.node import (
    StructuralNodeCreate,
    StructuralNodeResponse,
    AntiGravityNodeCreate,
    AntiGravityNodeResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(tags=["Buildings & Hierarchy"])


# ==========================================
# 1. Building Endpoints
# ==========================================

@router.get(
    "/buildings",
    response_model=PaginatedResponse[BuildingResponse],
    summary="List Buildings",
    description="Retrieve paginated list of buildings with optional status and search filtering.",
)
async def list_buildings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BuildingResponse]:
    service = BuildingService(db)
    items, total = await service.list_buildings(page=page, limit=limit, status=status, search=search)
    return PaginatedResponse.create(
        items=[BuildingResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "/buildings",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Building",
    description="Register a new facility in the digital-twin platform.",
)
async def create_building(
    data: BuildingCreate,
    db: AsyncSession = Depends(get_db),
) -> BuildingResponse:
    service = BuildingService(db)
    try:
        created = await service.create_building(data)
        return BuildingResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/buildings/{building_id}",
    response_model=BuildingResponse,
    summary="Get Building",
    description="Retrieve facility details by unique identifier.",
)
async def get_building(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BuildingResponse:
    service = BuildingService(db)
    bld = await service.get_building(building_id)
    if not bld:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Building {building_id} not found")
    return BuildingResponse.model_validate(bld)


@router.put(
    "/buildings/{building_id}",
    response_model=BuildingResponse,
    summary="Update Building",
    description="Update facility metadata and configuration.",
)
async def update_building(
    building_id: uuid.UUID,
    data: BuildingUpdate,
    db: AsyncSession = Depends(get_db),
) -> BuildingResponse:
    service = BuildingService(db)
    updated = await service.update_building(building_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Building {building_id} not found")
    return BuildingResponse.model_validate(updated)


@router.delete(
    "/buildings/{building_id}",
    summary="Delete Building",
    description="Delete a facility and cascading floors, zones, and nodes.",
)
async def delete_building(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    service = BuildingService(db)
    deleted = await service.delete_building(building_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Building {building_id} not found")
    return {"deleted": True, "building_id": str(building_id)}


@router.get(
    "/buildings/{building_id}/hierarchy",
    response_model=BuildingHierarchyResponse,
    summary="Get Building Hierarchy",
    description="Retrieve facility with all floors and zones loaded eagerly.",
)
async def get_building_hierarchy(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BuildingHierarchyResponse:
    service = BuildingService(db)
    bld = await service.get_building_hierarchy(building_id)
    if not bld:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Building {building_id} not found")
    return BuildingHierarchyResponse.model_validate(bld)


# ==========================================
# 2. Floor & Zone Endpoints
# ==========================================

@router.get(
    "/buildings/{building_id}/floors",
    response_model=List[FloorResponse],
    summary="List Building Floors",
)
async def list_floors(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[FloorResponse]:
    service = BuildingService(db)
    floors = await service.list_floors(building_id)
    return [FloorResponse.model_validate(f) for f in floors]


@router.post(
    "/buildings/{building_id}/floors",
    response_model=FloorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Floor to Building",
)
async def add_floor(
    building_id: uuid.UUID,
    data: FloorCreate,
    db: AsyncSession = Depends(get_db),
) -> FloorResponse:
    service = BuildingService(db)
    try:
        created = await service.add_floor(building_id, data)
        return FloorResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/floors/{floor_id}",
    response_model=FloorResponse,
    summary="Get Floor Details",
)
async def get_floor(
    floor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FloorResponse:
    service = BuildingService(db)
    floor = await service.get_floor(floor_id)
    if not floor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Floor {floor_id} not found")
    return FloorResponse.model_validate(floor)


@router.get(
    "/floors/{floor_id}/zones",
    response_model=List[ZoneResponse],
    summary="List Zones on Floor",
)
async def list_zones(
    floor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ZoneResponse]:
    service = BuildingService(db)
    zones = await service.list_zones(floor_id)
    return [ZoneResponse.model_validate(z) for z in zones]


@router.post(
    "/floors/{floor_id}/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Zone to Floor",
)
async def add_zone(
    floor_id: uuid.UUID,
    data: ZoneCreate,
    db: AsyncSession = Depends(get_db),
) -> ZoneResponse:
    service = BuildingService(db)
    try:
        created = await service.add_zone(floor_id, data)
        return ZoneResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Get Zone Details",
)
async def get_zone(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ZoneResponse:
    service = BuildingService(db)
    zone = await service.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone {zone_id} not found")
    return ZoneResponse.model_validate(zone)


# ==========================================
# 3. Structural Node Endpoints
# ==========================================

@router.get(
    "/zones/{zone_id}/structural-nodes",
    response_model=List[StructuralNodeResponse],
    summary="List Structural Nodes in Zone",
)
async def list_structural_nodes(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[StructuralNodeResponse]:
    service = BuildingService(db)
    nodes = await service.list_structural_nodes(zone_id)
    return [StructuralNodeResponse.model_validate(n) for n in nodes]


@router.post(
    "/structural-nodes",
    response_model=StructuralNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Structural Node",
)
async def register_structural_node(
    data: StructuralNodeCreate,
    db: AsyncSession = Depends(get_db),
) -> StructuralNodeResponse:
    service = BuildingService(db)
    try:
        created = await service.register_structural_node(data)
        return StructuralNodeResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/structural-nodes/{node_id}",
    response_model=StructuralNodeResponse,
    summary="Get Structural Node",
)
async def get_structural_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StructuralNodeResponse:
    service = BuildingService(db)
    node = await service.get_structural_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StructuralNode {node_id} not found")
    return StructuralNodeResponse.model_validate(node)


# ==========================================
# 4. Anti-Gravity Node Endpoints (In-Silico Simulation Only)
# ==========================================

@router.get(
    "/buildings/{building_id}/antigravity-nodes",
    response_model=List[AntiGravityNodeResponse],
    summary="List Simulated Anti-Gravity Nodes",
    description="Returns simulated anti-gravity digital-twin calculation nodes.",
)
async def list_antigravity_nodes(
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[AntiGravityNodeResponse]:
    service = BuildingService(db)
    nodes = await service.list_antigravity_nodes(building_id)
    return [AntiGravityNodeResponse.model_validate(n) for n in nodes]


@router.post(
    "/antigravity-nodes",
    response_model=AntiGravityNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Simulated Anti-Gravity Node",
    description="Registers an in-silico simulated node. Hardware actuation is strictly forbidden.",
)
async def register_antigravity_node(
    data: AntiGravityNodeCreate,
    db: AsyncSession = Depends(get_db),
) -> AntiGravityNodeResponse:
    service = BuildingService(db)
    try:
        created = await service.register_antigravity_node(data)
        return AntiGravityNodeResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/antigravity-nodes/{node_id}",
    response_model=AntiGravityNodeResponse,
    summary="Get Simulated Anti-Gravity Node",
)
async def get_antigravity_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AntiGravityNodeResponse:
    service = BuildingService(db)
    node = await service.get_antigravity_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AntiGravityNode {node_id} not found")
    return AntiGravityNodeResponse.model_validate(node)
