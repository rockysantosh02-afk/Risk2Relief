"""Audit log schemas for security and operational monitoring."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Audit log entry schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime
    actor: str
    action: str
    resource: str
    result: str
    correlation_id: Optional[str] = None
    client_ip: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = None


class AuditLogFilterParams(BaseModel):
    """Filter parameters for querying audit logs."""
    actor: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    result: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
