"""Unit tests for Deterministic Structural Risk Engine."""

import pytest
from app.physics.gravity_engine import Coordinate3D
from app.physics.structural_load import StructuralLoadEngine, StructuralLoadDistribution
from app.physics.stability import StabilityAssessmentResult, StabilityStatus
from app.physics.structural_risk import (
    StructuralRiskEngine,
    RiskLevel,
)


def _create_mock_distribution(peak_utilization: float, telemetry: dict = None) -> StructuralLoadDistribution:
    """Helper to create a load distribution with controlled utilization."""
    members_data = [
        {
            "node_id": "SN-01",
            "node_code": "COL-01",
            "node_type": "COLUMN",
            "floor_number": 1,
            "zone_code": "CORE",
            "position_x": 0.0,
            "position_y": 0.0,
            "position_z": 0.0,
            "capacity_kn": 1000.0,
            "dead_load_kn": 1000.0 * peak_utilization,
            "live_load_kn": 0.0,
        }
    ]
    tel_map = {"SN-01": telemetry or {}}
    return StructuralLoadEngine.evaluate_building_loads(members_data, telemetry_by_node=tel_map)


def test_structural_risk_nominal():
    """Verify low load and stable conditions evaluate to LOW risk."""
    dist = _create_mock_distribution(0.40)  # 40% utilization
    stab = StabilityAssessmentResult(
        status=StabilityStatus.NORMAL,
        stability_score=0.95,
        target_deviation_percentage=1.0,
        field_uniformity=0.85,
        node_availability_ratio=1.0,
        convergence_delta=0.1,
    )

    res = StructuralRiskEngine.evaluate_risk(dist, stability_result=stab)
    assert res.overall_risk_level == RiskLevel.LOW
    assert res.risk_score < 40.0
    assert len(res.critical_members) == 0


def test_structural_risk_critical_overload():
    """Verify extreme utilization >= 1.0 triggers CRITICAL risk and emergency recommendations."""
    dist = _create_mock_distribution(1.15)  # 115% utilization (structural overload)

    res = StructuralRiskEngine.evaluate_risk(dist)
    assert res.overall_risk_level == RiskLevel.CRITICAL
    assert res.risk_score >= 88.0
    assert len(res.critical_members) >= 1
    assert any("EMERGENCY" in rec for rec in res.action_recommendations)


def test_structural_risk_unstable_gravity_penalty():
    """Verify UNSTABLE gravity field elevates risk level to CRITICAL."""
    dist = _create_mock_distribution(0.65)  # 65% utilization (normally moderate)
    stab_unstable = StabilityAssessmentResult(
        status=StabilityStatus.UNSTABLE,
        stability_score=0.20,
        target_deviation_percentage=12.0,
        field_uniformity=0.30,
        node_availability_ratio=0.40,
        convergence_delta=8.0,
    )

    res = StructuralRiskEngine.evaluate_risk(dist, stability_result=stab_unstable)
    assert res.overall_risk_level == RiskLevel.CRITICAL


def test_structural_risk_telemetry_unreliability_penalty():
    """Verify degraded telemetry reliability (< 0.70) adds an uncertainty risk penalty."""
    dist = _create_mock_distribution(0.50)

    res_reliable = StructuralRiskEngine.evaluate_risk(dist, telemetry_reliability=1.0)
    res_unreliable = StructuralRiskEngine.evaluate_risk(dist, telemetry_reliability=0.20)

    # Uncertainty penalty increases the score
    assert res_unreliable.risk_score > res_reliable.risk_score
    assert any(c.factor_name == "Telemetry Uncertainty Penalty" for c in res_unreliable.contributing_factors)


def test_structural_risk_explainable_contributors():
    """Verify all contributing factors are returned with explicit weights and severity."""
    dist = _create_mock_distribution(
        0.86,
        telemetry={
            "strain_microstrain": 950.0,
            "vibration_hz": 25.0,
            "inclination_deg": 0.12,
            "temperature_celsius": 42.0,
        },
    )

    res = StructuralRiskEngine.evaluate_risk(dist)
    factors = {c.factor_name: c for c in res.contributing_factors}

    assert "Structural Utilization" in factors
    assert "Material Strain" in factors
    assert "Dynamic Vibration" in factors
    assert "Inclination / Plumb Deflection" in factors
    assert "Thermal Differential" in factors
    assert "Simulated Field Stability" in factors

    # Sum of base weights is 1.0
    base_weights = sum(c.weight for c in res.contributing_factors if "Uncertainty" not in c.factor_name)
    assert abs(base_weights - 1.0) < 1e-4
