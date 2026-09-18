"""Audit Trail REST API endpoints."""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import (
    get_current_user,
    require_permission,
    PERM_AUDIT_READ,
)
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService

logger = logging.getLogger("risk2relief.api.audit")

router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Query Audit Logs",
    description="Paginated audit trail of security, configuration, and operational events (requires audit:read permission).",
)
async def query_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    result: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(require_permission(PERM_AUDIT_READ)),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditLogResponse]:
    """Retrieve filtered audit trail records."""
    service = AuditService(session)
    items, total = await service.query_logs(
        actor=actor,
        action=action,
        resource=resource,
        result=result,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
