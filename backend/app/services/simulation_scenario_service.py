"""Simulation scenario domain service for stress & failure injection testing."""

import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import SimulationScenario
from app.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.schemas.configuration import SimulationScenarioCreate


class SimulationScenarioService:
    """Manages digital-twin disturbance and failure simulation scenarios."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SimulationScenarioRepository(session)

    async def create_scenario(self, data: SimulationScenarioCreate) -> SimulationScenario:
        """Create a new disturbance scenario."""
        if data.duration_seconds <= 0:
            raise ValueError("Scenario duration must be strictly positive")

        scenario = SimulationScenario(
            building_id=data.building_id,
            name=data.name,
            scenario_type=data.scenario_type.value,
            duration_seconds=data.duration_seconds,
            severity=data.severity,
            injected_parameters=data.injected_parameters or {},
            expected_behavior=data.expected_behavior,
            is_active=False,
        )
        return await self.repo.create(scenario)

    async def activate_scenario(self, scenario_id: uuid.UUID, building_id: uuid.UUID) -> Optional[SimulationScenario]:
        """Activate a scenario in the digital twin while deactivating any previously active scenario."""
        scenario = await self.repo.get_by_id(scenario_id)
        if not scenario:
            raise ValueError(f"SimulationScenario {scenario_id} not found")
        if scenario.building_id != building_id:
            raise ValueError(f"Scenario {scenario_id} does not belong to building {building_id}")

        return await self.repo.activate_scenario(scenario_id, building_id)

    async def get_active_scenario(self, building_id: uuid.UUID) -> Optional[SimulationScenario]:
        return await self.repo.get_active_scenario(building_id)

    async def get_scenario(self, scenario_id: uuid.UUID) -> Optional[SimulationScenario]:
        return await self.repo.get_by_id(scenario_id)

    async def list_scenarios(self, building_id: uuid.UUID) -> Sequence[SimulationScenario]:
        return await self.repo.list_by_building(building_id)

