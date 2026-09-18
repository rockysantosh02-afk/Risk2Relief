"""Audit logging service for registering and querying system and security events."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse

logger = logging.getLogger("risk2relief.audit")


class AuditService:
    """Service to capture, sanitize, and query audit trail records."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditRepository(session)

    async def record_event(
        self,
        actor: str,
        action: str,
        resource: str,
        result: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Record an auditable action."""
        try:
            entry = AuditLog(
                actor=actor,
                action=action,
                resource=resource,
                result=result,
                details_json=details or {},
                correlation_id=correlation_id,
                client_ip=client_ip,
            )
            created = await self.repo.create(entry)
            logger.info(f"AUDIT [{result}]: {actor} -> {action} on {resource}")
            return created
        except Exception as exc:
            # Audit recording should never crash business operations, but must be logged
            logger.error(f"Failed to record audit event: {exc}")
            return None

    async def query_logs(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[AuditLogResponse], int]:
        """Retrieve paginated audit entries."""
        records, total = await self.repo.query(
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size,
        )
        return [AuditLogResponse.model_validate(r) for r in records], total
