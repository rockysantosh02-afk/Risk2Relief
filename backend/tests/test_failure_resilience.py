"""Failure resilience, edge-case, fault tolerance, and multi-node recovery tests."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.building import Building
from app.schemas.telemetry import (
    SourceTypeEnum,
    TelemetrySourceCreate,
    TelemetryReadingCreate,
    QualityEnum,
)
from app.services.telemetry_service import TelemetryService
from app.telemetry.validation import TelemetryValidationEngine
from app.safety.state_machine import SafetyStateMachine, SafetyState, SafetyInputs
from app.safety.failure_injection import FailureInjectionEngine, FailureMode
from app.services.safety_service import SafetyService
from app.websockets.redis_bridge import RedisPubSubBridge
from app.tasks.telemetry_tasks import aggregate_telemetry_task


def _run_task_eager(task_obj, *args, **kwargs):
    if hasattr(task_obj, "apply"):
        res = task_obj.apply(args=args, kwargs=kwargs)
        return res.result
    return task_obj(*args, **kwargs)


# ============================================================================
# 1. Telemetry Quality Rejection & Anomaly Classification
# ============================================================================

def test_telemetry_corrupted_and_stale_data_rejection():
    """Verify corrupted values, out-of-range metrics, and stale timestamps are flagged accurately."""
    now = datetime.now(timezone.utc)

    # 1. Future timestamp (clock skew > 60s)
    future_time = now + timedelta(minutes=10)
    future_res = TelemetryValidationEngine.validate_reading(
        metric="vibration_hz",
        value=15.0,
        unit="Hz",
        timestamp=future_time,
        event_id="EVT-FUTURE-01",
        now=now,
    )
    assert future_res.is_valid is False
    assert future_res.quality == QualityEnum.INVALID
    assert future_res.error_code == "ERR_FUTURE_TIMESTAMP"

    # 2. Stale timestamp (> 2 hours old)
    stale_time = now - timedelta(hours=3)
    stale_res = TelemetryValidationEngine.validate_reading(
        metric="vibration_hz",
        value=15.0,
        unit="Hz",
        timestamp=stale_time,
        event_id="EVT-STALE-01",
        now=now,
    )
    assert stale_res.is_valid is False
    assert stale_res.quality == QualityEnum.STALE
    assert stale_res.error_code == "ERR_STALE_TIMESTAMP"

    # 3. Physically implausible vibration (> 1000 Hz)
    implausible_res = TelemetryValidationEngine.validate_reading(
        metric="vibration_hz",
        value=5000.0,
        unit="Hz",
        timestamp=now,
        event_id="EVT-IMPLAUSIBLE-01",
        now=now,
    )
    assert implausible_res.is_valid is False
    assert implausible_res.quality == QualityEnum.ANOMALOUS
    assert implausible_res.error_code == "ERR_PHYSICAL_RANGE_EXCEEDED"

    # 4. Unknown metric
    unknown_metric_res = TelemetryValidationEngine.validate_reading(
        metric="unknown_plasma_flux",
        value=100.0,
        unit="raw",
        timestamp=now,
        event_id="EVT-UNKNOWN-01",
        now=now,
    )
    assert unknown_metric_res.is_valid is False
    assert unknown_metric_res.quality == QualityEnum.INVALID
    assert unknown_metric_res.error_code == "ERR_UNKNOWN_METRIC"


# ============================================================================
# 2. Redis Disconnection & In-Memory Fallback
# ============================================================================

@pytest.mark.asyncio
async def test_redis_bridge_graceful_in_memory_fallback():
    """Verify RedisPubSubBridge falls back gracefully to in-memory local subscribers when disconnected."""
    bridge = RedisPubSubBridge()

    # Publish message without active Redis daemon - must fallback to in-memory broadcast cleanly
    payload = {"event": "TEST_BROADCAST", "timestamp": datetime.now(timezone.utc).isoformat()}
    await bridge.publish_event(
        channel="telemetry",
        data=payload,
        building_id=str(uuid.uuid4()),
    )


# ============================================================================
# 3. Celery Task Idempotency
# ============================================================================

def test_celery_task_idempotency_safe_execution():
    """Verify repeating Celery task executions with identical parameters does not crash or corrupt state."""
    building_id = str(uuid.uuid4())

    # First execution succeeds
    res1 = _run_task_eager(aggregate_telemetry_task, building_id, "vibration_hz", bucket_seconds=60)
    assert res1["status"] == "COMPLETED"
    assert res1["metric"] == "vibration_hz"

    # Second execution is skipped as duplicate within TTL window
    res2 = _run_task_eager(aggregate_telemetry_task, building_id, "vibration_hz", bucket_seconds=60)
    assert res2["status"] == "SKIPPED"
    assert "Duplicate" in res2["reason"]


# ============================================================================
# 4. Multi-Node Failure -> Emergency State Machine Transition & Safe Recovery
# ============================================================================

@pytest.mark.asyncio
async def test_multi_node_emergency_transition_and_recovery_cycle(db_session):
    """Verify cascading multi-node failure transitions through NORMAL -> WARNING -> DEGRADED -> EMERGENCY -> RECOVERY -> NORMAL."""
    # 1. Start in NORMAL, apply moderate risk -> WARNING
    input_warning = SafetyInputs(
        gravity_stability="NORMAL",
        structural_risk="MODERATE",
        telemetry_reliability=0.95,
    )
    t_warning = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, input_warning)
    assert t_warning.to_state == SafetyState.WARNING

    # 2. Inject primary node drop -> DEGRADED
    input_degraded = SafetyInputs(
        gravity_stability="WARNING",
        structural_risk="HIGH",
        telemetry_reliability=0.85,
    )
    t_degraded = SafetyStateMachine.evaluate_target_state(SafetyState.WARNING, input_degraded)
    assert t_degraded.to_state == SafetyState.DEGRADED

    # 3. Inject catastrophic multi-node failure -> EMERGENCY
    input_emergency = SafetyInputs(
        gravity_stability="UNSTABLE",
        structural_risk="CRITICAL",
        telemetry_reliability=0.40,
    )
    t_emergency = SafetyStateMachine.evaluate_target_state(SafetyState.DEGRADED, input_emergency)
    assert t_emergency.to_state == SafetyState.EMERGENCY

    # In EMERGENCY, nominal inputs transition to RECOVERY first (Safety Invariant)
    input_nominal = SafetyInputs(
        gravity_stability="NORMAL",
        structural_risk="LOW",
        telemetry_reliability=1.0,
    )
    t_recovery = SafetyStateMachine.evaluate_target_state(SafetyState.EMERGENCY, input_nominal)
    assert t_recovery.to_state == SafetyState.RECOVERY

    # From RECOVERY, after stabilization, safely return to NORMAL
    t_recovered = SafetyStateMachine.evaluate_target_state(SafetyState.RECOVERY, input_nominal)
    assert t_recovered.to_state == SafetyState.NORMAL
