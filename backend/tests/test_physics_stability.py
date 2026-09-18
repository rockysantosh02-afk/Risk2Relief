"""Unit tests for Gravity Stability Assessment Engine."""

import pytest
from app.physics.gravity_engine import (
    Coordinate3D,
    GravityNodeState,
    FieldEvaluationPoint,
    PureGravityEngine,
)
from app.physics.stability import (
    GravityStabilityEvaluator,
    StabilityStatus,
)


def test_stability_evaluator_normal():
    """Verify healthy, well-distributed simulation yields NORMAL stability."""
    nodes = [
        GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 300.0),
        GravityNodeState("N-02", "AG-02", Coordinate3D(10.0, 0.0, 0.0), 300.0),
    ]
    pts = [
        FieldEvaluationPoint("P1", Coordinate3D(5.0, 0.0, 0.0), reference_dead_load_kn=2000.0),
    ]

    sim_state = PureGravityEngine.simulate_step(1, 0.0, nodes, pts, target_offset_percentage=28.0)
    res = GravityStabilityEvaluator.evaluate_stability(sim_state)

    assert res.status in (StabilityStatus.NORMAL, StabilityStatus.WARNING)
    assert res.stability_score >= 0.70
    assert "safety_disclaimer" in res.explanation


def test_stability_evaluator_catastrophic_node_loss():
    """Verify losing > 50% of nodes triggers UNSTABLE status and CRITICAL safety event."""
    # 3 out of 4 nodes failed (25% available)
    nodes = [
        GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 300.0, operating_state="FAILED"),
        GravityNodeState("N-02", "AG-02", Coordinate3D(10.0, 0.0, 0.0), 300.0, operating_state="FAILED"),
        GravityNodeState("N-03", "AG-03", Coordinate3D(20.0, 0.0, 0.0), 300.0, operating_state="FAILED"),
        GravityNodeState("N-04", "AG-04", Coordinate3D(30.0, 0.0, 0.0), 300.0, operating_state="ACTIVE"),
    ]
    pts = [
        FieldEvaluationPoint("P1", Coordinate3D(5.0, 0.0, 0.0), reference_dead_load_kn=2000.0),
    ]

    sim_state = PureGravityEngine.simulate_step(1, 0.0, nodes, pts, target_offset_percentage=15.0)
    res = GravityStabilityEvaluator.evaluate_stability(sim_state, building_id="BLD-01")

    assert res.status == StabilityStatus.UNSTABLE
    assert res.node_availability_ratio == 0.25
    assert res.stability_score <= 0.25
    assert len(res.violations) >= 1
    assert any(v.violation_type == "CRITICAL_NODE_LOSS" for v in res.violations)
    assert len(res.safety_events) >= 1
    assert res.safety_events[0]["severity"] == "CRITICAL"


def test_stability_evaluator_step_convergence_divergence():
    """Verify large delta between steps triggers divergence trip."""
    nodes = [GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 500.0)]
    pts = [FieldEvaluationPoint("P1", Coordinate3D(0.0, 0.0, 0.0), reference_dead_load_kn=1000.0)]

    # Step 1: 50% offset
    step1 = PureGravityEngine.simulate_step(1, 0.0, nodes, pts, target_offset_percentage=50.0)

    # Step 2: sudden jump to 10% offset (40% delta >> 5% threshold)
    nodes_changed = [GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 100.0)]
    step2 = PureGravityEngine.simulate_step(2, 1.0, nodes_changed, pts, target_offset_percentage=10.0)

    res = GravityStabilityEvaluator.evaluate_stability(step2, previous_state=step1)
    assert res.status == StabilityStatus.UNSTABLE
    assert res.convergence_delta >= 30.0
    assert any(v.violation_type == "FIELD_DIVERGENCE_DETECTED" for v in res.violations)
