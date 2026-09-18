"""Audit repository for recording and querying security/operational events."""

import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.audit import AuditLog


class AuditRepository:
    """Repository handling AuditLog entry persistence and filtering."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log_entry: AuditLog) -> AuditLog:
        """Persist a new audit log record."""
        self.session.add(log_entry)
        await self.session.flush()
        await self.session.refresh(log_entry)
        return log_entry

    async def query(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """Query audit log records with filtering and pagination."""
        stmt = select(AuditLog)
        count_stmt = select(func.count(AuditLog.id))

        if actor:
            stmt = stmt.where(AuditLog.actor == actor)
            count_stmt = count_stmt.where(AuditLog.actor == actor)
        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)
        if resource:
            stmt = stmt.where(AuditLog.resource == resource)
            count_stmt = count_stmt.where(AuditLog.resource == resource)
        if result:
            stmt = stmt.where(AuditLog.result == result)
            count_stmt = count_stmt.where(AuditLog.result == result)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
            count_stmt = count_stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)
            count_stmt = count_stmt.where(AuditLog.timestamp <= end_time)

        total = await self.session.scalar(count_stmt) or 0
        stmt = (
            stmt.order_by(AuditLog.timestamp.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total
