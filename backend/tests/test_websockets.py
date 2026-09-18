"""Unit and integration tests for real-time WebSockets and pub/sub broadcasting."""

import json
import pytest
from starlette.testclient import TestClient
from app.websockets.manager import connection_manager


def test_websocket_connection_and_heartbeat(client: TestClient):
    """Verify WebSocket handshake, connected acknowledgment, and ping/pong heartbeat."""
    with client.websocket_connect("/api/v1/ws") as ws:
        # 1. Connected acknowledgment
        ack_text = ws.receive_text()
        ack = json.loads(ack_text)
        assert ack["type"] == "connected"
        assert "available_channels" in ack
        assert "telemetry" in ack["available_channels"]

        # 2. Ping-pong heartbeat
        ws.send_text(json.dumps({"type": "ping", "echo": "test-heartbeat"}))
        pong_text = ws.receive_text()
        pong = json.loads(pong_text)
        assert pong["type"] == "pong"
        assert pong["echo"] == "test-heartbeat"
        assert "timestamp" in pong


def test_websocket_authentication_and_subscription(client: TestClient):
    """Verify auth frame and channel subscriptions."""
    with client.websocket_connect("/api/v1/ws") as ws:
        ws.receive_text()  # Consume connect ack

        # 1. Auth frame
        ws.send_text(json.dumps({"action": "auth", "token": "operator-session-token"}))
        auth_ack = json.loads(ws.receive_text())
        assert auth_ack["type"] == "auth_result"
        assert auth_ack["authenticated"] is True

        # 2. Subscription to 'safety' channel
        ws.send_text(json.dumps({"action": "subscribe", "channel": "safety", "building_id": "BLD-01"}))
        sub_ack = json.loads(ws.receive_text())
        assert sub_ack["type"] == "subscription_ack"
        assert sub_ack["channel"] == "safety"
        assert sub_ack["status"] == "subscribed"

        # 3. Unsubscribe
        ws.send_text(json.dumps({"action": "unsubscribe", "channel": "safety"}))
        unsub_ack = json.loads(ws.receive_text())
        assert unsub_ack["type"] == "unsubscribe_ack"
        assert unsub_ack["status"] == "unsubscribed"


@pytest.mark.asyncio
async def test_websocket_broadcast_delivery(client: TestClient):
    """Verify that broadcasting messages delivers framed events with monotonic sequence numbers."""
    with client.websocket_connect("/api/v1/ws?token=valid_token") as ws:
        ws.receive_text()  # Connect ack

        # Subscribe to alerts channel
        ws.send_text(json.dumps({"action": "subscribe", "channel": "alerts"}))
        ws.receive_text()  # Subscription ack

        # Broadcast test event via connection_manager
        await connection_manager.broadcast(
            channel="alerts",
            data={"alert_title": "Field Deviation Warning", "severity": "WARNING"},
        )

        # Receive dispatched event frame
        event_text = ws.receive_text()
        event_frame = json.loads(event_text)
        assert event_frame["type"] == "event"
        assert event_frame["channel"] == "alerts"
        assert event_frame["sequence"] >= 1
        assert "event_id" in event_frame
        assert event_frame["data"]["alert_title"] == "Field Deviation Warning"


def test_dedicated_channel_websocket(client: TestClient):
    """Verify pre-subscribed dedicated channel connection."""
    with client.websocket_connect("/api/v1/ws/telemetry?token=valid_token&building_id=B-100") as ws:
        ack = json.loads(ws.receive_text())
        assert ack["type"] == "connected"
        assert ack["channel"] == "telemetry"
        assert ack["building_id"] == "B-100"

        # Heartbeat ping
        ws.send_text(json.dumps({"type": "ping"}))
        pong = json.loads(ws.receive_text())
        assert pong["type"] == "pong"
        assert pong["channel"] == "telemetry"
