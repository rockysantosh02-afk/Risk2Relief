"""Unit tests for Building domain models, relationships, and constraints."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.building import (
    Building,
    BuildingFloor,
    BuildingZone,
    StructuralNode,
    AntiGravityNode,
)


@pytest.mark.asyncio
async def test_building_hierarchy_creation(db_session):
    """Verify end-to-end creation of building, floor, zone, and structural node."""
    # 1. Create Building
    building = Building(
        name="Apex Tower Alpha",
        code="BLD-APEX-01",
        description="High-rise test structure",
        location="Sector 7, Tech District",
        status="OPERATIONAL",
        number_of_floors=50,
    )
    db_session.add(building)
    await db_session.flush()

    assert building.id is not None
    assert building.created_at is not None

    # 2. Add Floor
    floor = BuildingFloor(
        building_id=building.id,
        floor_number=1,
        name="Ground Concourse",
        elevation_meters=0.0,
    )
    db_session.add(floor)
    await db_session.flush()

    assert floor.id is not None
    assert floor.building_id == building.id

    # 3. Add Zone
    zone = BuildingZone(
        floor_id=floor.id,
        zone_code="CORE-NORTH",
        name="North Elevator Core",
        zone_type="CORE",
        area_sqm=450.0,
    )
    db_session.add(zone)
    await db_session.flush()

    # 4. Add Structural Node
    node = StructuralNode(
        building_id=building.id,
        floor_id=floor.id,
        zone_id=zone.id,
        node_code="COL-CN-01",
        node_type="COLUMN",
        position_x=12.5,
        position_y=8.0,
        position_z=0.0,
        health_status="OPTIMAL",
    )
    db_session.add(node)
    await db_session.flush()

    # Query with full relationships
    result = await db_session.execute(
        select(Building)
        .options(
            selectinload(Building.floors)
            .selectinload(BuildingFloor.zones)
            .selectinload(BuildingZone.structural_nodes)
        )
        .where(Building.id == building.id)
    )
    queried_building = result.scalar_one()

    assert len(queried_building.floors) == 1
    assert queried_building.floors[0].floor_number == 1
    assert len(queried_building.floors[0].zones) == 1
    assert queried_building.floors[0].zones[0].zone_code == "CORE-NORTH"
    assert len(queried_building.floors[0].zones[0].structural_nodes) == 1
    assert queried_building.floors[0].zones[0].structural_nodes[0].node_code == "COL-CN-01"


@pytest.mark.asyncio
async def test_antigravity_node_in_silico_invariants(db_session):
    """Verify simulated anti-gravity nodes enforce in-silico isolation."""
    building = Building(name="Beta Complex", code="BLD-BETA-02", number_of_floors=20)
    db_session.add(building)
    await db_session.flush()

    ag_node = AntiGravityNode(
        building_id=building.id,
        node_identifier="AG-SIM-001",
        name="Virtual Load Offset Generator 1",
        position_x=0.0,
        position_y=0.0,
        position_z=75.0,
        nominal_field_strength_kn=750.0,
        operating_state="SIMULATED",
        is_simulated="true",
    )
    db_session.add(ag_node)
    await db_session.flush()

    assert ag_node.id is not None
    assert ag_node.is_simulated == "true"
    assert ag_node.operating_state == "SIMULATED"


@pytest.mark.asyncio
async def test_building_unique_code_constraint(db_session):
    """Verify that duplicate building codes trigger an integrity error."""
    b1 = Building(name="Tower A", code="BLD-DUP-01")
    db_session.add(b1)
    await db_session.flush()

    b2 = Building(name="Tower B", code="BLD-DUP-01")
    db_session.add(b2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_cascade_deletion(db_session):
    """Verify that deleting a building cascades and deletes floors, zones, and nodes."""
    b = Building(name="Tower Cascade", code="BLD-CASC-01")
    db_session.add(b)
    await db_session.flush()

    f = BuildingFloor(building_id=b.id, floor_number=1, name="F1")
    db_session.add(f)
    await db_session.flush()

    z = BuildingZone(floor_id=f.id, zone_code="Z1", name="Zone 1")
    db_session.add(z)
    await db_session.flush()

    n = StructuralNode(
        building_id=b.id, floor_id=f.id, zone_id=z.id, node_code="N1", node_type="COLUMN"
    )
    db_session.add(n)
    await db_session.flush()

    # Delete building
    await db_session.delete(b)
    await db_session.flush()

    # Verify children are deleted
    floor_res = await db_session.execute(select(BuildingFloor).where(BuildingFloor.id == f.id))
    assert floor_res.scalar_one_or_none() is None

    node_res = await db_session.execute(select(StructuralNode).where(StructuralNode.id == n.id))
    assert node_res.scalar_one_or_none() is None
