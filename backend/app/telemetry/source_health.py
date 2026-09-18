"""Telemetry Source Health & Explainable Reliability Intelligence Engine.

Computes source-level operational metrics:
- last seen timestamp
- freshness in seconds
- error rate, duplicate rate, anomaly rate
- availability based on sampling frequency
- explainable reliability score (0.0 to 1.0)

SAFETY INVARIANT:
The reliability score is diagnostic/observational only and must NOT be used as
an automated final safety decision.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Sequence
from pydantic import BaseModel, Field


class SourceHealthMetrics(BaseModel):
    """Health and reliability metrics for a telemetry sensor source."""
    source_id: uuid.UUID
    source_identifier: str
    status: str
    last_seen: Optional[datetime] = None
    freshness_seconds: Optional[float] = None
    total_readings: int = 0
    valid_readings: int = 0
    error_readings: int = 0
    duplicate_readings: int = 0
    anomalous_readings: int = 0
    error_rate: float = 0.0
    duplicate_rate: float = 0.0
    anomaly_rate: float = 0.0
    availability: float = 1.0
    reliability_score: float = 1.0
    is_healthy: bool = True
    explanation: Dict[str, Any] = Field(default_factory=dict)


class SourceHealthEngine:
    """Calculates explainable health and reliability scores for telemetry sources."""

    @classmethod
    def calculate_health(
        cls,
        source_id: uuid.UUID,
        source_identifier: str,
        status: str,
        sampling_rate_hz: float,
        readings: Sequence[Any],
        now: Optional[datetime] = None,
        evaluation_window_seconds: float = 3600.0,
    ) -> SourceHealthMetrics:
        """Compute metrics and explainable reliability score over an evaluation window."""
        current_time = now or datetime.now(timezone.utc)

        total = len(readings)
        valid = 0
        errors = 0
        duplicates = 0
        anomalies = 0
        latest_timestamp = None

        for r in readings:
            ts = r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc)
            if latest_timestamp is None or ts > latest_timestamp:
                latest_timestamp = ts

            quality = getattr(r, "quality", "VALID")
            if quality == "VALID":
                valid += 1
            elif quality in ("INVALID", "MISSING"):
                errors += 1
            elif quality == "DUPLICATE":
                duplicates += 1
            elif quality in ("ANOMALOUS", "STALE"):
                anomalies += 1

        # Calculate freshness
        freshness_secs = None
        freshness_factor = 1.0
        if latest_timestamp:
            freshness_secs = max(0.0, (current_time - latest_timestamp).total_seconds())
            # Fresh within 30s -> 1.0; decaying to 0.0 over 1 hour
            freshness_factor = max(0.0, 1.0 - (freshness_secs / 3600.0))
        else:
            freshness_factor = 0.0

        # Error, duplicate, and anomaly rates
        error_rate = (errors / total) if total > 0 else 0.0
        duplicate_rate = (duplicates / total) if total > 0 else 0.0
        anomaly_rate = (anomalies / total) if total > 0 else 0.0

        # Availability calculation: actual vs expected packets
        expected_readings = max(1.0, sampling_rate_hz * evaluation_window_seconds)
        availability = min(1.0, total / expected_readings) if expected_readings > 0 else 1.0

        # If offline or fault, apply heavy penalty
        status_multiplier = 1.0
        if status.upper() == "OFFLINE":
            status_multiplier = 0.4
        elif status.upper() == "FAULT":
            status_multiplier = 0.1

        # Explainable reliability formula:
        # Base fidelity from components:
        # 40% Accuracy (1 - error_rate) + 25% Plausibility (1 - anomaly_rate) + 20% Availability + 15% Freshness
        component_accuracy = 0.40 * (1.0 - error_rate)
        component_plausibility = 0.25 * (1.0 - anomaly_rate)
        component_availability = 0.20 * availability
        component_freshness = 0.15 * freshness_factor

        base_score = component_accuracy + component_plausibility + component_availability + component_freshness

        # Heavy error degradation: if errors occur, scale by error penalty factor
        error_penalty_factor = max(0.1, (1.0 - error_rate))

        score_unscaled = base_score * error_penalty_factor
        reliability_score = round(max(0.0, min(1.0, score_unscaled * status_multiplier)), 4)
        is_healthy = reliability_score >= 0.70 and status.upper() == "ONLINE" and error_rate < 0.15

        explanation = {
            "accuracy_component": round(component_accuracy, 4),
            "plausibility_component": round(component_plausibility, 4),
            "availability_component": round(component_availability, 4),
            "freshness_component": round(component_freshness, 4),
            "error_penalty_factor": round(error_penalty_factor, 4),
            "status_multiplier": status_multiplier,
            "formula": "reliability = (0.40*acc + 0.25*plaus + 0.20*avail + 0.15*fresh) * (1 - err) * status_mult",
            "safety_disclaimer": "Diagnostic/observational metric only; must not replace certified safety interlocks.",
        }

        return SourceHealthMetrics(
            source_id=source_id,
            source_identifier=source_identifier,
            status=status,
            last_seen=latest_timestamp,
            freshness_seconds=freshness_secs,
            total_readings=total,
            valid_readings=valid,
            error_readings=errors,
            duplicate_readings=duplicates,
            anomalous_readings=anomalies,
            error_rate=round(error_rate, 4),
            duplicate_rate=round(duplicate_rate, 4),
            anomaly_rate=round(anomaly_rate, 4),
            availability=round(availability, 4),
            reliability_score=reliability_score,
            is_healthy=is_healthy,
            explanation=explanation,
        )
