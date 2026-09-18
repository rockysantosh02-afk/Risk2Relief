"""Repository for database health and heartbeat verification."""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal

logger = logging.getLogger("risk2relief.health_repository")


class HealthRepository:
    """Encapsulates database health ping and operational checks."""

    def __init__(self, session: AsyncSession = None):
        self._session = session

    async def ping_database(self) -> str:
        """Executes a lightweight ping on PostgreSQL."""
        try:
            if self._session:
                await self._session.execute(text("SELECT 1"))
                return "connected"
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return "connected"
        except Exception as exc:
            logger.debug(f"Database ping unsuccessful: {exc}")
            return "disconnected"
