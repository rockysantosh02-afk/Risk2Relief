"""Celery Background Task: Maintenance Scheduling & Zone Transition."""

import logging
import uuid
from typing import Optional
from app.core.celery_app import celery_app
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.maintenance")


def _execute_maintenance_scheduling(
    building_id: str, zone_id: Optional[str] = None, duration_hours: float = 4.0, reason: str = "Scheduled Inspection"
) -> dict:
    logger.info(f"Scheduling maintenance for building {building_id}, zone {zone_id}, duration {duration_hours}h")
    return {
        "schedule_id": f"SCHED-{uuid.uuid4().hex[:8].upper()}",
        "building_id": building_id,
        "zone_id": zone_id,
        "duration_hours": duration_hours,
        "reason": reason,
        "status": "SCHEDULED",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.schedule_maintenance",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def schedule_maintenance_window_task(
        self, building_id: str, zone_id: Optional[str] = None, duration_hours: float = 4.0, reason: str = "Scheduled Inspection"
    ) -> dict:
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "schedule_maintenance", "STARTED", retries=self.request.retries)

        idem_key = generate_idempotency_key(
            "schedule_maintenance", building_id=building_id, zone_id=zone_id, duration=duration_hours
        )
        if not check_and_set_idempotency(idem_key, ttl_seconds=60.0):
            msg = "Duplicate maintenance schedule rejected within active execution window"
            record_task_status(task_id, "schedule_maintenance", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        try:
            result = _execute_maintenance_scheduling(building_id, zone_id, duration_hours, reason)
            record_task_status(task_id, "schedule_maintenance", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "schedule_maintenance", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def schedule_maintenance_window_task(
        building_id: str, zone_id: Optional[str] = None, duration_hours: float = 4.0, reason: str = "Scheduled Inspection"
    ) -> dict:
        return _execute_maintenance_scheduling(building_id, zone_id, duration_hours, reason)
