"""Celery Task Base Infrastructure: Idempotency, Status Tracking, and Retries."""

from __future__ import annotations
import functools
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger("risk2relief.tasks")

# In-memory idempotency cache for duplicate prevention and status tracking
_TASK_STATUS_REGISTRY: Dict[str, Dict[str, Any]] = {}
_IDEMPOTENCY_LOCKS: Dict[str, float] = {}  # key -> timestamp


def generate_idempotency_key(task_name: str, **kwargs) -> str:
    """Generate deterministic signature hash for task parameters."""
    normalized = json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.sha256(f"{task_name}:{normalized}".encode()).hexdigest()


def check_and_set_idempotency(key: str, ttl_seconds: float = 300.0) -> bool:
    """Returns True if the task execution is unique and acquired the lock, False if duplicate."""
    now = time.time()
    # Clean expired locks
    expired = [k for k, ts in _IDEMPOTENCY_LOCKS.items() if now - ts > ttl_seconds]
    for k in expired:
        _IDEMPOTENCY_LOCKS.pop(k, None)

    if key in _IDEMPOTENCY_LOCKS:
        return False  # Duplicate detected within TTL window

    _IDEMPOTENCY_LOCKS[key] = now
    return True


def record_task_status(
    task_id: str,
    task_name: str,
    status: str,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    retries: int = 0,
) -> Dict[str, Any]:
    """Update centralized in-memory task status."""
    entry = {
        "task_id": task_id,
        "task_name": task_name,
        "status": status,
        "result": result,
        "error": error,
        "retries": retries,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _TASK_STATUS_REGISTRY[task_id] = entry
    return entry


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve execution state of a background task."""
    return _TASK_STATUS_REGISTRY.get(task_id)
