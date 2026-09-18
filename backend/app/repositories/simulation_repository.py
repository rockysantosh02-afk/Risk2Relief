"""Repository for SimulationRun and SafetyEvent persistence."""

import uuid
from typing import Optional, Sequence, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.simulation import SimulationRun, SafetyEvent
from app.repositories.base import BaseRepository


class SimulationRepository(BaseRepository[SimulationRun]):
    """Data access repository for simulation history and safety events."""

    def __init__(self, session: AsyncSession):
        super().__init__(SimulationRun, session)

    async def add_simulation_run(self, run: SimulationRun) -> SimulationRun:
        """Persist a new simulation run record."""
        return await self.create(run)

    async def get_simulation_run_detail(self, run_id: uuid.UUID) -> Optional[SimulationRun]:
        """Fetch simulation run with eagerly loaded safety events."""
        stmt = (
            select(SimulationRun)
            .where(SimulationRun.id == run_id)
            .options(selectinload(SimulationRun.safety_events))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_simulation_runs(
        self, building_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> Sequence[SimulationRun]:
        """List simulation runs for a building ordered by completion time descending."""
        stmt = (
            select(SimulationRun)
            .where(SimulationRun.building_id == building_id)
            .order_by(desc(SimulationRun.end_time), desc(SimulationRun.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_simulation_run(self, building_id: uuid.UUID) -> Optional[SimulationRun]:
        """Get the most recent simulation run for a building."""
        stmt = (
            select(SimulationRun)
            .where(SimulationRun.building_id == building_id)
            .order_by(desc(SimulationRun.end_time), desc(SimulationRun.created_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_safety_event(self, event: SafetyEvent) -> SafetyEvent:
        """Persist a safety event record."""
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list_safety_events(
        self,
        building_id: uuid.UUID,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SafetyEvent]:
        """List safety events for a building with optional severity filter."""
        stmt = (
            select(SafetyEvent)
            .where(SafetyEvent.building_id == building_id)
            .order_by(desc(SafetyEvent.detected_at))
            .limit(limit)
            .offset(offset)
        )
        if severity:
            stmt = stmt.where(SafetyEvent.severity == severity.upper())

        result = await self.session.execute(stmt)
        return result.scalars().all()
