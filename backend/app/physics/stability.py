"""Deterministic Gravity Stability Assessment Engine.

Evaluates field deviation, spatial uniformity, node availability, temporal convergence,
and detects threshold violations. Emits SafetyEvent-compatible payloads.

SAFETY INVARIANT:
Outputs are diagnostic and simulation-oriented. Does not operate physical safety interlocks.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from app.physics.gravity_engine import GravitySimulationState, GravityFieldState


class StabilityStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNSTABLE = "UNSTABLE"


@dataclass
class ThresholdViolation:
    """Detected threshold excursion during stability evaluation."""
    violation_type: str
    severity: str
    message: str
    observed_value: float
    threshold_value: float


@dataclass
class StabilityAssessmentResult:
    """Outcome of gravity field stability evaluation."""
    status: StabilityStatus
    stability_score: float              # 0.0 (worst) to 1.0 (ideal)
    target_deviation_percentage: float
    field_uniformity: float
    node_availability_ratio: float
    convergence_delta: float
    violations: List[ThresholdViolation] = field(default_factory=list)
    safety_events: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Dict[str, Any] = field(default_factory=dict)


class GravityStabilityEvaluator:
    """Deterministic evaluator for simulated gravitational stability."""

    # Configurable deterministic thresholds
    MAX_NORMAL_DEVIATION_PCT = 3.0
    MAX_WARNING_DEVIATION_PCT = 8.0

    MIN_NORMAL_UNIFORMITY = 0.75
    MIN_WARNING_UNIFORMITY = 0.50

    MIN_NORMAL_NODE_AVAILABILITY = 0.90
    MIN_WARNING_NODE_AVAILABILITY = 0.75

    MAX_CONVERGENCE_DELTA_PCT = 5.0  # Step-to-step delta exceeding this indicates divergence/instability

    @classmethod
    def evaluate_stability(
        cls,
        current_state: GravitySimulationState,
        previous_state: Optional[GravitySimulationState] = None,
        building_id: Optional[str] = None,
    ) -> StabilityAssessmentResult:
        """Evaluate stability across spatial and temporal dimensions."""
        field_state = current_state.field_state
        dev = field_state.target_deviation_percentage
        uniformity = field_state.field_uniformity
        avail = current_state.active_node_ratio

        # Calculate temporal convergence
        convergence_delta = 0.0
        if previous_state is not None:
            prev_mean = previous_state.field_state.mean_offset_percentage
            curr_mean = field_state.mean_offset_percentage
            convergence_delta = round(abs(curr_mean - prev_mean), 4)

        violations: List[ThresholdViolation] = []
        safety_events: List[Dict[str, Any]] = []

        # 1. Node availability checks
        if avail < 0.50:
            v = ThresholdViolation(
                violation_type="CRITICAL_NODE_LOSS",
                severity="HIGH",
                message=f"Catastrophic node loss: {avail * 100:.1f}% active nodes",
                observed_value=avail,
                threshold_value=0.50,
            )
            violations.append(v)
            safety_events.append({
                "event_type": "GRAVITY_NODE_FAILURE_CLUSTER",
                "severity": "CRITICAL",
                "details": {"active_ratio": avail, "failed_nodes": current_state.total_node_count - current_state.active_node_count},
            })
        elif avail < cls.MIN_WARNING_NODE_AVAILABILITY:
            violations.append(
                ThresholdViolation(
                    violation_type="DEGRADED_NODE_AVAILABILITY",
                    severity="MEDIUM",
                    message=f"Node availability below warning threshold: {avail * 100:.1f}%",
                    observed_value=avail,
                    threshold_value=cls.MIN_WARNING_NODE_AVAILABILITY,
                )
            )

        # 2. Field deviation checks
        if dev > cls.MAX_WARNING_DEVIATION_PCT:
            violations.append(
                ThresholdViolation(
                    violation_type="FIELD_TARGET_DEVIATION_EXCEEDED",
                    severity="HIGH",
                    message=f"Field deviation {dev:.2f}% exceeds warning ceiling {cls.MAX_WARNING_DEVIATION_PCT}%",
                    observed_value=dev,
                    threshold_value=cls.MAX_WARNING_DEVIATION_PCT,
                )
            )
            safety_events.append({
                "event_type": "GRAVITY_FIELD_DEVIATION_CRITICAL",
                "severity": "CRITICAL",
                "details": {"observed_deviation": dev, "threshold": cls.MAX_WARNING_DEVIATION_PCT},
            })
        elif dev > cls.MAX_NORMAL_DEVIATION_PCT:
            violations.append(
                ThresholdViolation(
                    violation_type="FIELD_TARGET_DEVIATION_WARNING",
                    severity="LOW",
                    message=f"Field deviation {dev:.2f}% exceeds normal threshold",
                    observed_value=dev,
                    threshold_value=cls.MAX_NORMAL_DEVIATION_PCT,
                )
            )

        # 3. Uniformity checks
        if uniformity < cls.MIN_WARNING_UNIFORMITY:
            violations.append(
                ThresholdViolation(
                    violation_type="FIELD_IMBALANCE_CRITICAL",
                    severity="HIGH",
                    message=f"Severe field spatial asymmetry; uniformity: {uniformity:.2f}",
                    observed_value=uniformity,
                    threshold_value=cls.MIN_WARNING_UNIFORMITY,
                )
            )
            safety_events.append({
                "event_type": "GRAVITY_FIELD_IMBALANCE",
                "severity": "HIGH",
                "details": {"uniformity": uniformity, "threshold": cls.MIN_WARNING_UNIFORMITY},
            })
        elif uniformity < cls.MIN_NORMAL_UNIFORMITY:
            violations.append(
                ThresholdViolation(
                    violation_type="FIELD_IMBALANCE_WARNING",
                    severity="LOW",
                    message=f"Field uniformity degraded: {uniformity:.2f}",
                    observed_value=uniformity,
                    threshold_value=cls.MIN_NORMAL_UNIFORMITY,
                )
            )

        # 4. Temporal oscillation / convergence check
        if convergence_delta > cls.MAX_CONVERGENCE_DELTA_PCT:
            violations.append(
                ThresholdViolation(
                    violation_type="FIELD_DIVERGENCE_DETECTED",
                    severity="HIGH",
                    message=f"Step-to-step mean delta {convergence_delta:.2f}% indicates oscillation divergence",
                    observed_value=convergence_delta,
                    threshold_value=cls.MAX_CONVERGENCE_DELTA_PCT,
                )
            )
            safety_events.append({
                "event_type": "GRAVITY_OSCILLATION_TRIP",
                "severity": "CRITICAL",
                "details": {"step_delta": convergence_delta, "threshold": cls.MAX_CONVERGENCE_DELTA_PCT},
            })

        # Determine overall status
        if convergence_delta > cls.MAX_CONVERGENCE_DELTA_PCT or avail < 0.50:
            status = StabilityStatus.UNSTABLE
        elif dev > cls.MAX_WARNING_DEVIATION_PCT or uniformity < cls.MIN_WARNING_UNIFORMITY or avail < cls.MIN_WARNING_NODE_AVAILABILITY:
            status = StabilityStatus.CRITICAL
        elif dev > cls.MAX_NORMAL_DEVIATION_PCT or uniformity < cls.MIN_NORMAL_UNIFORMITY or avail < cls.MIN_NORMAL_NODE_AVAILABILITY:
            status = StabilityStatus.WARNING
        else:
            status = StabilityStatus.NORMAL

        # Stability score calculation [0.0, 1.0]
        dev_score = max(0.0, 1.0 - (dev / 15.0))
        conv_score = max(0.0, 1.0 - (convergence_delta / 10.0))
        stability_score = round(
            0.30 * uniformity + 0.30 * avail + 0.25 * dev_score + 0.15 * conv_score, 4
        )
        if status == StabilityStatus.UNSTABLE:
            stability_score = min(stability_score, 0.25)
        elif status == StabilityStatus.CRITICAL:
            stability_score = min(stability_score, 0.50)

        explanation = {
            "status": status.value,
            "uniformity_factor": uniformity,
            "availability_factor": avail,
            "deviation_factor": dev_score,
            "convergence_factor": conv_score,
            "violation_count": len(violations),
            "safety_disclaimer": "Diagnostic assessment for digital-twin simulation. Not a certified structural safety interlock.",
        }

        # Tag building_id if provided
        for ev in safety_events:
            if building_id:
                ev["building_id"] = building_id
            ev["step_number"] = current_state.step_number

        return StabilityAssessmentResult(
            status=status,
            stability_score=stability_score,
            target_deviation_percentage=dev,
            field_uniformity=uniformity,
            node_availability_ratio=avail,
            convergence_delta=convergence_delta,
            violations=violations,
            safety_events=safety_events,
            explanation=explanation,
        )
