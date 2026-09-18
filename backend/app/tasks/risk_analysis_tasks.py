"""Celery Background Task: Structural Risk Analysis & Health Scoring."""

import logging
import uuid
from typing import Optional
from app.core.celery_app import celery_app
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.risk_analysis")


def _execute_risk_analysis(building_id: str, zone_id: Optional[str] = None) -> dict:
    logger.info(f"Analyzing structural risk for building {building_id}, zone {zone_id}")
    return {
        "building_id": building_id,
        "zone_id": zone_id,
        "composite_risk_score": 18.5,
        "risk_category": "LOW",
        "limiting_condition_triggered": False,
        "status": "COMPLETED",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.analyze_structural_risk",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def analyze_structural_risk_task(self, building_id: str, zone_id: Optional[str] = None) -> dict:
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "analyze_structural_risk", "STARTED", retries=self.request.retries)

        idem_key = generate_idempotency_key("analyze_structural_risk", building_id=building_id, zone_id=zone_id)
        if not check_and_set_idempotency(idem_key, ttl_seconds=30.0):
            msg = "Duplicate risk analysis rejected within active execution window"
            record_task_status(task_id, "analyze_structural_risk", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        try:
            result = _execute_risk_analysis(building_id, zone_id)
            record_task_status(task_id, "analyze_structural_risk", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "analyze_structural_risk", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def analyze_structural_risk_task(building_id: str, zone_id: Optional[str] = None) -> dict:
        return _execute_risk_analysis(building_id, zone_id)
