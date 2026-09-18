"""Celery Background Task: Advisory Telemetry Anomaly Detection."""

import logging
import uuid
from typing import List
from app.core.celery_app import celery_app
from app.safety.anomaly import StatisticalZScoreDetector
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
)

logger = logging.getLogger("risk2relief.tasks.anomaly")


def _execute_anomaly_detection(source_id: str, values: List[float]) -> dict:
    logger.info(f"Running advisory anomaly detection for source {source_id} over {len(values)} samples")
    detector = StatisticalZScoreDetector(window_size=30, z_threshold=3.0)
    anomalies = []
    for idx, v in enumerate(values):
        res = detector.detect(v)
        if res.is_anomaly:
            anomalies.append({
                "sample_index": idx,
                "value": v,
                "score": res.anomaly_score,
                "z_score": res.features.get("z_score"),
            })

    return {
        "source_id": source_id,
        "total_samples": len(values),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "advisory_disclaimer": "ADVISORY ONLY. Model inference provides observational intelligence.",
        "status": "COMPLETED",
    }


if celery_app:
    @celery_app.task(
        bind=True,
        name="tasks.detect_anomalies",
        max_retries=3,
        default_retry_delay=2,
        time_limit=300,
        soft_time_limit=240,
    )
    def detect_anomalies_task(self, source_id: str, values: List[float]) -> dict:
        task_id = self.request.id or str(uuid.uuid4())
        record_task_status(task_id, "detect_anomalies", "STARTED", retries=self.request.retries)

        idem_key = generate_idempotency_key("detect_anomalies", source_id=source_id, sample_count=len(values))
        if not check_and_set_idempotency(idem_key, ttl_seconds=30.0):
            msg = "Duplicate anomaly detection rejected within active execution window"
            record_task_status(task_id, "detect_anomalies", "SKIPPED", result={"reason": msg})
            return {"status": "SKIPPED", "reason": msg}

        try:
            result = _execute_anomaly_detection(source_id, values)
            record_task_status(task_id, "detect_anomalies", "SUCCESS", result=result)
            return result
        except Exception as exc:
            countdown = 2 ** self.request.retries
            record_task_status(task_id, "detect_anomalies", "RETRY", error=str(exc), retries=self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)

else:
    def detect_anomalies_task(source_id: str, values: List[float]) -> dict:
        return _execute_anomaly_detection(source_id, values)
