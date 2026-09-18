"""Unit tests for Source Health and Explainable Reliability Intelligence Engine."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from app.telemetry.source_health import SourceHealthEngine, SourceHealthMetrics


@dataclass
class MockReading:
    timestamp: datetime
    quality: str = "VALID"


def test_source_health_healthy_source():
    """Verify an online source with valid, fresh data receives high reliability."""
    source_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    
    # 10 readings in the last 10 seconds at 1 Hz
    readings = [
        MockReading(timestamp=now - timedelta(seconds=i), quality="VALID")
        for i in range(10)
    ]

    metrics = SourceHealthEngine.calculate_health(
        source_id=source_id,
        source_identifier="SENS-HEALTHY-01",
        status="ONLINE",
        sampling_rate_hz=1.0,
        readings=readings,
        now=now,
        evaluation_window_seconds=10.0,
    )

    assert metrics.source_id == source_id
    assert metrics.source_identifier == "SENS-HEALTHY-01"
    assert metrics.status == "ONLINE"
    assert metrics.error_rate == 0.0
    assert metrics.duplicate_rate == 0.0
    assert metrics.anomaly_rate == 0.0
    assert metrics.availability == 1.0
    assert metrics.freshness_seconds == 0.0
    assert metrics.reliability_score >= 0.95
    assert metrics.is_healthy is True
    assert "safety_disclaimer" in metrics.explanation


def test_source_health_high_error_rate():
    """Verify high error rate significantly degrades reliability score."""
    source_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 8 errors out of 10 readings
    readings = [
        MockReading(timestamp=now - timedelta(seconds=i), quality="INVALID" if i < 8 else "VALID")
        for i in range(10)
    ]

    metrics = SourceHealthEngine.calculate_health(
        source_id=source_id,
        source_identifier="SENS-ERROR-01",
        status="ONLINE",
        sampling_rate_hz=1.0,
        readings=readings,
        now=now,
        evaluation_window_seconds=10.0,
    )

    assert metrics.error_rate == 0.8
    assert metrics.valid_readings == 2
    assert metrics.error_readings == 8
    assert metrics.reliability_score < 0.60
    assert metrics.is_healthy is False


def test_source_health_status_penalties():
    """Verify OFFLINE and FAULT statuses apply severe multipliers."""
    source_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    readings = [MockReading(timestamp=now, quality="VALID")]

    # OFFLINE status (0.4 multiplier)
    offline_metrics = SourceHealthEngine.calculate_health(
        source_id=source_id,
        source_identifier="SENS-OFFLINE",
        status="OFFLINE",
        sampling_rate_hz=1.0,
        readings=readings,
        now=now,
        evaluation_window_seconds=1.0,
    )
    assert offline_metrics.explanation["status_multiplier"] == 0.4
    assert offline_metrics.reliability_score <= 0.40
    assert offline_metrics.is_healthy is False

    # FAULT status (0.1 multiplier)
    fault_metrics = SourceHealthEngine.calculate_health(
        source_id=source_id,
        source_identifier="SENS-FAULT",
        status="FAULT",
        sampling_rate_hz=1.0,
        readings=readings,
        now=now,
        evaluation_window_seconds=1.0,
    )
    assert fault_metrics.explanation["status_multiplier"] == 0.1
    assert fault_metrics.reliability_score <= 0.10
    assert fault_metrics.is_healthy is False


def test_source_health_stale_data_decay():
    """Verify stale readings without recent transmissions decay freshness factor."""
    source_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    # Last seen 2 hours ago (7200s > 3600s decay window)
    stale_time = now - timedelta(hours=2)
    readings = [MockReading(timestamp=stale_time, quality="VALID")]

    metrics = SourceHealthEngine.calculate_health(
        source_id=source_id,
        source_identifier="SENS-STALE",
        status="ONLINE",
        sampling_rate_hz=1.0,
        readings=readings,
        now=now,
        evaluation_window_seconds=3600.0,
    )

    assert metrics.freshness_seconds == 7200.0
    assert metrics.explanation["freshness_component"] == 0.0
