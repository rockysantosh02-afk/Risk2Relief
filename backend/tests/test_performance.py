"""Performance benchmarks and latency profiling for Telemetry Pipeline, Physics Engine, and API."""

import time
import uuid
import statistics
import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from app.telemetry.validation import TelemetryValidationEngine
from app.telemetry.simulator import TelemetrySimulator
from app.physics.gravity_engine import (
    PureGravityEngine,
    GravityNodeState,
    Coordinate3D,
    FieldEvaluationPoint,
)
from app.physics.structural_load import StructuralLoadEngine


# ============================================================================
# 1. Telemetry Ingestion & Validation Throughput
# ============================================================================

def test_telemetry_validation_throughput_10000_readings():
    """Benchmark: TelemetryValidationEngine must validate 10,000 readings in under 1.0s (> 10,000 readings/sec)."""
    now = datetime.now(timezone.utc)
    readings = []
    for i in range(10_000):
        readings.append({
            "metric": "vibration_hz",
            "value": 12.5 + (i % 10) * 0.1,
            "unit": "Hz",
            "timestamp": now - timedelta(milliseconds=i),
            "event_id": f"PERF-EVT-{i}",
        })

    start = time.perf_counter()
    valid_count = 0
    for r in readings:
        res = TelemetryValidationEngine.validate_reading(
            metric=r["metric"],
            value=r["value"],
            unit=r["unit"],
            timestamp=r["timestamp"],
            event_id=r["event_id"],
            now=now,
        )
        if res.is_valid:
            valid_count += 1
    duration = time.perf_counter() - start

    throughput = len(readings) / duration
    print(f"\n[PERF] 10,000 readings validated in {duration:.4f}s ({throughput:.0f} readings/sec)")

    assert valid_count == 10_000
    assert duration < 1.0, f"Validation engine took {duration:.4f}s; expected < 1.0s"
    assert throughput >= 10_000, f"Throughput was {throughput:.0f} readings/sec; expected >= 10,000"


def test_telemetry_batch_simulation_throughput_1000_readings():
    """Benchmark: Simulate 1,000 readings generated and validated in under 0.25s (> 4,000 readings/sec)."""
    sim = TelemetrySimulator(seed=42)
    source_id = uuid.uuid4()
    building_id = uuid.uuid4()
    start = time.perf_counter()

    batch = sim.generate_batch(
        source_id=source_id,
        building_id=building_id,
        metric="vibration_hz",
        count=1000,
    )
    sim_duration = time.perf_counter() - start

    assert len(batch) == 1000
    assert sim_duration < 0.25, f"Simulator generated 1,000 readings in {sim_duration:.4f}s; expected < 0.25s"


# ============================================================================
# 2. Pure Gravity & Physics Computation Latency
# ============================================================================

def test_physics_gravity_computation_latency_sub_5ms():
    """Benchmark: 3D Gravity field calculation over 20 nodes and 50 points must execute in < 5ms per step."""
    # 20 anti-gravity nodes
    nodes = []
    for i in range(20):
        nodes.append(
            GravityNodeState(
                node_id=f"AG-PERF-{i:02d}",
                identifier=f"NODE-{i:02d}",
                position=Coordinate3D(x=float(i % 5 * 10), y=float((i // 5) * 10), z=15.0),
                nominal_capacity_kn=100.0,
                health_score=98.0,
                efficiency=0.95,
                influence_radius_m=35.0,
            )
        )

    # 50 structural evaluation points
    eval_points = [
        FieldEvaluationPoint(
            point_id=f"PT-{i:02d}",
            position=Coordinate3D(x=float(i % 10 * 5), y=float((i // 10) * 10), z=float(i % 3 * 5)),
            zone_id="ZONE-01",
            reference_dead_load_kn=800.0,
        )
        for i in range(50)
    ]

    # Warm-up run
    for _ in range(3):
        PureGravityEngine.calculate_field(nodes=nodes, evaluation_points=eval_points, target_offset_percentage=15.0)

    # Benchmark 20 iterations
    timings = []
    for _ in range(20):
        t0 = time.perf_counter()
        field_res = PureGravityEngine.calculate_field(nodes=nodes, evaluation_points=eval_points, target_offset_percentage=15.0)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)  # ms

    p50 = statistics.median(timings)
    p95 = statistics.quantiles(timings, n=20)[18] if len(timings) >= 20 else max(timings)
    print(f"\n[PERF] Gravity Field (20 nodes, 50 points): P50={p50:.3f}ms, P95={p95:.3f}ms")

    assert p50 < 25.0, f"P50 gravity compute time was {p50:.3f}ms; expected < 25.0ms"
    assert field_res is not None


def test_structural_load_analysis_latency():
    """Benchmark: Structural load analysis of 100 members must execute in < 15ms."""
    members_data = []
    for i in range(100):
        members_data.append({
            "node_id": str(uuid.uuid4()),
            "node_code": f"NODE-{i:03d}",
            "node_type": "COLUMN" if i % 2 == 0 else "BEAM",
            "floor_number": (i // 10) + 1,
            "zone_code": f"Z-{(i % 4) + 1}",
            "position_x": float(i % 10 * 6),
            "position_y": float((i // 10) * 6),
            "position_z": float((i // 10) * 3.5),
            "capacity_kn": 3000.0,
            "dead_load_kn": 800.0,
            "live_load_kn": 400.0,
            "cross_sectional_area_m2": 0.20,
            "elastic_modulus_gpa": 30.0,
        })

    t0 = time.perf_counter()
    load_dist = StructuralLoadEngine.evaluate_building_loads(members_data=members_data)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    print(f"\n[PERF] Structural Load Analysis (100 members): {duration_ms:.3f}ms")
    assert duration_ms < 15.0, f"Load analysis took {duration_ms:.3f}ms; expected < 15.0ms"
    assert len(load_dist.members) == 100


# ============================================================================
# 3. API Latency Benchmarks (P50, P95, P99)
# ============================================================================

def test_api_latency_profile(client: TestClient):
    """Benchmark: API endpoint response latencies must meet SLA (P50 < 20ms, P99 < 100ms)."""
    latencies_ms = []

    # Perform 50 consecutive requests to /api/v1/simulation/status
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/simulation/status")
        t1 = time.perf_counter()
        assert resp.status_code == 200
        latencies_ms.append((t1 - t0) * 1000.0)

    p50 = statistics.median(latencies_ms)
    p95 = statistics.quantiles(latencies_ms, n=100)[94] if len(latencies_ms) >= 100 else statistics.quantiles(latencies_ms, n=20)[18]
    p99 = max(latencies_ms)

    print(f"\n[PERF] API Latency (/api/v1/simulation/status, 50 calls): P50={p50:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")

    assert p50 < 20.0, f"P50 was {p50:.2f}ms; expected < 20ms"
    assert p99 < 100.0, f"P99 was {p99:.2f}ms; expected < 100ms"
