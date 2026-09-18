"""Audit logging domain SQLAlchemy 2.x model for security and business events."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    DateTime,
    JSON,
    Uuid,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Audit log entry for tracking security, operational, and administrative actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_actor_action", "actor", "action"),
        Index("ix_audit_logs_timestamp_result", "timestamp", "result"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, actor='{self.actor}', action='{self.action}', result='{self.result}')>"
