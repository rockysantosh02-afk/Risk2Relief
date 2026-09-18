"""Health check domain service aggregating dependency diagnostics."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import check_redis_health
from app.repositories.health_repository import HealthRepository
from app.schemas.health import HealthResponse, DependencyHealth

settings = get_settings()


class HealthService:
    """Orchestrates health status checks across backing resources."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.health_repo = HealthRepository(session=session)

    async def get_system_health(self) -> HealthResponse:
        """Collects health and dependency statuses safely without leaking secrets."""
        db_status = await self.health_repo.ping_database()
        redis_status = await check_redis_health()

        # Overall platform status determination
        overall_status = "ok"
        if db_status != "connected" or redis_status not in ("connected", "not_installed"):
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            service="risk2relief-api",
            version=settings.APP_VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dependencies=DependencyHealth(
                database=db_status,
                redis=redis_status
            )
        )
