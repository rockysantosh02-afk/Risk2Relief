"""Unit tests for Structural Load & Response Engine."""

import pytest
from app.physics.gravity_engine import Coordinate3D, PureGravityEngine, GravityNodeState, FieldEvaluationPoint
from app.physics.structural_load import (
    StructuralLoadEngine,
    DataProvenance,
)


def test_member_load_calculation_basic():
    """Verify load redistribution, utilization, stress, and strain."""
    # Capacity 2000 kN, Dead 1000 kN, Live 500 kN -> Applied 1500 kN
    # Gravity relief: 500 kN -> Net effective: 1000 kN
    # Area: 0.25 m2, E = 30 GPa
    res = StructuralLoadEngine.calculate_member_load(
        node_id="NODE-01",
        node_code="C-01",
        node_type="COLUMN",
        floor_number=1,
        zone_code="CORE",
        position=Coordinate3D(0.0, 0.0, 0.0),
        capacity_kn=2000.0,
        dead_load_kn=1000.0,
        live_load_kn=500.0,
        simulated_relief_kn=500.0,
        cross_sectional_area_m2=0.25,
        elastic_modulus_gpa=30.0,
    )

    assert res.net_effective_load_kn == 1000.0
    # Utilization: 1000 / 2000 = 0.50 (50%)
    assert res.utilization_ratio == 0.50
    # Safety margin: (1 - 0.5) * 100 = 50%
    assert res.safety_margin_percentage == 50.0
    # Stress: (1000 * 0.001) / 0.25 = 4.0 MPa
    assert res.estimated_axial_stress_mpa == 4.0
    # Strain: (4.0 / 30.0) * 1000 = 133.33 microstrain
    assert res.estimated_strain_microstrain == 133.33


def test_member_data_provenance_distinction():
    """Verify explicit data provenance tracking (MEASURED, SIMULATED, ESTIMATED)."""
    tel = {
        "strain_microstrain": 142.5,
        "vibration_hz": 12.0,
        "inclination_deg": 0.02,
        "temperature_celsius": 21.5,
    }
    res = StructuralLoadEngine.calculate_member_load(
        node_id="NODE-02",
        node_code="C-02",
        node_type="COLUMN",
        floor_number=2,
        zone_code="PERIMETER",
        position=Coordinate3D(5.0, 5.0, 4.0),
        capacity_kn=2000.0,
        dead_load_kn=800.0,
        live_load_kn=200.0,
        simulated_relief_kn=200.0,
        telemetry=tel,
    )

    prov = res.provenance_map
    assert prov["dead_load_kn"] == DataProvenance.ESTIMATED.value
    assert prov["gravity_relief_kn"] == DataProvenance.SIMULATED.value
    assert prov["net_effective_load_kn"] == DataProvenance.ESTIMATED.value
    assert prov["utilization_ratio"] == DataProvenance.ESTIMATED.value
    assert prov["measured_strain_microstrain"] == DataProvenance.MEASURED.value
    assert prov["measured_vibration_hz"] == DataProvenance.MEASURED.value
    assert prov["measured_inclination_deg"] == DataProvenance.MEASURED.value
    assert prov["measured_temperature_c"] == DataProvenance.MEASURED.value


def test_evaluate_building_loads():
    """Verify whole-building load evaluation under simulated gravity state."""
    nodes = [GravityNodeState("N-01", "AG-01", Coordinate3D(0.0, 0.0, 0.0), 400.0)]
    pts = [FieldEvaluationPoint("NODE-01", Coordinate3D(0.0, 0.0, 0.0), reference_dead_load_kn=1000.0)]
    sim_state = PureGravityEngine.simulate_step(1, 0.0, nodes, pts)

    members_data = [
        {
            "node_id": "NODE-01",
            "node_code": "C-01",
            "node_type": "COLUMN",
            "floor_number": 1,
            "zone_code": "CORE",
            "position_x": 0.0,
            "position_y": 0.0,
            "position_z": 0.0,
            "capacity_kn": 2000.0,
            "dead_load_kn": 1000.0,
            "live_load_kn": 200.0,
        }
    ]

    dist = StructuralLoadEngine.evaluate_building_loads(
        members_data=members_data,
        gravity_simulation_state=sim_state,
    )

    assert dist.total_structural_dead_load_kn == 1000.0
    assert dist.total_live_load_kn == 200.0
    assert dist.total_applied_load_kn == 1200.0
    assert dist.total_simulated_relief_kn == 400.0
    assert dist.net_building_load_kn == 800.0
    assert dist.overall_building_relief_percentage == 33.33
    assert len(dist.members) == 1
    assert "In-silico digital-twin simulation" in dist.disclaimer
