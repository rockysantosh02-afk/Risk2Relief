"""Unit tests for digital-twin SimulationScenario entities and scenario activation."""

import uuid
import pytest
from app.models.building import Building
from app.models.configuration import SimulationScenario
from app.repositories.simulation_scenario_repository import SimulationScenarioRepository


@pytest.mark.asyncio
async def test_simulation_scenario_lifecycle_and_switching(db_session):
    """Verify scenario creation, parameter injection, and dynamic scenario activation."""
    building = Building(name="Scenario Sim Facility", code="BLD-SIM-01")
    db_session.add(building)
    await db_session.flush()

    repo = SimulationScenarioRepository(db_session)

    # 1. Create baseline scenario
    scen_normal = SimulationScenario(
        building_id=building.id,
        name="Baseline Normal Operation",
        scenario_type="NORMAL",
        duration_seconds=600,
        severity="LOW",
        is_active=True,
    )
    await repo.create(scen_normal)

    active = await repo.get_active_scenario(building.id)
    assert active is not None
    assert active.id == scen_normal.id
    assert active.scenario_type == "NORMAL"

    # 2. Create emergency scenario
    scen_overload = SimulationScenario(
        building_id=building.id,
        name="Seismic Overload Test",
        scenario_type="STRUCTURAL_OVERLOAD",
        duration_seconds=300,
        severity="CRITICAL",
        injected_parameters={"overload_factor": 1.5, "target_zone": "CORE"},
        is_active=False,
    )
    await repo.create(scen_overload)

    # 3. Activate the emergency scenario
    activated = await repo.activate_scenario(scen_overload.id, building.id)
    assert activated.is_active is True

    # 4. Verify previous scenario is deactivated
    active_now = await repo.get_active_scenario(building.id)
    assert active_now.id == scen_overload.id
    assert active_now.scenario_type == "STRUCTURAL_OVERLOAD"

    # Refresh normal scenario to check state
    await db_session.refresh(scen_normal)
    assert scen_normal.is_active is False
