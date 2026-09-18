"""Incident & Alert Management Subsystem.

Tracks safety incidents, logs evidence, coordinates simulated containment recommendations,
and dispatches digital-twin alert notifications.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


@dataclass
class AlertNotification:
    """Dispatched alert envelope for dashboard subscriptions and operator logs."""
    alert_id: str
    building_id: str
    severity: str
    event_type: str
    message: str
    state_transition: Optional[str]
    recommended_simulated_action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered: bool = True


class AlertService:
    """Dispatches in-app, WebSocket, and audit log alert notifications."""

    def __init__(self):
        self.dispatched_alerts: List[AlertNotification] = []

    def dispatch_alert(
        self,
        building_id: str,
        severity: str,
        event_type: str,
        message: str,
        state_transition: Optional[str] = None,
        recommended_simulated_action: Optional[str] = None,
    ) -> AlertNotification:
        """Create and publish an auditable alert notification."""
        action = recommended_simulated_action or (
            "Initiate simulated nodal load re-balancing and alert facility engineering."
        )
        alert = AlertNotification(
            alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
            building_id=str(building_id),
            severity=severity.upper(),
            event_type=event_type,
            message=message,
            state_transition=state_transition,
            recommended_simulated_action=action,
        )
        self.dispatched_alerts.append(alert)
        return alert

    def get_recent_alerts(self, limit: int = 50) -> List[AlertNotification]:
        """Return recently dispatched alerts."""
        return self.dispatched_alerts[-limit:]


class IncidentService:
    """Domain service managing incident lifecycles and containment recommendations."""

    @staticmethod
    def generate_containment_recommendation(
        severity: str,
        escalated_state: str,
        cause: Optional[str] = None,
    ) -> str:
        """Generate deterministic simulated containment recommendations."""
        sev = severity.upper()
        state = escalated_state.upper()

        if state == "EMERGENCY" or sev == "CRITICAL":
            return (
                "EMERGENCY SIMULATION CONTAINMENT: "
                "1. Trigger simulated localized zone egress alarms. "
                "2. Cut off non-essential simulated live loads. "
                "3. Transfer active anti-gravity nodal offload vectors to foundation-bearing columns."
            )
        elif state == "DEGRADED" or sev == "HIGH":
            return (
                "HIGH PRIORITY CONTAINMENT: "
                "1. Increase sensor telemetry polling to 50 Hz. "
                "2. Rebalance simulated anti-gravity force vectors away from degraded quadrants. "
                "3. Request on-site physical non-destructive ultrasonic column testing."
            )
        elif state == "WARNING" or sev == "MEDIUM":
            return (
                "WARNING PROTOCOL: "
                "1. Maintain continuous background observation. "
                "2. Check sensor calibration drift and communication channel packet loss."
            )
        return "Nominal operational state. No simulated containment action required."
