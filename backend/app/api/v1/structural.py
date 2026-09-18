"""API v1 Structural Health and Structural Risk Assessment Endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query
from app.physics.structural_load import StructuralLoadEngine
from app.physics.gravity_engine import Coordinate3D
from app.physics.stability import StabilityAssessmentResult, StabilityStatus
from app.physics.structural_risk import (
    StructuralRiskEngine,
    RiskLevel,
)

router = APIRouter(prefix="/structural", tags=["Structural Health & Risk"])


@router.post(
    "/health",
    summary="Calculate Structural Member Health & Load Redistribution",
    description="Evaluates member utilization, estimated axial stress, strain, and safety margins under simulated relief.",
)
async def calculate_structural_health(
    members: List[Dict[str, Any]],
    relief_percentage: float = Query(default=15.0, ge=0.0, le=50.0),
) -> List[Dict[str, Any]]:
    results = []
    for m in members:
        pos = Coordinate3D(
            x=float(m.get("x", 0.0)),
            y=float(m.get("y", 0.0)),
            z=float(m.get("z", 0.0)),
        )
        dead = float(m.get("dead_load_kn", 1000.0))
        live = float(m.get("live_load_kn", 500.0))
        relief = (dead + live) * (relief_percentage / 100.0)
        res = StructuralLoadEngine.calculate_member_load(
            node_id=str(m.get("node_id", "COL-1")),
            node_code=str(m.get("node_code", "C-101")),
            node_type=str(m.get("node_type", "COLUMN")),
            floor_number=int(m.get("floor_number", 1)),
            zone_code=str(m.get("zone_code", "ZONE-A")),
            position=pos,
            capacity_kn=float(m.get("capacity_kn", 2500.0)),
            dead_load_kn=dead,
            live_load_kn=live,
            simulated_relief_kn=relief,
            cross_sectional_area_m2=float(m.get("cross_section_area_m2", 0.16)),
            elastic_modulus_gpa=float(m.get("elastic_modulus_gpa", 30.0)),
        )
        results.append({
            "node_id": res.node_id,
            "node_code": res.node_code,
            "node_type": res.node_type,
            "dead_load_kn": res.dead_load_kn,
            "live_load_kn": res.live_load_kn,
            "gravity_relief_kn": res.gravity_relief_kn,
            "net_effective_load_kn": res.net_effective_load_kn,
            "utilization_ratio": res.utilization_ratio,
            "safety_margin_percentage": res.safety_margin_percentage,
            "estimated_axial_stress_mpa": res.estimated_axial_stress_mpa,
            "estimated_strain_microstrain": res.estimated_strain_microstrain,
            "provenance_map": res.provenance_map,
        })
    return results


@router.post(
    "/risk",
    summary="Calculate Composite Structural Risk Score",
    description="Computes explainable composite risk score [0, 100], risk category, and contributing factors.",
)
async def calculate_structural_risk(
    utilization_ratio: float = Query(default=0.60, ge=0.0, le=2.0),
    strain_microstrain: float = Query(default=600.0, ge=0.0),
    vibration_frequency_hz: float = Query(default=12.0, ge=0.0),
    inclination_degrees: float = Query(default=0.05, ge=0.0),
    thermal_gradient_c: float = Query(default=15.0, ge=0.0),
    gravity_stability_status: str = Query(default="NORMAL"),
    telemetry_reliability: float = Query(default=1.0, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    members_data = [
        {
            "node_id": "EVAL-01",
            "node_code": "COL-EVAL",
            "node_type": "COLUMN",
            "floor_number": 1,
            "zone_code": "CORE",
            "position_x": 0.0,
            "position_y": 0.0,
            "position_z": 0.0,
            "capacity_kn": 1000.0,
            "dead_load_kn": 1000.0 * utilization_ratio,
            "live_load_kn": 0.0,
        }
    ]
    tel_map = {
        "EVAL-01": {
            "strain_microstrain": strain_microstrain,
            "vibration_hz": vibration_frequency_hz,
            "inclination_deg": inclination_degrees,
            "temperature_celsius": thermal_gradient_c,
        }
    }
    load_dist = StructuralLoadEngine.evaluate_building_loads(members_data, telemetry_by_node=tel_map)

    stability_enum = StabilityStatus.NORMAL
    try:
        stability_enum = StabilityStatus(gravity_stability_status.upper())
    except ValueError:
        pass

    stab_res = StabilityAssessmentResult(
        status=stability_enum,
        stability_score=0.95,
        target_deviation_percentage=1.0,
        field_uniformity=0.85,
        node_availability_ratio=1.0,
        convergence_delta=0.1,
    )

    assessment = StructuralRiskEngine.evaluate_risk(
        load_distribution=load_dist,
        stability_result=stab_res,
        telemetry_reliability=telemetry_reliability,
    )

    return {
        "risk_score": assessment.risk_score,
        "overall_risk_level": assessment.overall_risk_level.value,
        "peak_utilization_ratio": assessment.peak_utilization_ratio,
        "max_strain_microstrain": assessment.max_strain_microstrain,
        "max_vibration_hz": assessment.max_vibration_hz,
        "max_inclination_deg": assessment.max_inclination_deg,
        "gravity_stability_status": assessment.gravity_stability_status,
        "telemetry_reliability": assessment.telemetry_reliability,
        "contributing_factors": [
            {
                "factor_name": c.factor_name,
                "component_score": c.component_score,
                "weight": c.weight,
                "weighted_score": c.weighted_score,
                "severity": c.severity,
                "description": c.description,
            }
            for c in assessment.contributing_factors
        ],
        "critical_members": assessment.critical_members,
        "action_recommendations": assessment.action_recommendations,
        "safety_disclaimer": assessment.safety_disclaimer,
    }
