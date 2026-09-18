"""Repository for Building, Floor, Zone, and Node domain entities.

Optimized with selectinload to prevent N+1 queries on hierarchy traversals.
"""

import uuid
from typing import Optional, Sequence, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import (
    Building,
    BuildingFloor,
    BuildingZone,
    StructuralNode,
    AntiGravityNode,
)
from app.repositories.base import BaseRepository


class BuildingRepository(BaseRepository[Building]):
    """Repository handling persistence for buildings and their structural components."""

    def __init__(self, session: AsyncSession):
        super().__init__(Building, session)

    async def get_by_code(self, code: str) -> Optional[Building]:
        """Lookup building by its unique code."""
        result = await self.session.execute(
            select(Building).where(Building.code == code)
        )
        return result.scalar_one_or_none()

    async def get_with_hierarchy(self, building_id: uuid.UUID) -> Optional[Building]:
        """Fetch building with all floors, zones, and nodes loaded eagerly without N+1 queries."""
        stmt = (
            select(Building)
            .options(
                selectinload(Building.floors).selectinload(BuildingFloor.zones).selectinload(BuildingZone.structural_nodes),
                selectinload(Building.structural_nodes),
                selectinload(Building.antigravity_nodes),
            )
            .where(Building.id == building_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_floor(self, floor: BuildingFloor) -> BuildingFloor:
        self.session.add(floor)
        await self.session.flush()
        await self.session.refresh(floor)
        floor.zones = []
        return floor

    async def get_floor_by_number(self, building_id: uuid.UUID, floor_number: int) -> Optional[BuildingFloor]:
        result = await self.session.execute(
            select(BuildingFloor).where(
                BuildingFloor.building_id == building_id,
                BuildingFloor.floor_number == floor_number,
            )
        )
        return result.scalar_one_or_none()

    async def list_floors(self, building_id: uuid.UUID) -> Sequence[BuildingFloor]:
        result = await self.session.execute(
            select(BuildingFloor)
            .options(selectinload(BuildingFloor.zones))
            .where(BuildingFloor.building_id == building_id)
            .order_by(BuildingFloor.floor_number)
        )
        return result.scalars().all()

    async def add_zone(self, zone: BuildingZone) -> BuildingZone:
        self.session.add(zone)
        await self.session.flush()
        await self.session.refresh(zone)
        return zone

    async def get_zone_by_code(self, floor_id: uuid.UUID, zone_code: str) -> Optional[BuildingZone]:
        result = await self.session.execute(
            select(BuildingZone).where(
                BuildingZone.floor_id == floor_id,
                BuildingZone.zone_code == zone_code,
            )
        )
        return result.scalar_one_or_none()

    async def add_structural_node(self, node: StructuralNode) -> StructuralNode:
        self.session.add(node)
        await self.session.flush()
        await self.session.refresh(node)
        return node

    async def list_structural_nodes_by_zone(self, zone_id: uuid.UUID) -> Sequence[StructuralNode]:
        result = await self.session.execute(
            select(StructuralNode).where(StructuralNode.zone_id == zone_id)
        )
        return result.scalars().all()

    async def list_buildings(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[Sequence[Building], int]:
        """List buildings with pagination, status filtering, and keyword search."""
        from sqlalchemy import func
        query = select(Building)
        count_query = select(func.count(Building.id))

        if status:
            query = query.where(Building.status == status.upper())
            count_query = count_query.where(Building.status == status.upper())
        if search:
            pattern = f"%{search}%"
            query = query.where((Building.name.ilike(pattern)) | (Building.code.ilike(pattern)))
            count_query = count_query.where((Building.name.ilike(pattern)) | (Building.code.ilike(pattern)))

        total_res = await self.session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(Building.name).offset(offset).limit(limit)
        res = await self.session.execute(query)
        return res.scalars().all(), total

    async def delete_building(self, building_id: uuid.UUID) -> bool:
        """Delete building and cascading children."""
        bld = await self.get_by_id(building_id)
        if not bld:
            return False
        await self.session.delete(bld)
        await self.session.flush()
        return True

    async def get_floor_by_id(self, floor_id: uuid.UUID) -> Optional[BuildingFloor]:
        res = await self.session.execute(
            select(BuildingFloor).options(selectinload(BuildingFloor.zones)).where(BuildingFloor.id == floor_id)
        )
        return res.scalar_one_or_none()

    async def list_zones_by_floor(self, floor_id: uuid.UUID) -> Sequence[BuildingZone]:
        res = await self.session.execute(
            select(BuildingZone).where(BuildingZone.floor_id == floor_id).order_by(BuildingZone.zone_code)
        )
        return res.scalars().all()

    async def get_zone_by_id(self, zone_id: uuid.UUID) -> Optional[BuildingZone]:
        res = await self.session.execute(
            select(BuildingZone).where(BuildingZone.id == zone_id)
        )
        return res.scalar_one_or_none()

    async def get_structural_node_by_id(self, node_id: uuid.UUID) -> Optional[StructuralNode]:
        res = await self.session.execute(
            select(StructuralNode).where(StructuralNode.id == node_id)
        )
        return res.scalar_one_or_none()

    async def get_antigravity_node_by_id(self, node_id: uuid.UUID) -> Optional[AntiGravityNode]:
        res = await self.session.execute(
            select(AntiGravityNode).where(AntiGravityNode.id == node_id)
        )
        return res.scalar_one_or_none()

    async def add_antigravity_node(self, ag_node: AntiGravityNode) -> AntiGravityNode:
        self.session.add(ag_node)
        await self.session.flush()
        await self.session.refresh(ag_node)
        return ag_node

    async def get_antigravity_node_by_identifier(self, identifier: str) -> Optional[AntiGravityNode]:
        result = await self.session.execute(
            select(AntiGravityNode).where(AntiGravityNode.node_identifier == identifier)
        )
        return result.scalar_one_or_none()

    async def list_antigravity_nodes(self, building_id: uuid.UUID) -> Sequence[AntiGravityNode]:
        result = await self.session.execute(
            select(AntiGravityNode).where(AntiGravityNode.building_id == building_id)
        )
        return result.scalars().all()

