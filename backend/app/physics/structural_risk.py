"""Deterministic Structural Risk Assessment Engine.

Combines utilization, strain, vibration, inclination, temperature, gravity stability,
and telemetry reliability into an explainable structural risk score.

SAFETY INVARIANT & CERTIFICATION BOUNDARY:
This risk scoring engine uses deterministic rule-based weights. It does NOT use opaque
or non-auditable machine learning models for final risk classification.
Outputs are digital-twin advisory assessments and NOT certified engineering sign-offs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any

from app.physics.structural_load import StructuralLoadDistribution, MemberLoadResult
from app.physics.stability import StabilityAssessmentResult, StabilityStatus


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskContributor:
    """Individual factor contributing to composite structural risk."""
    factor_name: str
    component_score: float  # 0.0 to 100.0
    weight: float           # Relative contribution weight (sum = 1.0)
    weighted_score: float   # component_score * weight
    severity: str           # NORMAL, ELEVATED, HIGH, CRITICAL
    description: str


@dataclass
class StructuralRiskAssessment:
    """Comprehensive explainable structural risk evaluation."""
    overall_risk_level: RiskLevel
    risk_score: float       # 0.0 to 100.0
    peak_utilization_ratio: float
    max_strain_microstrain: float
    max_vibration_hz: float
    max_inclination_deg: float
    gravity_stability_status: str
    telemetry_reliability: float
    contributing_factors: List[RiskContributor] = field(default_factory=list)
    critical_members: List[str] = field(default_factory=list)
    action_recommendations: List[str] = field(default_factory=list)
    safety_disclaimer: str = (
        "Diagnostic digital-twin advisory assessment. "
        "Strictly in-silico simulation; does not supersede certified structural inspections."
    )


class StructuralRiskEngine:
    """Deterministic, explainable risk scoring engine."""

    # Risk level thresholds
    THRESHOLD_MODERATE = 40.0
    THRESHOLD_HIGH = 70.0
    THRESHOLD_CRITICAL = 88.0

    @classmethod
    def evaluate_risk(
        cls,
        load_distribution: StructuralLoadDistribution,
        stability_result: Optional[StabilityAssessmentResult] = None,
        telemetry_reliability: float = 1.0,
    ) -> StructuralRiskAssessment:
        """Calculate composite explainable risk score from physical and simulation states."""
        members = load_distribution.members
        peak_u = load_distribution.peak_utilization_ratio

        # 1. Utilization Score (Weight: 30%)
        # Normal < 0.60 (0-20), Elevated 0.60-0.85 (20-65), High 0.85-1.0 (65-90), Overload >= 1.0 (100)
        if peak_u < 0.60:
            u_score = (peak_u / 0.60) * 20.0
            u_sev = "NORMAL"
        elif peak_u < 0.85:
            u_score = 20.0 + ((peak_u - 0.60) / 0.25) * 45.0
            u_sev = "ELEVATED"
        elif peak_u < 1.0:
            u_score = 65.0 + ((peak_u - 0.85) / 0.15) * 25.0
            u_sev = "HIGH"
        else:
            u_score = min(100.0, 90.0 + (peak_u - 1.0) * 50.0)
            u_sev = "CRITICAL"

        # 2. Strain Score (Weight: 20%)
        # Concrete tensile crack ~200 ue, yield ~1500-2000 ue
        max_strain = 0.0
        for m in members:
            s = m.measured_strain_microstrain if m.measured_strain_microstrain is not None else m.estimated_strain_microstrain
            if s > max_strain:
                max_strain = s

        if max_strain < 300.0:
            strain_score = (max_strain / 300.0) * 20.0
            strain_sev = "NORMAL"
        elif max_strain < 800.0:
            strain_score = 20.0 + ((max_strain - 300.0) / 500.0) * 45.0
            strain_sev = "ELEVATED"
        elif max_strain < 1500.0:
            strain_score = 65.0 + ((max_strain - 800.0) / 700.0) * 25.0
            strain_sev = "HIGH"
        else:
            strain_score = min(100.0, 90.0 + ((max_strain - 1500.0) / 1000.0) * 10.0)
            strain_sev = "CRITICAL"

        # 3. Vibration Score (Weight: 15%)
        # Normal ambient building 2-15 Hz, resonant flutter > 30 Hz
        max_vib = 0.0
        for m in members:
            if m.measured_vibration_hz and m.measured_vibration_hz > max_vib:
                max_vib = m.measured_vibration_hz

        if max_vib < 15.0:
            vib_score = (max_vib / 15.0) * 20.0
            vib_sev = "NORMAL"
        elif max_vib < 35.0:
            vib_score = 20.0 + ((max_vib - 15.0) / 20.0) * 45.0
            vib_sev = "ELEVATED"
        elif max_vib < 60.0:
            vib_score = 65.0 + ((max_vib - 35.0) / 25.0) * 25.0
            vib_sev = "HIGH"
        else:
            vib_score = 100.0
            vib_sev = "CRITICAL"

        # 4. Inclination Score (Weight: 15%)
        # Plumb tolerance: 0.05 deg normal, > 0.2 deg warning, > 0.5 deg critical
        max_incl = 0.0
        for m in members:
            if m.measured_inclination_deg and abs(m.measured_inclination_deg) > max_incl:
                max_incl = abs(m.measured_inclination_deg)

        if max_incl < 0.05:
            incl_score = (max_incl / 0.05) * 15.0
            incl_sev = "NORMAL"
        elif max_incl < 0.20:
            incl_score = 15.0 + ((max_incl - 0.05) / 0.15) * 50.0
            incl_sev = "ELEVATED"
        elif max_incl < 0.50:
            incl_score = 65.0 + ((max_incl - 0.20) / 0.30) * 25.0
            incl_sev = "HIGH"
        else:
            incl_score = 100.0
            incl_sev = "CRITICAL"

        # 5. Temperature Score (Weight: 10%)
        # Baseline 20C. Differentials > 30C elevate thermal stresses
        max_temp_diff = 0.0
        for m in members:
            if m.measured_temperature_c is not None:
                diff = abs(m.measured_temperature_c - 20.0)
                if diff > max_temp_diff:
                    max_temp_diff = diff

        if max_temp_diff < 15.0:
            temp_score = (max_temp_diff / 15.0) * 25.0
            temp_sev = "NORMAL"
        elif max_temp_diff < 35.0:
            temp_score = 25.0 + ((max_temp_diff - 15.0) / 20.0) * 45.0
            temp_sev = "ELEVATED"
        else:
            temp_score = min(100.0, 70.0 + (max_temp_diff - 35.0) * 1.5)
            temp_sev = "HIGH"

        # 6. Gravity Stability Score (Weight: 10%)
        stab_status = stability_result.status if stability_result else StabilityStatus.NORMAL
        if stab_status == StabilityStatus.NORMAL:
            stab_score = 0.0
            stab_sev = "NORMAL"
        elif stab_status == StabilityStatus.WARNING:
            stab_score = 45.0
            stab_sev = "ELEVATED"
        elif stab_status == StabilityStatus.CRITICAL:
            stab_score = 80.0
            stab_sev = "HIGH"
        else:  # UNSTABLE
            stab_score = 100.0
            stab_sev = "CRITICAL"

        # Build Explainable Contributors
        contributors = [
            RiskContributor("Structural Utilization", round(u_score, 2), 0.30, round(u_score * 0.30, 2), u_sev, f"Peak load utilization ratio {peak_u:.2%}"),
            RiskContributor("Material Strain", round(strain_score, 2), 0.20, round(strain_score * 0.20, 2), strain_sev, f"Max tensile/compressive strain {max_strain:.1f} με"),
            RiskContributor("Dynamic Vibration", round(vib_score, 2), 0.15, round(vib_score * 0.15, 2), vib_sev, f"Max dominant oscillation {max_vib:.1f} Hz"),
            RiskContributor("Inclination / Plumb Deflection", round(incl_score, 2), 0.15, round(incl_score * 0.15, 2), incl_sev, f"Max angular deflection {max_incl:.3f}°"),
            RiskContributor("Thermal Differential", round(temp_score, 2), 0.10, round(temp_score * 0.10, 2), temp_sev, f"Max thermal gradient {max_temp_diff:.1f} °C"),
            RiskContributor("Simulated Field Stability", round(stab_score, 2), 0.10, round(stab_score * 0.10, 2), stab_sev, f"Simulated gravity stability status: {stab_status.value}"),
        ]

        # Base composite score
        composite_score = sum(c.weighted_score for c in contributors)

        # Telemetry unreliability penalty: If telemetry is degraded, uncertainty increases risk floor
        if telemetry_reliability < 0.70:
            uncertainty_penalty = (0.70 - telemetry_reliability) * 20.0
            composite_score += uncertainty_penalty
            contributors.append(
                RiskContributor(
                    "Telemetry Uncertainty Penalty",
                    round(uncertainty_penalty / 0.10, 2),
                    0.05,
                    round(uncertainty_penalty, 2),
                    "ELEVATED",
                    f"Sensor unreliability ({telemetry_reliability:.1%}) introduces measurement uncertainty",
                )
            )

        final_risk_score = round(max(0.0, min(100.0, composite_score)), 2)

        # Safety rule: Catastrophic single-factor excursions cannot be diluted by quiet sensors
        if peak_u >= 1.0:
            final_risk_score = max(final_risk_score, round(90.0 + min(10.0, (peak_u - 1.0) * 50.0), 2))
        elif peak_u >= 0.85:
            final_risk_score = max(final_risk_score, round(70.0 + ((peak_u - 0.85) / 0.15) * 18.0), 2)
        elif stab_status == StabilityStatus.UNSTABLE:
            final_risk_score = max(final_risk_score, 90.0)

        # Classify risk level
        if final_risk_score >= cls.THRESHOLD_CRITICAL or peak_u >= 1.0 or stab_status == StabilityStatus.UNSTABLE:
            overall_level = RiskLevel.CRITICAL
        elif final_risk_score >= cls.THRESHOLD_HIGH or peak_u >= 0.85:
            overall_level = RiskLevel.HIGH
        elif final_risk_score >= cls.THRESHOLD_MODERATE or peak_u >= 0.65:
            overall_level = RiskLevel.MODERATE
        else:
            overall_level = RiskLevel.LOW

        critical_members = [
            f"{m.node_code} ({m.node_type} Floor {m.floor_number} Zone {m.zone_code}: {m.utilization_ratio:.1%})"
            for m in members if m.utilization_ratio >= 0.85
        ]

        recommendations = []
        if overall_level == RiskLevel.CRITICAL:
            recommendations.append("EMERGENCY PROTOCOL: Initiate localized zone evacuation simulation.")
            recommendations.append("CRITICAL OVERLOAD: Recalibrate simulated anti-gravity nodal offload vectors immediately.")
        elif overall_level == RiskLevel.HIGH:
            recommendations.append("HIGH STRESS WARNING: Redistribute simulated gravitational relief to critical columns.")
            recommendations.append("Schedule physical ultrasonic non-destructive testing for high-utilization nodes.")
        elif overall_level == RiskLevel.MODERATE:
            recommendations.append("ELEVATED MONITORING: Increase telemetry sampling frequency to 20 Hz.")
        else:
            recommendations.append("Nominal digital-twin operating state. Continue continuous background observation.")

        return StructuralRiskAssessment(
            overall_risk_level=overall_level,
            risk_score=final_risk_score,
            peak_utilization_ratio=peak_u,
            max_strain_microstrain=round(max_strain, 2),
            max_vibration_hz=round(max_vib, 2),
            max_inclination_deg=round(max_incl, 4),
            gravity_stability_status=stab_status.value,
            telemetry_reliability=telemetry_reliability,
            contributing_factors=contributors,
            critical_members=critical_members,
            action_recommendations=recommendations,
        )
