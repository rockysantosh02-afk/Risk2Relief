"""Deterministic Telemetry Validation Engine.

Provides rule-based validation for schemas, metric-unit compatibility, physical ranges,
staleness, future timestamps, duplicate events, and source validity.
Does NOT use ML for basic validation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Set, Any, Tuple
from app.schemas.telemetry import QualityEnum

# Recognized metrics, allowable units, and safe physical boundaries
METRIC_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    "strain_microstrain": {
        "valid_units": {"um/m", "microstrain", "με", "ue"},
        "min_value": -10000.0,
        "max_value": 10000.0,
        "description": "Structural strain in microstrain",
    },
    "vibration_hz": {
        "valid_units": {"Hz", "hz"},
        "min_value": 0.0,
        "max_value": 1000.0,
        "description": "Dominant vibration oscillation frequency",
    },
    "temperature_celsius": {
        "valid_units": {"C", "degC", "celsius", "°C"},
        "min_value": -50.0,
        "max_value": 120.0,
        "description": "Ambient or structural temperature in Celsius",
    },
    "load_kn": {
        "valid_units": {"kN", "kn"},
        "min_value": -1000.0,
        "max_value": 50000.0,
        "description": "Structural load in kiloNewtons",
    },
    "inclination_deg": {
        "valid_units": {"deg", "degree", "°"},
        "min_value": -45.0,
        "max_value": 45.0,
        "description": "Angular deflection from plumb in degrees",
    },
    "pressure_kpa": {
        "valid_units": {"kPa", "kpa"},
        "min_value": 50.0,
        "max_value": 200.0,
        "description": "Barometric or hydraulic pressure in kiloPascals",
    },
    "air_quality_aqi": {
        "valid_units": {"AQI", "aqi", "index"},
        "min_value": 0.0,
        "max_value": 500.0,
        "description": "Air quality index",
    },
}

# Threshold limits
MAX_FUTURE_DRIFT_SECONDS = 60.0  # Up to 1 minute clock skew
MAX_STALENESS_SECONDS = 3600.0   # 1 hour staleness threshold


@dataclass
class ValidationResult:
    """Outcome of deterministic telemetry validation."""
    is_valid: bool
    quality: QualityEnum
    error_code: Optional[str] = None
    reason: Optional[str] = None
    anomaly_score: float = 0.0


class TelemetryValidationEngine:
    """Deterministic validation pipeline for telemetry readings."""

    @classmethod
    def validate_reading(
        cls,
        metric: Optional[str],
        value: Optional[float],
        unit: Optional[str],
        timestamp: Optional[datetime],
        event_id: Optional[str],
        source_is_known: bool = True,
        source_is_active: bool = True,
        is_duplicate: bool = False,
        now: Optional[datetime] = None,
    ) -> ValidationResult:
        """Execute deterministic sequence of validation checks.

        Returns a structured ValidationResult with machine-readable error codes.
        """
        # 1. Required field checks
        if not event_id or not metric or value is None or not unit or not timestamp:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.MISSING,
                error_code="ERR_MISSING_FIELD",
                reason="Required telemetry fields missing or null",
                anomaly_score=1.0,
            )

        # 2. Source checks
        if not source_is_known:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.INVALID,
                error_code="ERR_UNKNOWN_SOURCE",
                reason="Telemetry source is not registered in the platform",
                anomaly_score=1.0,
            )
        if not source_is_active:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.INVALID,
                error_code="ERR_SOURCE_INACTIVE",
                reason="Telemetry source is marked OFFLINE or FAULT",
                anomaly_score=0.9,
            )

        # 3. Duplicate event check
        if is_duplicate:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.DUPLICATE,
                error_code="ERR_DUPLICATE_EVENT",
                reason=f"Duplicate event_id '{event_id}' already ingested for this source",
                anomaly_score=1.0,
            )

        # 4. Metric specification checks
        spec = METRIC_SPECIFICATIONS.get(metric)
        if not spec:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.INVALID,
                error_code="ERR_UNKNOWN_METRIC",
                reason=f"Unrecognized metric '{metric}'. Expected one of: {list(METRIC_SPECIFICATIONS.keys())}",
                anomaly_score=0.9,
            )

        # 5. Unit compatibility check
        if unit not in spec["valid_units"]:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.INVALID,
                error_code="ERR_INVALID_UNIT",
                reason=f"Unit '{unit}' is invalid for metric '{metric}'. Allowed: {sorted(list(spec['valid_units']))}",
                anomaly_score=0.8,
            )

        # 6. Timestamp checks
        current_time = now or datetime.now(timezone.utc)
        reading_time = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)

        # Check for future timestamps (exceeding allowable clock skew)
        if reading_time > current_time + timedelta(seconds=MAX_FUTURE_DRIFT_SECONDS):
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.INVALID,
                error_code="ERR_FUTURE_TIMESTAMP",
                reason=f"Reading timestamp {reading_time.isoformat()} is in the future beyond {MAX_FUTURE_DRIFT_SECONDS}s skew limit",
                anomaly_score=0.85,
            )

        # Check for stale timestamps
        if reading_time < current_time - timedelta(seconds=MAX_STALENESS_SECONDS):
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.STALE,
                error_code="ERR_STALE_TIMESTAMP",
                reason=f"Reading timestamp {reading_time.isoformat()} is older than max staleness limit ({MAX_STALENESS_SECONDS}s)",
                anomaly_score=0.75,
            )

        # 7. Physical range plausibility checks
        min_val = spec["min_value"]
        max_val = spec["max_value"]
        if value < min_val or value > max_val:
            return ValidationResult(
                is_valid=False,
                quality=QualityEnum.ANOMALOUS,
                error_code="ERR_PHYSICAL_RANGE_EXCEEDED",
                reason=f"Value {value} {unit} exceeds plausible physical bounds [{min_val}, {max_val}] for metric '{metric}'",
                anomaly_score=0.95,
            )

        # 8. All checks passed
        return ValidationResult(
            is_valid=True,
            quality=QualityEnum.VALID,
            error_code=None,
            reason=None,
            anomaly_score=0.0,
        )
