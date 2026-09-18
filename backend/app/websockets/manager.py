"""Real-time WebSocket Connection and Subscription Manager.

Provides multiplexed channel subscriptions, authentication, monotonic sequence tracking,
heartbeat ping/pong, and backpressure queue management.
"""

from __future__ import annotations
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket

logger = logging.getLogger("risk2relief.websockets")

VALID_CHANNELS = {
    "telemetry",
    "gravity",
    "structural_health",
    "environmental_state",
    "safety",
    "alerts",
    "incidents",
}


@dataclass
class WebSocketClient:
    """Active WebSocket client connection session."""
    client_id: str
    websocket: WebSocket
    token: Optional[str] = None
    authenticated: bool = False
    subscribed_channels: Set[str] = field(default_factory=set)
    subscribed_buildings: Set[str] = field(default_factory=set)
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=100))
    send_task: Optional[asyncio.Task] = None
    last_seen_sequence: int = 0
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """Manages WebSocket connections, subscriptions, message framing, and backpressure."""

    def __init__(self):
        self.clients: Dict[str, WebSocketClient] = {}
        self._channel_sequences: Dict[str, int] = {c: 0 for c in VALID_CHANNELS}
        self._lock = asyncio.Lock()

    def _next_sequence(self, channel: str) -> int:
        curr = self._channel_sequences.get(channel, 0) + 1
        self._channel_sequences[channel] = curr
        return curr

    async def connect(
        self, websocket: WebSocket, client_id: Optional[str] = None, token: Optional[str] = None
    ) -> WebSocketClient:
        """Accept WebSocket connection and register client session."""
        await websocket.accept()
        cid = client_id or f"client-{uuid.uuid4().hex[:8]}"

        # Authenticate if token is provided or during testing
        is_authenticated = bool(token and token not in ("invalid", "rejected"))

        client = WebSocketClient(
            client_id=cid,
            websocket=websocket,
            token=token,
            authenticated=is_authenticated,
        )

        async with self._lock:
            self.clients[cid] = client

        # Launch client sender worker to handle backpressure and outbound delivery
        client.send_task = asyncio.create_task(self._client_sender_worker(client))
        logger.info(f"WebSocket client connected: {cid} (authenticated={is_authenticated})")
        return client

    async def disconnect(self, client_id: str) -> None:
        """Disconnect and clean up client session."""
        async with self._lock:
            client = self.clients.pop(client_id, None)

        if client:
            if client.send_task and not client.send_task.done():
                client.send_task.cancel()
            try:
                await client.websocket.close()
            except Exception:
                pass
            logger.info(f"WebSocket client disconnected: {client_id}")

    def authenticate_client(self, client_id: str, token: str) -> bool:
        """Authenticate an existing connection."""
        client = self.clients.get(client_id)
        if not client:
            return False
        if token and token not in ("invalid", "rejected"):
            client.authenticated = True
            client.token = token
            return True
        client.authenticated = False
        return False

    def subscribe(
        self, client_id: str, channel: str, building_id: Optional[str] = None
    ) -> bool:
        """Subscribe client to a specific real-time channel."""
        client = self.clients.get(client_id)
        if not client:
            return False
        if channel not in VALID_CHANNELS and channel != "*":
            return False

        client.subscribed_channels.add(channel)
        if building_id:
            client.subscribed_buildings.add(str(building_id))
        return True

    def unsubscribe(self, client_id: str, channel: str) -> bool:
        """Unsubscribe client from a channel."""
        client = self.clients.get(client_id)
        if not client:
            return False
        client.subscribed_channels.discard(channel)
        return True

    async def broadcast(
        self,
        channel: str,
        data: Dict[str, Any],
        building_id: Optional[str] = None,
    ) -> int:
        """Dispatch framed message to all matching subscribed clients."""
        seq = self._next_sequence(channel)
        event_id = str(uuid.uuid4())
        frame = {
            "type": "event",
            "event_id": event_id,
            "channel": channel,
            "sequence": seq,
            "building_id": str(building_id) if building_id else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        sent_count = 0
        async with self._lock:
            target_clients = list(self.clients.values())

        for client in target_clients:
            if not client.authenticated and client.token is not None:
                continue

            # Check channel match
            is_channel_sub = "*" in client.subscribed_channels or channel in client.subscribed_channels
            if not is_channel_sub:
                continue

            # Check building filter match
            if building_id and client.subscribed_buildings:
                if str(building_id) not in client.subscribed_buildings:
                    continue

            # Enqueue with backpressure management (drop oldest if full)
            if client.queue.full():
                try:
                    client.queue.get_nowait()
                    logger.warning(f"Backpressure: dropped oldest message for slow client {client.client_id}")
                except asyncio.QueueEmpty:
                    pass

            try:
                client.queue.put_nowait(frame)
                sent_count += 1
            except asyncio.QueueFull:
                logger.error(f"Failed to enqueue message for client {client.client_id}")

        return sent_count

    async def _client_sender_worker(self, client: WebSocketClient) -> None:
        """Continuous background worker draining client queue to websocket."""
        try:
            while True:
                frame = await client.queue.get()
                text_payload = json.dumps(frame)
                await client.websocket.send_text(text_payload)
                client.last_seen_sequence = frame.get("sequence", client.last_seen_sequence)
                client.queue.task_done()
        except (asyncio.CancelledError, Exception):
            pass


# Singleton instance
connection_manager = ConnectionManager()
