"""Unit tests for Celery Background Tasks, Idempotency, and Failure Recovery."""

import uuid
from app.tasks.base import (
    generate_idempotency_key,
    check_and_set_idempotency,
    get_task_status,
)
from app.tasks.telemetry_tasks import aggregate_telemetry_task
from app.tasks.simulation_tasks import run_simulation_task
from app.tasks.risk_analysis_tasks import analyze_structural_risk_task
from app.tasks.anomaly_detection_tasks import detect_anomalies_task
from app.tasks.report_tasks import generate_facility_report_task
from app.tasks.maintenance_tasks import schedule_maintenance_window_task


def _run_task_eager(task_obj, *args, **kwargs):
    """Helper to invoke a Celery task either via .apply() or direct function call."""
    if hasattr(task_obj, "apply"):
        res = task_obj.apply(args=args, kwargs=kwargs)
        return res.result
    return task_obj(*args, **kwargs)


def test_telemetry_aggregation_task_and_idempotency():
    """Verify telemetry aggregation task execution and duplicate prevention."""
    bld_id = str(uuid.uuid4())
    metric = "strain"

    # First execution
    res1 = _run_task_eager(aggregate_telemetry_task, bld_id, metric, bucket_seconds=60)
    assert res1["status"] == "COMPLETED"
    assert res1["metric"] == "strain"
    assert res1["processed_samples"] > 0

    # Second immediate execution with identical parameters should trigger duplicate prevention
    res2 = _run_task_eager(aggregate_telemetry_task, bld_id, metric, bucket_seconds=60)
    assert res2["status"] == "SKIPPED"
    assert "Duplicate" in res2["reason"]


def test_simulation_execution_task():
    """Verify in-silico simulation background task execution."""
    bld_id = str(uuid.uuid4())
    res = _run_task_eager(run_simulation_task, bld_id, "NORMAL", step_count=5, step_duration_seconds=1.0)
    assert res["status"] == "COMPLETED"
    assert res["step_count"] == 5
    assert "In-silico digital twin" in res["simulation_disclaimer"]


def test_risk_analysis_task():
    """Verify structural risk evaluation background job."""
    bld_id = str(uuid.uuid4())
    res = _run_task_eager(analyze_structural_risk_task, bld_id, zone_id="CORE")
    assert res["status"] == "COMPLETED"
    assert res["risk_category"] == "LOW"
    assert "composite_risk_score" in res


def test_anomaly_detection_task():
    """Verify advisory anomaly detection background processing."""
    src_id = str(uuid.uuid4())
    # Baseline data with an outlier spike
    values = [10.0, 10.1, 9.9, 10.0, 10.2, 35.0, 10.0]
    res = _run_task_eager(detect_anomalies_task, src_id, values)
    assert res["status"] == "COMPLETED"
    assert res["total_samples"] == 7
    assert res["anomaly_count"] >= 1
    assert "ADVISORY ONLY" in res["advisory_disclaimer"]


def test_report_generation_task():
    """Verify report compilation background job."""
    bld_id = str(uuid.uuid4())
    res = _run_task_eager(generate_facility_report_task, bld_id, "FACILITY_COMPREHENSIVE")
    assert res["status"] == "GENERATED"
    assert res["report_id"].startswith("REP-")


def test_maintenance_scheduling_task():
    """Verify maintenance scheduling background task."""
    bld_id = str(uuid.uuid4())
    res = _run_task_eager(
        schedule_maintenance_window_task, bld_id, zone_id="WING-B", duration_hours=6.0, reason="Calibrate Sensors"
    )
    assert res["status"] == "SCHEDULED"
    assert res["schedule_id"].startswith("SCHED-")


def test_idempotency_key_generation():
    """Verify deterministic hash generation for idempotency locks."""
    k1 = generate_idempotency_key("task_a", param1=10, param2="xyz")
    k2 = generate_idempotency_key("task_a", param2="xyz", param1=10)
    k3 = generate_idempotency_key("task_a", param1=11, param2="xyz")

    assert k1 == k2  # Independent of dictionary order
    assert k1 != k3
