"""Repository for Incident and SafetyStateTransition persistence."""

import uuid
from typing import Optional, Sequence, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.safety import Incident, SafetyStateTransitionRecord
from app.repositories.base import BaseRepository


class SafetyRepository(BaseRepository[Incident]):
    """Data access repository for incidents and auditable safety state transitions."""

    def __init__(self, session: AsyncSession):
        super().__init__(Incident, session)

    async def add_incident(self, incident: Incident) -> Incident:
        """Persist a new safety incident."""
        return await self.create(incident)

    async def get_incident_by_code(self, incident_code: str) -> Optional[Incident]:
        """Fetch incident by unique incident_code."""
        stmt = select(Incident).where(Incident.incident_code == incident_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        building_id: uuid.UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Incident]:
        """List incidents for a building with optional filtering."""
        stmt = (
            select(Incident)
            .where(Incident.building_id == building_id)
            .order_by(desc(Incident.opened_at))
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(Incident.status == status.upper())
        if severity:
            stmt = stmt.where(Incident.severity == severity.upper())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_transition_record(
        self, record: SafetyStateTransitionRecord
    ) -> SafetyStateTransitionRecord:
        """Persist an auditable state transition record."""
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def list_transition_records(
        self, building_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> Sequence[SafetyStateTransitionRecord]:
        """List state transitions for a building ordered by timestamp descending."""
        stmt = (
            select(SafetyStateTransitionRecord)
            .where(SafetyStateTransitionRecord.building_id == building_id)
            .order_by(desc(SafetyStateTransitionRecord.transitioned_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_current_safety_state(self, building_id: uuid.UUID) -> str:
        """Get the most recent safety state for a building (defaults to NORMAL)."""
        stmt = (
            select(SafetyStateTransitionRecord.to_state)
            .where(SafetyStateTransitionRecord.building_id == building_id)
            .order_by(desc(SafetyStateTransitionRecord.transitioned_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest = result.scalar_one_or_none()
        return latest or "NORMAL"
