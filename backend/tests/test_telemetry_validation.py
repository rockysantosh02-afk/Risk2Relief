"""Unit tests for Deterministic Telemetry Validation Engine."""

import pytest
from datetime import datetime, timezone, timedelta

from app.schemas.telemetry import QualityEnum
from app.telemetry.validation import (
    TelemetryValidationEngine,
    METRIC_SPECIFICATIONS,
    MAX_FUTURE_DRIFT_SECONDS,
    MAX_STALENESS_SECONDS,
)


def test_validation_engine_valid_reading():
    """Verify standard valid telemetry reading passes all validation checks."""
    now = datetime.now(timezone.utc)
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=24.5,
        unit="C",
        timestamp=now,
        event_id="EVT-001",
        source_is_known=True,
        source_is_active=True,
        is_duplicate=False,
        now=now,
    )
    assert res.is_valid is True
    assert res.quality == QualityEnum.VALID
    assert res.error_code is None
    assert res.reason is None
    assert res.anomaly_score == 0.0


def test_validation_engine_all_supported_metrics():
    """Verify all supported metrics validate successfully with valid units and ranges."""
    now = datetime.now(timezone.utc)
    test_cases = [
        ("strain_microstrain", 250.0, "um/m"),
        ("vibration_hz", 12.4, "Hz"),
        ("temperature_celsius", 21.0, "degC"),
        ("load_kn", 500.0, "kN"),
        ("inclination_deg", 0.02, "deg"),
        ("pressure_kpa", 101.3, "kPa"),
        ("air_quality_aqi", 42.0, "AQI"),
    ]
    for metric, value, unit in test_cases:
        res = TelemetryValidationEngine.validate_reading(
            metric=metric,
            value=value,
            unit=unit,
            timestamp=now,
            event_id=f"EVT-{metric}",
            now=now,
        )
        assert res.is_valid is True, f"Failed for metric {metric}: {res.reason}"
        assert res.quality == QualityEnum.VALID


def test_validation_engine_missing_fields():
    """Verify missing mandatory fields are deterministically rejected with ERR_MISSING_FIELD."""
    now = datetime.now(timezone.utc)
    
    # Missing metric
    res = TelemetryValidationEngine.validate_reading(
        metric=None,
        value=10.0,
        unit="C",
        timestamp=now,
        event_id="EVT-002",
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.MISSING
    assert res.error_code == "ERR_MISSING_FIELD"

    # Missing value
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=None,
        unit="C",
        timestamp=now,
        event_id="EVT-003",
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.MISSING
    assert res.error_code == "ERR_MISSING_FIELD"

    # Missing event_id
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=20.0,
        unit="C",
        timestamp=now,
        event_id="",
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.MISSING
    assert res.error_code == "ERR_MISSING_FIELD"


def test_validation_engine_unknown_metric():
    """Verify unrecognized metrics are rejected with ERR_UNKNOWN_METRIC."""
    now = datetime.now(timezone.utc)
    res = TelemetryValidationEngine.validate_reading(
        metric="warp_field_distortion",
        value=9.9,
        unit="warp",
        timestamp=now,
        event_id="EVT-004",
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.INVALID
    assert res.error_code == "ERR_UNKNOWN_METRIC"
    assert "Unrecognized metric" in res.reason


def test_validation_engine_invalid_unit():
    """Verify incompatible units for known metrics are rejected with ERR_INVALID_UNIT."""
    now = datetime.now(timezone.utc)
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=25.0,
        unit="liters",
        timestamp=now,
        event_id="EVT-005",
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.INVALID
    assert res.error_code == "ERR_INVALID_UNIT"
    assert "is invalid for metric" in res.reason


def test_validation_engine_future_timestamp():
    """Verify timestamps skewed into the future beyond threshold are rejected."""
    now = datetime.now(timezone.utc)
    future_time = now + timedelta(seconds=MAX_FUTURE_DRIFT_SECONDS + 30)
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=25.0,
        unit="C",
        timestamp=future_time,
        event_id="EVT-006",
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.INVALID
    assert res.error_code == "ERR_FUTURE_TIMESTAMP"
    assert "in the future" in res.reason


def test_validation_engine_stale_timestamp():
    """Verify readings older than max staleness limit are marked STALE."""
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(seconds=MAX_STALENESS_SECONDS + 100)
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=25.0,
        unit="C",
        timestamp=stale_time,
        event_id="EVT-007",
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.STALE
    assert res.error_code == "ERR_STALE_TIMESTAMP"
    assert "older than max staleness" in res.reason


def test_validation_engine_physical_range_exceeded():
    """Verify readings exceeding physical plausible boundaries are classified as ANOMALOUS."""
    now = datetime.now(timezone.utc)
    
    # Strain beyond 10,000 microstrain
    res = TelemetryValidationEngine.validate_reading(
        metric="strain_microstrain",
        value=50000.0,
        unit="um/m",
        timestamp=now,
        event_id="EVT-008",
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.ANOMALOUS
    assert res.error_code == "ERR_PHYSICAL_RANGE_EXCEEDED"

    # Temperature below -50C
    res_cold = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=-75.0,
        unit="C",
        timestamp=now,
        event_id="EVT-009",
        now=now,
    )
    assert res_cold.is_valid is False
    assert res_cold.quality == QualityEnum.ANOMALOUS
    assert res_cold.error_code == "ERR_PHYSICAL_RANGE_EXCEEDED"


def test_validation_engine_duplicate_event():
    """Verify duplicate event flags generate ERR_DUPLICATE_EVENT."""
    now = datetime.now(timezone.utc)
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=22.0,
        unit="C",
        timestamp=now,
        event_id="EVT-DUP-01",
        is_duplicate=True,
        now=now,
    )
    assert res.is_valid is False
    assert res.quality == QualityEnum.DUPLICATE
    assert res.error_code == "ERR_DUPLICATE_EVENT"


def test_validation_engine_unknown_and_inactive_source():
    """Verify unknown or inactive sources are rejected."""
    now = datetime.now(timezone.utc)
    
    # Unknown source
    res = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=22.0,
        unit="C",
        timestamp=now,
        event_id="EVT-010",
        source_is_known=False,
        now=now,
    )
    assert res.is_valid is False
    assert res.error_code == "ERR_UNKNOWN_SOURCE"

    # Inactive source
    res_inactive = TelemetryValidationEngine.validate_reading(
        metric="temperature_celsius",
        value=22.0,
        unit="C",
        timestamp=now,
        event_id="EVT-011",
        source_is_active=False,
        now=now,
    )
    assert res_inactive.is_valid is False
    assert res_inactive.error_code == "ERR_SOURCE_INACTIVE"
