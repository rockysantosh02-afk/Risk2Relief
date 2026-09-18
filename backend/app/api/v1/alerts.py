"""API v1 Real-time Alerts and Notification Endpoints."""

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field
from app.safety.incidents import AlertService, AlertNotification
from app.websockets.manager import connection_manager

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

# In-memory shared alert service instance
_alert_service = AlertService()


class AlertDispatchRequest(BaseModel):
    building_id: uuid.UUID
    severity: str = Field(default="HIGH")
    event_type: str = Field(default="MANUAL_ALERT")
    message: str = Field(min_length=1)
    state_transition: Optional[str] = None
    recommended_simulated_action: Optional[str] = None


@router.get(
    "",
    summary="List Recent Alerts",
    description="Retrieve recently dispatched alert notifications for dashboard consumption.",
)
async def list_recent_alerts(
    limit: int = Query(default=50, ge=1, le=200),
) -> List[Dict[str, Any]]:
    alerts = _alert_service.get_recent_alerts(limit=limit)
    return [
        {
            "alert_id": a.alert_id,
            "building_id": a.building_id,
            "severity": a.severity,
            "event_type": a.event_type,
            "message": a.message,
            "state_transition": a.state_transition,
            "recommended_simulated_action": a.recommended_simulated_action,
            "timestamp": a.timestamp.isoformat(),
            "delivered": a.delivered,
        }
        for a in alerts
    ]


@router.post(
    "/dispatch",
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch Real-Time Alert",
    description="Publish an alert notification envelope and broadcast to real-time WebSocket subscribers.",
)
async def dispatch_alert(
    request: AlertDispatchRequest,
) -> Dict[str, Any]:
    alert = _alert_service.dispatch_alert(
        building_id=str(request.building_id),
        severity=request.severity,
        event_type=request.event_type,
        message=request.message,
        state_transition=request.state_transition,
        recommended_simulated_action=request.recommended_simulated_action,
    )

    # Broadcast to WebSocket 'alerts' channel
    await connection_manager.broadcast(
        channel="alerts",
        data={
            "alert_id": alert.alert_id,
            "building_id": alert.building_id,
            "severity": alert.severity,
            "message": alert.message,
            "action": alert.recommended_simulated_action,
        },
        building_id=str(request.building_id),
    )

    return {
        "alert_id": alert.alert_id,
        "building_id": alert.building_id,
        "severity": alert.severity,
        "message": alert.message,
        "timestamp": alert.timestamp.isoformat(),
    }
