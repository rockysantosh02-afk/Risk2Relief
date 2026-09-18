"""FastAPI WebSocket endpoints for real-time digital-twin streams."""

import json
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websockets.manager import connection_manager, VALID_CHANNELS

logger = logging.getLogger("risk2relief.websockets.router")

ws_router = APIRouter(tags=["WebSockets"])


@ws_router.websocket("/api/v1/ws")
async def multiplexed_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None),
    client_id: str = Query(default=None),
):
    """Multiplexed real-time WebSocket connection endpoint.

    Supports dynamic channel subscription, authentication, ping-pong heartbeat,
    and bi-directional messaging.
    """
    cid = client_id or f"client-{uuid.uuid4().hex[:8]}"
    client = await connection_manager.connect(websocket, client_id=cid, token=token)

    try:
        # Send initial connection acknowledgment
        ack = {
            "type": "connected",
            "client_id": cid,
            "authenticated": client.authenticated,
            "available_channels": sorted(list(VALID_CHANNELS)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_text(json.dumps(ack))

        while True:
            text = await websocket.receive_text()
            try:
                frame = json.loads(text)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON frame"}))
                continue

            frame_type = frame.get("type") or frame.get("action")

            # 1. Heartbeat ping
            if frame_type == "ping":
                pong = {
                    "type": "pong",
                    "client_id": cid,
                    "echo": frame.get("echo"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send_text(json.dumps(pong))

            # 2. Authentication frame
            elif frame_type == "auth":
                provided_token = frame.get("token")
                is_auth = connection_manager.authenticate_client(cid, provided_token)
                await websocket.send_text(
                    json.dumps({
                        "type": "auth_result",
                        "authenticated": is_auth,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

            # 3. Channel subscription
            elif frame_type == "subscribe":
                channel = frame.get("channel")
                building_id = frame.get("building_id")
                ok = connection_manager.subscribe(cid, channel, building_id=building_id)
                await websocket.send_text(
                    json.dumps({
                        "type": "subscription_ack",
                        "channel": channel,
                        "building_id": building_id,
                        "status": "subscribed" if ok else "rejected",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

            # 4. Unsubscribe
            elif frame_type == "unsubscribe":
                channel = frame.get("channel")
                ok = connection_manager.unsubscribe(cid, channel)
                await websocket.send_text(
                    json.dumps({
                        "type": "unsubscribe_ack",
                        "channel": channel,
                        "status": "unsubscribed" if ok else "failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

            else:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": f"Unknown action: '{frame_type}'",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

    except WebSocketDisconnect:
        await connection_manager.disconnect(cid)
    except Exception as exc:
        logger.warning(f"WebSocket session error for {cid}: {exc}")
        await connection_manager.disconnect(cid)


@ws_router.websocket("/api/v1/ws/{channel}")
async def dedicated_channel_websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(default=None),
    building_id: str = Query(default=None),
    client_id: str = Query(default=None),
):
    """Direct connection endpoint pre-subscribed to a dedicated channel."""
    if channel not in VALID_CHANNELS:
        await websocket.close(code=4000, reason=f"Unknown channel: {channel}")
        return

    cid = client_id or f"direct-{uuid.uuid4().hex[:8]}"
    client = await connection_manager.connect(websocket, client_id=cid, token=token)
    connection_manager.subscribe(cid, channel, building_id=building_id)

    try:
        ack = {
            "type": "connected",
            "channel": channel,
            "building_id": building_id,
            "client_id": cid,
            "authenticated": client.authenticated,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_text(json.dumps(ack))

        while True:
            text = await websocket.receive_text()
            try:
                frame = json.loads(text)
            except Exception:
                continue

            if frame.get("type") == "ping" or frame.get("action") == "ping":
                await websocket.send_text(
                    json.dumps({
                        "type": "pong",
                        "channel": channel,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

    except WebSocketDisconnect:
        await connection_manager.disconnect(cid)
    except Exception as exc:
        logger.warning(f"Dedicated WebSocket error: {exc}")
        await connection_manager.disconnect(cid)
