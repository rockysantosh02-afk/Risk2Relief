"""Integration tests for SimulationResultService and Database Persistence."""

import uuid
import pytest
from app.models.building import (
    Building,
    BuildingFloor,
    BuildingZone,
    StructuralNode,
    AntiGravityNode,
)
from app.schemas.simulation import SimulationExecuteRequest
from app.services.simulation_service import SimulationResultService


@pytest.mark.asyncio
async def test_simulation_service_lifecycle_and_persistence(db_session):
    """Verify full end-to-end simulation execution and persistence in database."""
    # 1. Setup building hierarchy
    bld = Building(name="Skyline Tower", code="SKY-01", number_of_floors=5)
    db_session.add(bld)
    await db_session.flush()

    floor = BuildingFloor(building_id=bld.id, floor_number=1, name="Level 1", elevation_meters=4.0)
    db_session.add(floor)
    await db_session.flush()

    zone = BuildingZone(floor_id=floor.id, zone_code="Z-MAIN", name="Main Core", area_sqm=500.0)
    db_session.add(zone)
    await db_session.flush()

    # Add Structural Node
    s_node = StructuralNode(
        building_id=bld.id,
        floor_id=floor.id,
        zone_id=zone.id,
        node_code="C-101",
        node_type="COLUMN",
        position_x=10.0,
        position_y=10.0,
        position_z=0.0,
    )
    db_session.add(s_node)

    # Add AntiGravityNode (Digital-Twin In-Silico Node)
    ag_node = AntiGravityNode(
        building_id=bld.id,
        zone_id=zone.id,
        node_identifier="AG-101",
        name="Simulated Anti-Gravity Node 101",
        position_x=10.0,
        position_y=10.0,
        position_z=0.0,
        nominal_field_strength_kn=600.0,
        operating_state="SIMULATED",
        is_simulated="true",
    )
    db_session.add(ag_node)
    await db_session.flush()

    # 2. Run NORMAL scenario simulation
    service = SimulationResultService(db_session)
    req = SimulationExecuteRequest(scenario_type="NORMAL", step_count=3, target_offset_percentage=15.0)

    saved_run, sim_result = await service.run_simulation(bld.id, req)

    assert saved_run.id is not None
    assert saved_run.building_id == bld.id
    assert saved_run.scenario_type == "NORMAL"
    assert saved_run.status == "COMPLETED"
    assert saved_run.step_count == 3
    assert saved_run.peak_risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert len(saved_run.step_results_json) == 3

    # 3. Query simulation detail
    fetched_run = await service.get_simulation_run(saved_run.id)
    assert fetched_run is not None
    assert fetched_run.id == saved_run.id

    # 4. List runs
    runs = await service.list_simulation_runs(bld.id)
    assert len(runs) >= 1
    assert runs[0].id == saved_run.id

    # 5. Run EMERGENCY scenario to trigger safety events
    req_emerg = SimulationExecuteRequest(scenario_type="EMERGENCY", step_count=2)
    saved_emerg, emerg_res = await service.run_simulation(bld.id, req_emerg)

    assert saved_emerg.scenario_type == "EMERGENCY"
    assert saved_emerg.peak_risk_level in ("HIGH", "CRITICAL")

    # 6. Verify safety events logged to database
    events = await service.list_safety_events(bld.id)
    assert len(events) >= 1

    # 7. Query latest risk summary
    summary = await service.get_latest_risk_summary(bld.id)
    assert summary is not None
    assert summary["scenario_type"] == "EMERGENCY"
    assert summary["peak_risk_level"] in ("HIGH", "CRITICAL")
