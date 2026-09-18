"""Repository for digital-twin SimulationScenario entities."""

import uuid
from typing import Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import SimulationScenario
from app.repositories.base import BaseRepository


class SimulationScenarioRepository(BaseRepository[SimulationScenario]):
    """Data access repository for simulation scenarios."""

    def __init__(self, session: AsyncSession):
        super().__init__(SimulationScenario, session)

    async def list_by_building(self, building_id: uuid.UUID) -> Sequence[SimulationScenario]:
        result = await self.session.execute(
            select(SimulationScenario)
            .where(SimulationScenario.building_id == building_id)
            .order_by(SimulationScenario.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_scenario(self, building_id: uuid.UUID) -> Optional[SimulationScenario]:
        result = await self.session.execute(
            select(SimulationScenario).where(
                SimulationScenario.building_id == building_id,
                SimulationScenario.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def activate_scenario(self, scenario_id: uuid.UUID, building_id: uuid.UUID) -> Optional[SimulationScenario]:
        """Deactivate all active scenarios for the building and activate the specified scenario."""
        # Deactivate current active scenarios
        await self.session.execute(
            update(SimulationScenario)
            .where(SimulationScenario.building_id == building_id)
            .values(is_active=False)
        )
        # Activate target scenario
        target = await self.get_by_id(scenario_id)
        if target:
            target.is_active = True
            await self.session.flush()
            await self.session.refresh(target)
        return target
