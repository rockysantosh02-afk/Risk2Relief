"""Celery background tasks for Risk2Relief digital-twin platform."""

from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    record_task_status,
    get_task_status,
)
from app.tasks.telemetry_tasks import aggregate_telemetry_task
from app.tasks.simulation_tasks import run_simulation_task
from app.tasks.risk_analysis_tasks import analyze_structural_risk_task
from app.tasks.anomaly_detection_tasks import detect_anomalies_task
from app.tasks.report_tasks import generate_facility_report_task
from app.tasks.maintenance_tasks import schedule_maintenance_window_task

__all__ = [
    "generate_idempotency_key",
    "check_and_set_idempotency",
    "record_task_status",
    "get_task_status",
    "aggregate_telemetry_task",
    "run_simulation_task",
    "analyze_structural_risk_task",
    "detect_anomalies_task",
    "generate_facility_report_task",
    "schedule_maintenance_window_task",
]
