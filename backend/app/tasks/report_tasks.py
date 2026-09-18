"""Celery Background Task: Facility Report Generation."""

import logging
import uuid
from app.core.celery_app import celery_app
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.report")


def _execute_report_generation(building_id: str, report_type: str = "FACILITY_COMPREHENSIVE") -> dict:
    logger.info(f"Compiling facility report for building {building_id}, type {report_type}")
    rep_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    return {
        "report_id": rep_id,
        "building_id": building_id,
        "report_type": report_type,
        "status": "GENERATED",
        "sections_count": 3,
        "summary": f"Facility report compiled for {building_id}.",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.generate_facility_report",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def generate_facility_report_task(self, building_id: str, report_type: str = "FACILITY_COMPREHENSIVE") -> dict:
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "generate_facility_report", "STARTED", retries=self.request.retries)

        idem_key = generate_idempotency_key("generate_facility_report", building_id=building_id, report_type=report_type)
        if not check_and_set_idempotency(idem_key, ttl_seconds=60.0):
            msg = "Duplicate report generation rejected within active execution window"
            record_task_status(task_id, "generate_facility_report", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        try:
            result = _execute_report_generation(building_id, report_type)
            record_task_status(task_id, "generate_facility_report", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "generate_facility_report", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def generate_facility_report_task(building_id: str, report_type: str = "FACILITY_COMPREHENSIVE") -> dict:
        return _execute_report_generation(building_id, report_type)
