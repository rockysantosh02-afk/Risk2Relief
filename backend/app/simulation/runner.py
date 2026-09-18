"""Simulation Runner Orchestrating Multi-Node Digital-Twin Physics & Structural Risk.

SAFETY INVARIANT:
In-silico digital twin only. Computes physics and risk in-memory without operating
or communicating with real physical hardware actuators.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from app.physics.gravity_engine import (
    GravityNodeState,
    FieldEvaluationPoint,
    GravitySimulationState,
    PureGravityEngine,
)
from app.physics.stability import (
    GravityStabilityEvaluator,
    StabilityAssessmentResult,
    StabilityStatus,
)
from app.physics.structural_load import (
    StructuralLoadEngine,
    StructuralLoadDistribution,
)
from app.physics.structural_risk import (
    StructuralRiskEngine,
    StructuralRiskAssessment,
    RiskLevel,
)
from app.simulation.scenarios import ScenarioExecutor, ScenarioType


@dataclass
class SimulationStepResult:
    """Consolidated state and results for a single discrete simulation time-step."""
    step_number: int
    timestamp_seconds: float
    gravity_state: GravitySimulationState
    stability_assessment: StabilityAssessmentResult
    load_distribution: StructuralLoadDistribution
    risk_assessment: StructuralRiskAssessment


@dataclass
class SimulationRunResult:
    """Complete summary outcome of a scenario simulation run."""
    run_id: str
    scenario_type: str
    building_id: Optional[str]
    step_count: int
    duration_seconds: float
    peak_risk_level: RiskLevel
    peak_risk_score: float
    final_risk_level: RiskLevel
    final_risk_score: float
    worst_stability_status: StabilityStatus
    total_active_relief_kn: float
    peak_member_utilization: float
    step_results: List[SimulationStepResult] = field(default_factory=list)
    safety_events: List[Dict[str, Any]] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class SimulationRunner:
    """Orchestrates deterministic multi-step digital-twin physics simulations."""

    @classmethod
    def execute_simulation(
        cls,
        run_id: str,
        scenario_type: str | ScenarioType,
        nodes: List[GravityNodeState],
        members_data: List[Dict[str, Any]],
        evaluation_points: List[FieldEvaluationPoint],
        telemetry_by_node: Optional[Dict[str, Dict[str, float]]] = None,
        target_offset_percentage: float = 15.0,
        step_count: int = 5,
        step_duration_seconds: float = 1.0,
        building_id: Optional[str] = None,
    ) -> SimulationRunResult:
        """Run multi-step digital-twin simulation with perturbation injection."""
        tel_data = telemetry_by_node or {}

        # 1. Apply scenario disturbance
        mod_nodes, mod_members, mod_tel, mod_target, tel_reliability = ScenarioExecutor.apply_scenario(
            scenario_type=scenario_type,
            nodes=nodes,
            members_data=members_data,
            telemetry_by_node=tel_data,
            target_offset_percentage=target_offset_percentage,
        )

        step_results: List[SimulationStepResult] = []
        collected_safety_events: List[Dict[str, Any]] = []
        previous_gravity_state: Optional[GravitySimulationState] = None

        peak_score = 0.0
        peak_u = 0.0
        worst_stab = StabilityStatus.NORMAL

        for step in range(1, step_count + 1):
            ts = (step - 1) * step_duration_seconds

            # Step 1: Pure gravity calculation
            grav_state = PureGravityEngine.simulate_step(
                step_number=step,
                timestamp_seconds=ts,
                nodes=mod_nodes,
                evaluation_points=evaluation_points,
                target_offset_percentage=mod_target,
            )

            # Step 2: Stability assessment
            stab_result = GravityStabilityEvaluator.evaluate_stability(
                current_state=grav_state,
                previous_state=previous_gravity_state,
                building_id=building_id,
            )
            grav_state.stability_status = stab_result.status.value

            # Track worst stability
            if stab_result.status == StabilityStatus.UNSTABLE:
                worst_stab = StabilityStatus.UNSTABLE
            elif stab_result.status == StabilityStatus.CRITICAL and worst_stab != StabilityStatus.UNSTABLE:
                worst_stab = StabilityStatus.CRITICAL
            elif stab_result.status == StabilityStatus.WARNING and worst_stab not in (StabilityStatus.CRITICAL, StabilityStatus.UNSTABLE):
                worst_stab = StabilityStatus.WARNING

            # Collect safety events from stability
            for ev in stab_result.safety_events:
                ev["simulation_run_id"] = run_id
                collected_safety_events.append(ev)

            # Step 3: Structural load evaluation
            load_dist = StructuralLoadEngine.evaluate_building_loads(
                members_data=mod_members,
                gravity_simulation_state=grav_state,
                telemetry_by_node=mod_tel,
            )
            if load_dist.peak_utilization_ratio > peak_u:
                peak_u = load_dist.peak_utilization_ratio

            # Step 4: Structural risk evaluation
            risk_res = StructuralRiskEngine.evaluate_risk(
                load_distribution=load_dist,
                stability_result=stab_result,
                telemetry_reliability=tel_reliability,
            )
            if risk_res.risk_score > peak_score:
                peak_score = risk_res.risk_score

            # If risk is CRITICAL or HIGH, record a safety event
            if risk_res.overall_risk_level == RiskLevel.CRITICAL:
                collected_safety_events.append({
                    "simulation_run_id": run_id,
                    "building_id": building_id,
                    "step_number": step,
                    "event_type": "STRUCTURAL_RISK_CRITICAL",
                    "severity": "CRITICAL",
                    "details": {
                        "risk_score": risk_res.risk_score,
                        "peak_utilization": load_dist.peak_utilization_ratio,
                        "critical_members": risk_res.critical_members,
                    },
                })

            step_res = SimulationStepResult(
                step_number=step,
                timestamp_seconds=ts,
                gravity_state=grav_state,
                stability_assessment=stab_result,
                load_distribution=load_dist,
                risk_assessment=risk_res,
            )
            step_results.append(step_res)
            previous_gravity_state = grav_state

        # Final summaries
        final_step = step_results[-1]
        final_risk = final_step.risk_assessment.overall_risk_level
        final_score = final_step.risk_assessment.risk_score

        # Peak risk level classification
        if peak_score >= 88.0:
            peak_level = RiskLevel.CRITICAL
        elif peak_score >= 70.0:
            peak_level = RiskLevel.HIGH
        elif peak_score >= 40.0:
            peak_level = RiskLevel.MODERATE
        else:
            peak_level = RiskLevel.LOW

        summary_metrics = {
            "scenario_type": str(scenario_type),
            "step_count": step_count,
            "duration_seconds": step_count * step_duration_seconds,
            "peak_risk_level": peak_level.value,
            "peak_risk_score": peak_score,
            "final_risk_level": final_risk.value,
            "final_risk_score": final_score,
            "worst_stability_status": worst_stab.value,
            "peak_member_utilization": peak_u,
            "total_applied_load_kn": final_step.load_distribution.total_applied_load_kn,
            "total_simulated_relief_kn": final_step.load_distribution.total_simulated_relief_kn,
            "building_relief_percentage": final_step.load_distribution.overall_building_relief_percentage,
            "critical_members_count": final_step.load_distribution.critical_members_count,
            "safety_event_count": len(collected_safety_events),
        }

        return SimulationRunResult(
            run_id=run_id,
            scenario_type=str(scenario_type),
            building_id=building_id,
            step_count=step_count,
            duration_seconds=step_count * step_duration_seconds,
            peak_risk_level=peak_level,
            peak_risk_score=peak_score,
            final_risk_level=final_risk,
            final_risk_score=final_score,
            worst_stability_status=worst_stab,
            total_active_relief_kn=final_step.load_distribution.total_simulated_relief_kn,
            peak_member_utilization=peak_u,
            step_results=step_results,
            safety_events=collected_safety_events,
            summary_metrics=summary_metrics,
        )
