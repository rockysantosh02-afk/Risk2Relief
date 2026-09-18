"""Unit tests for Pure Computational Gravity Digital-Twin Engine."""

import pytest
from app.physics.gravity_engine import (
    Coordinate3D,
    GravityNodeState,
    FieldEvaluationPoint,
    PureGravityEngine,
)


def test_coordinate_distance():
    """Verify Euclidean 3D distance calculation."""
    c1 = Coordinate3D(0.0, 0.0, 0.0)
    c2 = Coordinate3D(3.0, 4.0, 0.0)
    assert c1.distance_to(c2) == 5.0

    c3 = Coordinate3D(1.0, 2.0, 2.0)
    c4 = Coordinate3D(1.0, 2.0, 5.0)
    assert c3.distance_to(c4) == 3.0


def test_node_active_field_calculation():
    """Verify nominal, efficiency, health score, and operating state effects on active field output."""
    # Active node with 100% health, 100% efficiency
    n_active = GravityNodeState(
        node_id="N-01",
        identifier="AG-01",
        position=Coordinate3D(0.0, 0.0, 0.0),
        nominal_capacity_kn=500.0,
        operating_state="ACTIVE",
        health_score=100.0,
        efficiency=1.0,
    )
    assert n_active.is_active is True
    assert n_active.active_field_kn == 500.0

    # Degraded efficiency (0.8) and health (80%)
    n_deg = GravityNodeState(
        node_id="N-02",
        identifier="AG-02",
        position=Coordinate3D(0.0, 0.0, 0.0),
        nominal_capacity_kn=500.0,
        operating_state="ACTIVE",
        health_score=80.0,
        efficiency=0.8,
    )
    # 500 * 0.8 * 0.8 = 320.0
    assert n_deg.active_field_kn == 320.0

    # FAILED node -> 0.0 kN
    n_failed = GravityNodeState(
        node_id="N-03",
        identifier="AG-03",
        position=Coordinate3D(0.0, 0.0, 0.0),
        nominal_capacity_kn=500.0,
        operating_state="FAILED",
    )
    assert n_failed.is_active is False
    assert n_failed.active_field_kn == 0.0


def test_node_spatial_attenuation():
    """Verify rational quadratic spatial attenuation w(r) = 1 / (1 + (r / R0)^2)."""
    node = GravityNodeState(
        node_id="N-01",
        identifier="AG-01",
        position=Coordinate3D(0.0, 0.0, 0.0),
        nominal_capacity_kn=400.0,
        influence_radius_m=10.0,
    )

    # At source (r=0): w(0) = 1.0 -> 400.0 kN
    assert node.calculate_contribution_at(Coordinate3D(0.0, 0.0, 0.0)) == 400.0

    # At r = R0 = 10.0m: w(10) = 1 / (1 + 1) = 0.5 -> 200.0 kN
    assert node.calculate_contribution_at(Coordinate3D(10.0, 0.0, 0.0)) == 200.0

    # At r = 2*R0 = 20.0m: w(20) = 1 / (1 + 4) = 0.2 -> 80.0 kN
    assert node.calculate_contribution_at(Coordinate3D(20.0, 0.0, 0.0)) == 80.0

    # Beyond 5x R0 = 51.0m: cutoff to 0.0
    assert node.calculate_contribution_at(Coordinate3D(51.0, 0.0, 0.0)) == 0.0


def test_pure_gravity_field_superposition():
    """Verify multiple simulated nodes superpose deterministically across evaluation points."""
    nodes = [
        GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 500.0, influence_radius_m=10.0),
        GravityNodeState("N-02", "AG-02", Coordinate3D(20.0, 0.0, 0.0), 500.0, influence_radius_m=10.0),
    ]

    # Evaluation point midway between nodes at (10, 0, 0)
    eval_pt = FieldEvaluationPoint(
        point_id="PT-MID",
        position=Coordinate3D(10.0, 0.0, 0.0),
        reference_dead_load_kn=2000.0,
    )

    field_state = PureGravityEngine.calculate_field(
        nodes=nodes,
        evaluation_points=[eval_pt],
        target_offset_percentage=25.0,
    )

    # N1 at dist 10: 250 kN; N2 at dist 10: 250 kN; Total: 500 kN
    pt_res = field_state.evaluation_points[0]
    assert pt_res.combined_field_kn == 500.0
    # Offset: 500 / 2000 = 25.0%
    assert pt_res.effective_offset_percentage == 25.0
    assert field_state.mean_offset_percentage == 25.0
    assert field_state.target_deviation_percentage == 0.0
    assert field_state.total_field_relief_kn == 500.0


def test_field_uniformity_and_step_execution():
    """Verify uniformity calculation and simulate_step return values."""
    nodes = [
        GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 500.0),
    ]
    # Points at varying distances
    pts = [
        FieldEvaluationPoint("P1", Coordinate3D(0.0, 0.0, 0.0), reference_dead_load_kn=1000.0),
        FieldEvaluationPoint("P2", Coordinate3D(15.0, 0.0, 0.0), reference_dead_load_kn=1000.0),
        FieldEvaluationPoint("P3", Coordinate3D(30.0, 0.0, 0.0), reference_dead_load_kn=1000.0),
    ]

    sim_state = PureGravityEngine.simulate_step(
        step_number=1,
        timestamp_seconds=0.0,
        nodes=nodes,
        evaluation_points=pts,
        target_offset_percentage=20.0,
    )

    assert sim_state.step_number == 1
    assert sim_state.active_node_count == 1
    assert sim_state.active_node_ratio == 1.0
    assert 0.0 <= sim_state.field_state.field_uniformity <= 1.0
