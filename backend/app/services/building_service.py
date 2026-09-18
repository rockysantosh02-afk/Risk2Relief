"""Building management domain service.

Contains domain validation rules for buildings, floor hierarchy, and structural/simulation nodes.
"""

import uuid
from typing import Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import (
    Building,
    BuildingFloor,
    BuildingZone,
    StructuralNode,
    AntiGravityNode,
)
from app.repositories.building_repository import BuildingRepository
from app.schemas.building import BuildingCreate, FloorCreate, ZoneCreate
from app.schemas.node import StructuralNodeCreate, AntiGravityNodeCreate


class BuildingService:
    """Orchestrates building lifecycle, hierarchy validation, and node registration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BuildingRepository(session)

    async def create_building(self, data: BuildingCreate) -> Building:
        """Validate uniqueness of code and create a new building."""
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ValueError(f"Building with code '{data.code}' already exists")
        if data.number_of_floors < 1:
            raise ValueError("Building must have at least 1 floor")

        building = Building(
            name=data.name,
            code=data.code,
            description=data.description,
            location=data.location,
            status=data.status,
            number_of_floors=data.number_of_floors,
            metadata_json=data.metadata_json or {},
        )
        return await self.repo.create(building)

    async def list_buildings(
        self,
        page: int = 1,
        limit: int = 50,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[Sequence[Building], int]:
        offset = (page - 1) * limit
        return await self.repo.list_buildings(limit=limit, offset=offset, status=status, search=search)

    async def update_building(self, building_id: uuid.UUID, data) -> Optional[Building]:
        bld = await self.repo.get_by_id(building_id)
        if not bld:
            return None
        if data.name is not None:
            bld.name = data.name
        if data.description is not None:
            bld.description = data.description
        if data.location is not None:
            bld.location = data.location
        if data.status is not None:
            bld.status = data.status.upper()
        if data.number_of_floors is not None:
            bld.number_of_floors = data.number_of_floors
        if data.metadata_json is not None:
            bld.metadata_json = data.metadata_json
        await self.session.flush()
        await self.session.refresh(bld)
        return bld

    async def delete_building(self, building_id: uuid.UUID) -> bool:
        return await self.repo.delete_building(building_id)

    async def get_building(self, building_id: uuid.UUID) -> Optional[Building]:
        return await self.repo.get_by_id(building_id)

    async def get_building_hierarchy(self, building_id: uuid.UUID) -> Optional[Building]:
        """Retrieve building with complete eager hierarchy."""
        return await self.repo.get_with_hierarchy(building_id)

    async def list_floors(self, building_id: uuid.UUID) -> Sequence[BuildingFloor]:
        return await self.repo.list_floors(building_id)

    async def get_floor(self, floor_id: uuid.UUID) -> Optional[BuildingFloor]:
        return await self.repo.get_floor_by_id(floor_id)

    async def list_zones(self, floor_id: uuid.UUID) -> Sequence[BuildingZone]:
        return await self.repo.list_zones_by_floor(floor_id)

    async def get_zone(self, zone_id: uuid.UUID) -> Optional[BuildingZone]:
        return await self.repo.get_zone_by_id(zone_id)

    async def list_structural_nodes(self, zone_id: uuid.UUID) -> Sequence[StructuralNode]:
        return await self.repo.list_structural_nodes_by_zone(zone_id)

    async def get_structural_node(self, node_id: uuid.UUID) -> Optional[StructuralNode]:
        return await self.repo.get_structural_node_by_id(node_id)

    async def list_antigravity_nodes(self, building_id: uuid.UUID) -> Sequence[AntiGravityNode]:
        return await self.repo.list_antigravity_nodes(building_id)

    async def get_antigravity_node(self, node_id: uuid.UUID) -> Optional[AntiGravityNode]:
        return await self.repo.get_antigravity_node_by_id(node_id)


    async def add_floor(self, building_id: uuid.UUID, data: FloorCreate) -> BuildingFloor:
        """Validate floor number uniqueness within building and attach floor."""
        building = await self.repo.get_by_id(building_id)
        if not building:
            raise ValueError(f"Building {building_id} not found")

        existing_floor = await self.repo.get_floor_by_number(building_id, data.floor_number)
        if existing_floor:
            raise ValueError(f"Floor {data.floor_number} already exists in building {building_id}")

        floor = BuildingFloor(
            building_id=building_id,
            floor_number=data.floor_number,
            name=data.name,
            elevation_meters=data.elevation_meters,
            metadata_json=data.metadata_json or {},
        )
        return await self.repo.add_floor(floor)

    async def add_zone(self, floor_id: uuid.UUID, data: ZoneCreate) -> BuildingZone:
        """Validate zone code uniqueness within floor and attach zone."""
        if data.area_sqm < 0:
            raise ValueError("Zone area cannot be negative")

        existing_zone = await self.repo.get_zone_by_code(floor_id, data.zone_code)
        if existing_zone:
            raise ValueError(f"Zone '{data.zone_code}' already exists on floor {floor_id}")

        zone = BuildingZone(
            floor_id=floor_id,
            zone_code=data.zone_code,
            name=data.name,
            zone_type=data.zone_type,
            area_sqm=data.area_sqm,
            metadata_json=data.metadata_json or {},
        )
        return await self.repo.add_zone(zone)

    async def register_structural_node(self, data: StructuralNodeCreate) -> StructuralNode:
        """Register a structural column, beam, or monitored point."""
        node = StructuralNode(
            building_id=data.building_id,
            floor_id=data.floor_id,
            zone_id=data.zone_id,
            node_code=data.node_code,
            node_type=data.node_type.value,
            position_x=data.position_x,
            position_y=data.position_y,
            position_z=data.position_z,
            health_status=data.health_status,
            baseline_parameters=data.baseline_parameters or {},
            node_metadata=data.node_metadata or {},
        )
        return await self.repo.add_structural_node(node)

    async def register_antigravity_node(self, data: AntiGravityNodeCreate) -> AntiGravityNode:
        """Register an in-silico simulated anti-gravity compensation node."""
        existing = await self.repo.get_antigravity_node_by_identifier(data.node_identifier)
        if existing:
            raise ValueError(f"AntiGravityNode '{data.node_identifier}' already exists")

        ag_node = AntiGravityNode(
            building_id=data.building_id,
            zone_id=data.zone_id,
            node_identifier=data.node_identifier,
            name=data.name,
            position_x=data.position_x,
            position_y=data.position_y,
            position_z=data.position_z,
            nominal_field_strength_kn=data.nominal_field_strength_kn,
            operating_state=data.operating_state.value,
            health_score=data.health_score,
            efficiency=data.efficiency,
            is_simulated="true",  # Hard invariant: digital-twin simulation only
            simulation_parameters=data.simulation_parameters or {},
            configuration_json=data.configuration_json or {},
        )
        return await self.repo.add_antigravity_node(ag_node)
