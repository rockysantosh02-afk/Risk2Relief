"""Redis Pub/Sub Bridge for WebSocket Event Broadcasting.

Enables horizontal scalability across multiple API workers by bridging Redis Pub/Sub
to local ConnectionManager instances, with transparent in-memory fallback.
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from app.core.redis import get_redis_client
from app.websockets.manager import connection_manager

logger = logging.getLogger("risk2relief.websockets.redis")

REDIS_CHANNEL = "risk2relief:events"


class RedisPubSubBridge:
    """Bridges Redis Pub/Sub messages to the local WebSocket ConnectionManager."""

    def __init__(self):
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start listening to Redis pub/sub events in the background."""
        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Redis Pub/Sub bridge started")

    async def stop(self) -> None:
        """Stop listening to Redis pub/sub."""
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
        logger.info("Redis Pub/Sub bridge stopped")

    async def publish_event(
        self,
        channel: str,
        data: Dict[str, Any],
        building_id: Optional[str] = None,
    ) -> None:
        """Publish event to Redis or directly to local connection manager if Redis unavailable."""
        client = get_redis_client()
        payload = {
            "channel": channel,
            "data": data,
            "building_id": str(building_id) if building_id else None,
        }

        if client is not None:
            try:
                await client.publish(REDIS_CHANNEL, json.dumps(payload))
                return
            except Exception as exc:
                logger.warning(f"Redis publish failed ({exc}); falling back to local broadcast")

        # In-memory broadcast fallback
        await connection_manager.broadcast(channel, data, building_id=building_id)

    async def _listen_loop(self) -> None:
        """Background loop reading published events from Redis."""
        while self._running:
            client = get_redis_client()
            if client is None:
                await asyncio.sleep(5.0)
                continue

            pubsub = client.pubsub()
            try:
                await pubsub.subscribe(REDIS_CHANNEL)
                logger.info(f"Subscribed to Redis channel '{REDIS_CHANNEL}'")
                while self._running:
                    msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if msg and msg.get("type") == "message":
                        try:
                            content = json.loads(msg["data"])
                            ch = content.get("channel")
                            dt = content.get("data", {})
                            bid = content.get("building_id")
                            if ch:
                                await connection_manager.broadcast(ch, dt, building_id=bid)
                        except Exception as parse_err:
                            logger.error(f"Error handling Redis event: {parse_err}")
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.warning(f"Redis pub/sub listener exception: {err}; retrying in 3s")
                await asyncio.sleep(3.0)
            finally:
                try:
                    await pubsub.unsubscribe(REDIS_CHANNEL)
                    await pubsub.close()
                except Exception:
                    pass


# Singleton instance
redis_bridge = RedisPubSubBridge()
