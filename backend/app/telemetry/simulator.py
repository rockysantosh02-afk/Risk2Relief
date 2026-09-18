"""Deterministic Synthetic Telemetry Generator.

Generates realistic sensor streams across 8 disturbance scenarios using seeded random numbers:
- NORMAL
- INCREASING_LOAD
- STRUCTURAL_STRESS
- SENSOR_FAILURE
- NOISY_SENSOR
- STALE_SENSOR
- DUPLICATE_SENSOR
- SUDDEN_EVENT

CRITICAL SYSTEM REQUIREMENT:
All generated telemetry is emitted as standard TelemetryReadingCreate payloads and
MUST be ingested via the exact same TelemetryService ingestion pipeline as external data.
"""

import math
import random
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any

from app.schemas.telemetry import TelemetryReadingCreate, QualityEnum


class SimulatorScenarioEnum(str, Enum):
    NORMAL = "NORMAL"
    INCREASING_LOAD = "INCREASING_LOAD"
    STRUCTURAL_STRESS = "STRUCTURAL_STRESS"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    NOISY_SENSOR = "NOISY_SENSOR"
    STALE_SENSOR = "STALE_SENSOR"
    DUPLICATE_SENSOR = "DUPLICATE_SENSOR"
    SUDDEN_EVENT = "SUDDEN_EVENT"


# Baseline parameters for metrics
METRIC_BASELINES = {
    "strain_microstrain": {"base": 120.0, "unit": "um/m", "amp": 15.0},
    "vibration_hz": {"base": 8.5, "unit": "Hz", "amp": 1.2},
    "temperature_celsius": {"base": 22.0, "unit": "C", "amp": 3.0},
    "load_kn": {"base": 1500.0, "unit": "kN", "amp": 100.0},
    "inclination_deg": {"base": 0.05, "unit": "deg", "amp": 0.02},
    "pressure_kpa": {"base": 101.3, "unit": "kPa", "amp": 0.5},
    "air_quality_aqi": {"base": 35.0, "unit": "AQI", "amp": 5.0},
}


class TelemetrySimulator:
    """Deterministic generator for synthetic digital-twin telemetry."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)
        self._step_counter = 0

    def reset(self, seed: Optional[int] = None):
        """Reset the internal pseudorandom number generator state."""
        if seed is not None:
            self.seed = seed
        self._rng = random.Random(self.seed)
        self._step_counter = 0

    def generate_reading(
        self,
        source_id: uuid.UUID,
        building_id: uuid.UUID,
        metric: str,
        scenario: SimulatorScenarioEnum = SimulatorScenarioEnum.NORMAL,
        zone_id: Optional[uuid.UUID] = None,
        base_time: Optional[datetime] = None,
        event_id_override: Optional[str] = None,
    ) -> TelemetryReadingCreate:
        """Generate a single reading payload conforming to the specified scenario."""
        self._step_counter += 1
        t = self._step_counter
        cfg = METRIC_BASELINES.get(metric, {"base": 100.0, "unit": "raw", "amp": 10.0})
        unit = cfg["unit"]
        base_val = cfg["base"]
        amp = cfg["amp"]

        current_time = base_time or datetime.now(timezone.utc)
        reading_time = current_time + timedelta(seconds=t)

        # Baseline harmonic oscillation + gaussian noise
        harmonic = amp * math.sin(t * 0.1)
        noise = self._rng.gauss(0.0, amp * 0.15)
        computed_val = base_val + harmonic + noise

        quality = QualityEnum.VALID

        # Apply scenario behaviors
        if scenario == SimulatorScenarioEnum.NORMAL:
            pass  # Normal baseline

        elif scenario == SimulatorScenarioEnum.INCREASING_LOAD:
            drift = t * (amp * 0.3)
            computed_val += drift

        elif scenario == SimulatorScenarioEnum.STRUCTURAL_STRESS:
            # Extreme structural stress close to threshold
            stress_multiplier = 4.5 + self._rng.random()
            computed_val = base_val * stress_multiplier

        elif scenario == SimulatorScenarioEnum.SENSOR_FAILURE:
            # Flatline at 0.0 or dead value
            computed_val = 0.0

        elif scenario == SimulatorScenarioEnum.NOISY_SENSOR:
            # Extreme random variance (10x normal noise)
            computed_val += self._rng.gauss(0.0, amp * 5.0)

        elif scenario == SimulatorScenarioEnum.STALE_SENSOR:
            # Reading generated with timestamp 3 hours in the past
            reading_time = current_time - timedelta(hours=3, seconds=t)

        elif scenario == SimulatorScenarioEnum.DUPLICATE_SENSOR:
            # Constant event_id to simulate repeated re-transmission
            event_id_override = f"DUP-REPEATED-EVENT-{source_id}"

        elif scenario == SimulatorScenarioEnum.SUDDEN_EVENT:
            # Sharp step-function transient impulse (seismic shock)
            if t % 10 == 0:
                computed_val += amp * 8.0

        event_id = event_id_override or f"SIM-EVT-{source_id}-{t}-{self._rng.randint(1000, 9999)}"

        return TelemetryReadingCreate(
            source_id=source_id,
            building_id=building_id,
            zone_id=zone_id,
            metric=metric,
            value=round(computed_val, 4),
            unit=unit,
            timestamp=reading_time,
            event_id=event_id,
            quality=quality,
            metadata_json={
                "is_synthetic": True,
                "scenario": scenario.value,
                "step": t,
                "seed": self.seed,
            },
        )

    def generate_batch(
        self,
        source_id: uuid.UUID,
        building_id: uuid.UUID,
        metric: str,
        count: int = 10,
        scenario: SimulatorScenarioEnum = SimulatorScenarioEnum.NORMAL,
        zone_id: Optional[uuid.UUID] = None,
        base_time: Optional[datetime] = None,
    ) -> List[TelemetryReadingCreate]:
        """Generate a series of contiguous readings for a scenario."""
        return [
            self.generate_reading(
                source_id=source_id,
                building_id=building_id,
                metric=metric,
                scenario=scenario,
                zone_id=zone_id,
                base_time=base_time,
            )
            for _ in range(count)
        ]
