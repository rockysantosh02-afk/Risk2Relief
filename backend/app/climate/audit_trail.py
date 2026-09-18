"""Decision Audit Trail Service for Parametric Climate Insurance.

Maintains an immutable, sequential audit trail of every stage in the telemetry-to-settlement pipeline.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any


@dataclass
class ClimateAuditEvent:
    """Discrete audit log entry for a pipeline lifecycle stage."""
    id: str
    event_identifier: str
    policy_id: Optional[str]
    stage: str                          # DATA_RECEIVED, VALIDATION, ML_ANOMALY_CHECK, CONSENSUS, TRIGGER_EVALUATION, SETTLEMENT_COMPLETED, ...
    status: str                         # SUCCESS, WARNING, FAILED, BLOCKED, COMPLETED
    title: str
    message: str
    actor: str = "RISK2RELIEF_ENGINE"
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ClimateAuditTrailService:
    """In-memory and persistent decision audit trail manager."""

    _audit_events: List[ClimateAuditEvent] = []

    @classmethod
    def record_stage(
        cls,
        event_identifier: str,
        stage: str,
        status: str,
        title: str,
        message: str,
        policy_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClimateAuditEvent:
        """Append an auditable event to the timeline."""
        event = ClimateAuditEvent(
            id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            event_identifier=event_identifier,
            policy_id=policy_id,
            stage=stage,
            status=status.upper(),
            title=title,
            message=message,
            actor="RISK2RELIEF_RELIABILITY_ENGINE",
            correlation_id=correlation_id or str(uuid.uuid4()),
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )
        cls._audit_events.append(event)
        return event

    @classmethod
    def get_events_for_climate_event(cls, event_identifier: str) -> List[ClimateAuditEvent]:
        """Fetch chronological audit history for a specific climate event."""
        return [e for e in cls._audit_events if e.event_identifier == event_identifier]

    @classmethod
    def get_all_events(cls, limit: int = 100) -> List[ClimateAuditEvent]:
        """Return global audit log."""
        return cls._audit_events[-limit:]

    @classmethod
    def reset_audit_log(cls) -> None:
        """Clear audit history for demo resets."""
        cls._audit_events.clear()
