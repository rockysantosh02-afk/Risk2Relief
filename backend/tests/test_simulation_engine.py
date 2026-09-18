"""Unit tests for Simulation Scenarios and SimulationRunner."""

import pytest
from app.physics.gravity_engine import Coordinate3D, GravityNodeState, FieldEvaluationPoint
from app.simulation.scenarios import ScenarioExecutor, ScenarioType
from app.simulation.runner import SimulationRunner
from app.physics.structural_risk import RiskLevel


@pytest.fixture
def base_sim_setup():
    """Provides base nodes, members, and evaluation points for scenario testing."""
    nodes = [
        GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 500.0),
        GravityNodeState("N-02", "AG-02", Coordinate3D(20.0, 0.0, 0.0), 500.0),
    ]
    members = [
        {
            "node_id": "SN-01",
            "node_code": "C-01",
            "node_type": "COLUMN",
            "floor_number": 1,
            "zone_code": "CORE",
            "position_x": 10.0,
            "position_y": 0.0,
            "position_z": 0.0,
            "capacity_kn": 2000.0,
            "dead_load_kn": 800.0,
            "live_load_kn": 200.0,
        }
    ]
    eval_pts = [
        FieldEvaluationPoint("SN-01", Coordinate3D(10.0, 0.0, 0.0), reference_dead_load_kn=1000.0)
    ]
    telemetry = {
        "SN-01": {"strain_microstrain": 150.0, "vibration_hz": 8.0, "inclination_deg": 0.01}
    }
    return nodes, members, eval_pts, telemetry


def test_scenario_executor_all_7_scenarios(base_sim_setup):
    """Verify all 7 scenarios modify inputs appropriately."""
    nodes, members, _, telemetry = base_sim_setup

    for sc in ScenarioType:
        mod_nodes, mod_members, mod_tel, target, rel = ScenarioExecutor.apply_scenario(
            sc, nodes, members, telemetry
        )
        assert len(mod_nodes) == len(nodes)
        assert len(mod_members) == len(members)

        if sc == ScenarioType.NODE_FAILURE:
            assert mod_nodes[0].operating_state == "FAILED"
            assert mod_nodes[0].active_field_kn == 0.0

        elif sc == ScenarioType.STRUCTURAL_OVERLOAD:
            assert mod_members[0]["live_load_kn"] > members[0]["live_load_kn"]

        elif sc == ScenarioType.TELEMETRY_FAILURE:
            assert rel < 0.50

        elif sc == ScenarioType.POWER_FAILURE:
            # Nodes tripped offline
            offline_count = sum(1 for n in mod_nodes if n.operating_state == "OFFLINE")
            assert offline_count >= 1


def test_simulation_runner_determinism(base_sim_setup):
    """Verify executing same simulation twice produces identical results."""
    nodes, members, eval_pts, telemetry = base_sim_setup

    run1 = SimulationRunner.execute_simulation(
        run_id="RUN-TEST-01",
        scenario_type="NORMAL",
        nodes=nodes,
        members_data=members,
        evaluation_points=eval_pts,
        telemetry_by_node=telemetry,
        step_count=3,
    )

    run2 = SimulationRunner.execute_simulation(
        run_id="RUN-TEST-02",
        scenario_type="NORMAL",
        nodes=nodes,
        members_data=members,
        evaluation_points=eval_pts,
        telemetry_by_node=telemetry,
        step_count=3,
    )

    assert run1.peak_risk_score == run2.peak_risk_score
    assert run1.final_risk_score == run2.final_risk_score
    assert run1.total_active_relief_kn == run2.total_active_relief_kn
    assert run1.worst_stability_status == run2.worst_stability_status


def test_simulation_runner_emergency_scenario(base_sim_setup):
    """Verify EMERGENCY scenario produces HIGH or CRITICAL risk and logs safety events."""
    nodes, members, eval_pts, telemetry = base_sim_setup

    run = SimulationRunner.execute_simulation(
        run_id="RUN-EMERGENCY-01",
        scenario_type="EMERGENCY",
        nodes=nodes,
        members_data=members,
        evaluation_points=eval_pts,
        telemetry_by_node=telemetry,
        step_count=3,
    )

    assert run.peak_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert len(run.safety_events) >= 1
    assert any(ev["severity"] == "CRITICAL" for ev in run.safety_events)
