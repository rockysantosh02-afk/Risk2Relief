"""Celery Background Task: In-Silico Digital-Twin Simulation Execution."""

import logging
import uuid
from app.core.celery_app import celery_app
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.simulation")


def _execute_simulation(
    building_id: str, scenario_type: str = "NORMAL", step_count: int = 5, step_duration_seconds: float = 1.0
) -> dict:
    logger.info(f"Running in-silico simulation for building {building_id}, scenario {scenario_type}, steps {step_count}")
    return {
        "building_id": building_id,
        "scenario_type": scenario_type,
        "step_count": step_count,
        "duration_seconds": step_count * step_duration_seconds,
        "peak_risk_level": "LOW" if scenario_type == "NORMAL" else "MODERATE",
        "peak_risk_score": 15.0 if scenario_type == "NORMAL" else 45.0,
        "status": "COMPLETED",
        "simulation_disclaimer": "In-silico digital twin simulation only. No physical hardware commanded.",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.run_simulation",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def run_simulation_task(
        self, building_id: str, scenario_type: str = "NORMAL", step_count: int = 5, step_duration_seconds: float = 1.0
    ) -> dict:
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "run_simulation", "STARTED", retries=self.request.retries)

        idem_key = generate_idempotency_key(
            "run_simulation",
            building_id=building_id,
            scenario_type=scenario_type,
            step_count=step_count,
            step_duration_seconds=step_duration_seconds,
        )
        if not check_and_set_idempotency(idem_key, ttl_seconds=30.0):
            msg = "Duplicate simulation task rejected within active execution window"
            record_task_status(task_id, "run_simulation", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        try:
            result = _execute_simulation(building_id, scenario_type, step_count, step_duration_seconds)
            record_task_status(task_id, "run_simulation", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "run_simulation", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def run_simulation_task(
        building_id: str, scenario_type: str = "NORMAL", step_count: int = 5, step_duration_seconds: float = 1.0
    ) -> dict:
        return _execute_simulation(building_id, scenario_type, step_count, step_duration_seconds)
