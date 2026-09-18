"""API v1 Health Endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Get System Health Diagnostics",
    description="Inspect overall platform status and connectivity of database and cache dependencies."
)
async def get_v1_health(
    db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    """Delegates to HealthService to inspect dependencies and platform status."""
    service = HealthService(session=db)
    return await service.get_system_health()
