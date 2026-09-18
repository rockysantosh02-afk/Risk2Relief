"""Redis client initialization and connection health checking."""

import logging
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger("risk2relief.redis")

settings = get_settings()

_redis_client = None


def get_redis_client():
    """Retrieve or initialize async Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.get_redis_url(),
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
        except ImportError:
            logger.warning("redis library not installed; redis operations will be disabled")
            return None
    return _redis_client


async def check_redis_health() -> str:
    """Safely check Redis connectivity."""
    client = get_redis_client()
    if client is None:
        return "not_installed"
    try:
        pong = await client.ping()
        return "connected" if pong else "disconnected"
    except Exception as exc:
        logger.warning(f"Redis health check failed: {str(exc)}")
        return "disconnected"


async def close_redis_connection():
    """Safely close active Redis client connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception as exc:
            logger.warning(f"Error closing redis connection: {exc}")
        finally:
            _redis_client = None
