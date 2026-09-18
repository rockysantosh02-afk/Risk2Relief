"""Deterministic Climate Telemetry Validation Engine.

Enforces physical reality bounds, engineering units, timestamp validity, freshness,
and duplicate detection for multi-source climate observations.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from enum import Enum


class ClimateQualityEnum(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    SUSPECT = "SUSPECT"
    INVALID = "INVALID"
    STALE = "STALE"
    DUPLICATE = "DUPLICATE"


@dataclass
class ClimateValidationOutcome:
    """Outcome of single observation validation check."""
    is_valid: bool
    quality: ClimateQualityEnum
    error_code: Optional[str]
    reason: str
    validated_at: datetime


class ClimateValidationEngine:
    """Deterministic validation engine for climate data streams."""

    # Physical reality ranges for plausible climate observations
    PHYSICAL_RANGES: Dict[str, Tuple[float, float]] = {
        "rainfall_24h": (0.0, 1200.0),       # 0 to 1200 mm/24h (Cherrapunji world record ~1000mm)
        "rainfall_1h": (0.0, 300.0),          # 0 to 300 mm/h
        "temperature_max": (-50.0, 60.0),     # -50C to +60C
        "temperature_min": (-60.0, 50.0),
        "wind_gust_kmh": (0.0, 400.0),        # 0 to 400 km/h (Category 5 cyclone ~300km/h)
        "soil_moisture_pct": (0.0, 100.0),    # 0 to 100%
        "air_pressure_hpa": (850.0, 1085.0),  # Atmospheric pressure bounds
    }

    CANONICAL_UNITS: Dict[str, str] = {
        "rainfall_24h": "mm",
        "rainfall_1h": "mm",
        "temperature_max": "C",
        "temperature_min": "C",
        "wind_gust_kmh": "km/h",
        "soil_moisture_pct": "%",
        "air_pressure_hpa": "hPa",
    }

    # In-memory sliding cache for observation idempotency
    _recent_event_cache: Dict[Tuple[str, str], float] = {}

    @classmethod
    def validate_observation(
        cls,
        source_id: str,
        event_id: str,
        metric: str,
        value: float,
        unit: str,
        timestamp: datetime,
        max_future_skew_seconds: float = 60.0,
        max_staleness_seconds: float = 7200.0,  # 2 hours
    ) -> ClimateValidationOutcome:
        """Execute deterministic multi-stage validation."""
        now = datetime.now(timezone.utc)
        ts_utc = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)

        # 1. Non-finite value check (NaN / Inf)
        if math.isnan(value) or math.isinf(value):
            return ClimateValidationOutcome(
                is_valid=False,
                quality=ClimateQualityEnum.INVALID,
                error_code="ERR_NON_FINITE_VALUE",
                reason="Observation value is NaN or Infinite.",
                validated_at=now,
            )

        # 2. Duplicate Detection
        cache_key = (str(source_id), str(event_id))
        if cache_key in cls._recent_event_cache:
            return ClimateValidationOutcome(
                is_valid=False,
                quality=ClimateQualityEnum.DUPLICATE,
                error_code="ERR_DUPLICATE_OBSERVATION",
                reason=f"Observation with ID '{event_id}' from source '{source_id}' was already ingested.",
                validated_at=now,
            )

        # 3. Unit Validation
        norm_metric = metric.lower().strip()
        norm_unit = unit.strip()
        expected_unit = cls.CANONICAL_UNITS.get(norm_metric)
        if expected_unit and norm_unit.lower() != expected_unit.lower():
            return ClimateValidationOutcome(
                is_valid=False,
                quality=ClimateQualityEnum.INVALID,
                error_code="ERR_INVALID_UNIT",
                reason=f"Unit '{unit}' incompatible with metric '{metric}'. Expected '{expected_unit}'.",
                validated_at=now,
            )

        # 4. Future Timestamp Check
        delta_seconds = (ts_utc - now).total_seconds()
        if delta_seconds > max_future_skew_seconds:
            return ClimateValidationOutcome(
                is_valid=False,
                quality=ClimateQualityEnum.INVALID,
                error_code="ERR_FUTURE_TIMESTAMP",
                reason=f"Observation timestamp is {delta_seconds:.1f}s in the future (exceeds clock skew threshold).",
                validated_at=now,
            )

        # 5. Stale Data Check
        age_seconds = (now - ts_utc).total_seconds()
        if age_seconds > max_staleness_seconds:
            return ClimateValidationOutcome(
                is_valid=True,  # Ingestible as stale historical evidence
                quality=ClimateQualityEnum.STALE,
                error_code="ERR_STALE_OBSERVATION",
                reason=f"Observation age ({age_seconds / 3600.0:.1f}h) exceeds freshness window ({max_staleness_seconds / 3600.0:.1f}h).",
                validated_at=now,
            )

        # 6. Physical Bounds Check
        bounds = cls.PHYSICAL_RANGES.get(norm_metric)
        if bounds:
            min_val, max_val = bounds
            if value < min_val or value > max_val:
                return ClimateValidationOutcome(
                    is_valid=False,
                    quality=ClimateQualityEnum.INVALID,
                    error_code="ERR_OUT_OF_BOUNDS",
                    reason=f"Value {value} {unit} breaches physical reality range [{min_val}, {max_val}] for {metric}.",
                    validated_at=now,
                )

        # Register in sliding window cache
        cls._recent_event_cache[cache_key] = now.timestamp()
        if len(cls._recent_event_cache) > 20000:
            cls._prune_cache(now.timestamp() - 7200.0)

        return ClimateValidationOutcome(
            is_valid=True,
            quality=ClimateQualityEnum.VALID,
            error_code=None,
            reason="Observation verified nominal against all physical and temporal constraints.",
            validated_at=now,
        )

    @classmethod
    def _prune_cache(cls, cutoff_timestamp: float) -> None:
        keys_to_del = [k for k, ts in cls._recent_event_cache.items() if ts < cutoff_timestamp]
        for k in keys_to_del:
            cls._recent_event_cache.pop(k, None)

    @classmethod
    def reset_cache(cls) -> None:
        """Clear cache for demo scenarios."""
        cls._recent_event_cache.clear()
