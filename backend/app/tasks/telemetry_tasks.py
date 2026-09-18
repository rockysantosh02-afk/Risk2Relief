"""Celery Background Task: Multi-Resolution Telemetry Aggregation."""

import logging
import uuid
from app.core.celery_app import celery_app
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.telemetry")


def _execute_aggregate_telemetry(building_id: str, metric: str, bucket_seconds: int = 60) -> dict:
    """Core logic for aggregation task."""
    logger.info(f"Aggregating telemetry for building {building_id}, metric {metric}, bucket {bucket_seconds}s")
    # Simulate processing and aggregation summary
    return {
        "building_id": building_id,
        "metric": metric,
        "bucket_seconds": bucket_seconds,
        "processed_samples": 120,
        "mean": 24.5,
        "min": 18.2,
        "max": 31.0,
        "status": "COMPLETED",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.aggregate_telemetry",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def aggregate_telemetry_task(self, building_id: str, metric: str, bucket_seconds: int = 60) -> dict:
        """Celery task calculating multi-resolution telemetry aggregations."""
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "aggregate_telemetry", "STARTED", retries=self.request.retries)

        # 1. Idempotency duplicate check
        idem_key = generate_idempotency_key("aggregate_telemetry", building_id=building_id, metric=metric, bucket_seconds=bucket_seconds)
        if not check_and_set_idempotency(idem_key, ttl_seconds=60.0):
            msg = "Duplicate aggregation task execution prevented within TTL window"
            record_task_status(task_id, "aggregate_telemetry", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        # 2. Execution with exponential backoff retry
        try:
            result = _execute_aggregate_telemetry(building_id, metric, bucket_seconds)
            record_task_status(task_id, "aggregate_telemetry", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "aggregate_telemetry", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def aggregate_telemetry_task(building_id: str, metric: str, bucket_seconds: int = 60) -> dict:
        return _execute_aggregate_telemetry(building_id, metric, bucket_seconds)
