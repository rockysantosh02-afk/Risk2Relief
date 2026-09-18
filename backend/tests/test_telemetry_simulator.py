"""Unit tests for Deterministic Telemetry Simulator across 8 disturbance scenarios."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.telemetry.simulator import (
    TelemetrySimulator,
    SimulatorScenarioEnum,
    METRIC_BASELINES,
)
from app.telemetry.validation import TelemetryValidationEngine
from app.schemas.telemetry import QualityEnum


def test_simulator_determinism():
    """Verify identical seeds produce identical telemetry sequences."""
    source_id = uuid.uuid4()
    building_id = uuid.uuid4()
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)

    sim1 = TelemetrySimulator(seed=12345)
    seq1 = [
        sim1.generate_reading(source_id, building_id, "vibration_hz", SimulatorScenarioEnum.NORMAL, base_time=now)
        for _ in range(5)
    ]

    sim2 = TelemetrySimulator(seed=12345)
    seq2 = [
        sim2.generate_reading(source_id, building_id, "vibration_hz", SimulatorScenarioEnum.NORMAL, base_time=now)
        for _ in range(5)
    ]

    for r1, r2 in zip(seq1, seq2):
        assert r1.value == r2.value
        assert r1.event_id == r2.event_id
        assert r1.timestamp == r2.timestamp


def test_simulator_all_8_scenarios():
    """Verify all 8 disturbance scenarios generate expected signatures."""
    source_id = uuid.uuid4()
    building_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. NORMAL
    sim = TelemetrySimulator(seed=42)
    r_norm = sim.generate_reading(source_id, building_id, "strain_microstrain", SimulatorScenarioEnum.NORMAL, base_time=now)
    assert 50.0 < r_norm.value < 200.0

    # 2. INCREASING_LOAD
    sim = TelemetrySimulator(seed=42)
    readings_load = [
        sim.generate_reading(source_id, building_id, "load_kn", SimulatorScenarioEnum.INCREASING_LOAD, base_time=now)
        for _ in range(10)
    ]
    # Trend should be upward
    assert readings_load[-1].value > readings_load[0].value

    # 3. STRUCTURAL_STRESS
    sim = TelemetrySimulator(seed=42)
    r_stress = sim.generate_reading(source_id, building_id, "strain_microstrain", SimulatorScenarioEnum.STRUCTURAL_STRESS, base_time=now)
    assert r_stress.value > 400.0  # Significant stress elevation

    # 4. SENSOR_FAILURE
    sim = TelemetrySimulator(seed=42)
    r_fail = sim.generate_reading(source_id, building_id, "temperature_celsius", SimulatorScenarioEnum.SENSOR_FAILURE, base_time=now)
    assert r_fail.value == 0.0

    # 5. NOISY_SENSOR
    sim = TelemetrySimulator(seed=42)
    readings_noisy = [
        sim.generate_reading(source_id, building_id, "vibration_hz", SimulatorScenarioEnum.NOISY_SENSOR, base_time=now)
        for _ in range(10)
    ]
    values = [r.value for r in readings_noisy]
    assert max(values) - min(values) > 5.0  # High dispersion

    # 6. STALE_SENSOR
    sim = TelemetrySimulator(seed=42)
    r_stale = sim.generate_reading(source_id, building_id, "pressure_kpa", SimulatorScenarioEnum.STALE_SENSOR, base_time=now)
    assert r_stale.timestamp < now - timedelta(hours=2)

    # 7. DUPLICATE_SENSOR
    sim = TelemetrySimulator(seed=42)
    r_dup1 = sim.generate_reading(source_id, building_id, "load_kn", SimulatorScenarioEnum.DUPLICATE_SENSOR, base_time=now)
    r_dup2 = sim.generate_reading(source_id, building_id, "load_kn", SimulatorScenarioEnum.DUPLICATE_SENSOR, base_time=now)
    assert r_dup1.event_id == r_dup2.event_id

    # 8. SUDDEN_EVENT
    sim = TelemetrySimulator(seed=42)
    readings_sudden = [
        sim.generate_reading(source_id, building_id, "vibration_hz", SimulatorScenarioEnum.SUDDEN_EVENT, base_time=now)
        for _ in range(11)
    ]
    # Step 10 should experience spike
    assert readings_sudden[9].value > readings_sudden[0].value + 5.0


def test_simulator_payload_passes_validation_when_normal():
    """Verify normal simulated readings are fully accepted by TelemetryValidationEngine."""
    sim = TelemetrySimulator(seed=999)
    source_id = uuid.uuid4()
    building_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    reading = sim.generate_reading(
        source_id,
        building_id,
        "temperature_celsius",
        SimulatorScenarioEnum.NORMAL,
        base_time=now,
    )

    val_res = TelemetryValidationEngine.validate_reading(
        metric=reading.metric,
        value=reading.value,
        unit=reading.unit,
        timestamp=reading.timestamp,
        event_id=reading.event_id,
        now=reading.timestamp,  # Same clock
    )

    assert val_res.is_valid is True
    assert val_res.quality == QualityEnum.VALID
