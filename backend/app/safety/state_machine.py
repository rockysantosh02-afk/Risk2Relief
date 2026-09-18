"""Deterministic Safety State Machine for Building Digital Twin.

States:
- NORMAL
- WARNING
- DEGRADED
- EMERGENCY
- RECOVERY
- MAINTENANCE

SAFETY INVARIANT:
State machine operations run within the digital-twin simulation.
Transitions are deterministic and fully auditable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, Set, Tuple


class SafetyState(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    EMERGENCY = "EMERGENCY"
    RECOVERY = "RECOVERY"
    MAINTENANCE = "MAINTENANCE"


# Allowable state transitions
VALID_TRANSITIONS: Dict[SafetyState, Set[SafetyState]] = {
    SafetyState.NORMAL: {SafetyState.WARNING, SafetyState.MAINTENANCE},
    SafetyState.WARNING: {SafetyState.NORMAL, SafetyState.DEGRADED, SafetyState.MAINTENANCE},
    SafetyState.DEGRADED: {SafetyState.WARNING, SafetyState.EMERGENCY, SafetyState.RECOVERY, SafetyState.MAINTENANCE},
    SafetyState.EMERGENCY: {SafetyState.RECOVERY},
    SafetyState.RECOVERY: {SafetyState.NORMAL, SafetyState.DEGRADED, SafetyState.EMERGENCY, SafetyState.MAINTENANCE},
    SafetyState.MAINTENANCE: {SafetyState.NORMAL, SafetyState.RECOVERY},
}


@dataclass
class SafetyInputs:
    """Multi-modal environmental, physical, and infrastructure observation inputs."""
    gravity_stability: str = "NORMAL"         # NORMAL, WARNING, CRITICAL, UNSTABLE
    structural_risk: str = "LOW"               # LOW, MODERATE, HIGH, CRITICAL
    telemetry_reliability: float = 1.0         # 0.0 to 1.0
    power_state: str = "NOMINAL"               # NOMINAL, BACKUP, CRITICAL_LOW, OFFLINE
    communication_state: str = "CONNECTED"     # CONNECTED, DEGRADED, DISCONNECTED
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    is_maintenance_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gravity_stability": self.gravity_stability,
            "structural_risk": self.structural_risk,
            "telemetry_reliability": round(self.telemetry_reliability, 4),
            "power_state": self.power_state,
            "communication_state": self.communication_state,
            "environmental_conditions": self.environmental_conditions,
            "is_maintenance_mode": self.is_maintenance_mode,
        }


@dataclass
class SafetyStateEvaluation:
    """Outcome of safety state evaluation and transition check."""
    from_state: SafetyState
    to_state: SafetyState
    is_transition_triggered: bool
    is_valid_transition: bool
    trigger_reason: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SafetyStateMachine:
    """Deterministic, auditable safety state engine."""

    @classmethod
    def evaluate_target_state(
        cls,
        current_state: SafetyState | str,
        inputs: SafetyInputs,
    ) -> SafetyStateEvaluation:
        """Evaluate inputs and determine if a deterministic state transition must occur."""
        curr = SafetyState(current_state.upper()) if isinstance(current_state, str) else current_state

        # 1. Maintenance mode override
        if inputs.is_maintenance_mode:
            target = SafetyState.MAINTENANCE
            reason = "Manual or scheduled maintenance mode activated"
            evidence = {"maintenance_flag": True}
            is_valid = target in VALID_TRANSITIONS[curr] or curr == target
            return SafetyStateEvaluation(
                from_state=curr,
                to_state=target,
                is_transition_triggered=(curr != target),
                is_valid_transition=is_valid,
                trigger_reason=reason,
                evidence=evidence,
            )

        # 2. EMERGENCY guards (highest priority)
        # Unstable gravity, critical structural risk, total power failure, or extreme seismic event
        is_seismic_emergency = inputs.environmental_conditions.get("seismic_pga_g", 0.0) >= 0.40
        if (
            inputs.gravity_stability.upper() == "UNSTABLE"
            or inputs.structural_risk.upper() == "CRITICAL"
            or inputs.power_state.upper() == "OFFLINE"
            or is_seismic_emergency
        ):
            target = SafetyState.EMERGENCY
            reasons = []
            if inputs.gravity_stability.upper() == "UNSTABLE":
                reasons.append("Gravity field oscillation / divergence UNSTABLE")
            if inputs.structural_risk.upper() == "CRITICAL":
                reasons.append("Structural risk CRITICAL (utilization >= 100%)")
            if inputs.power_state.upper() == "OFFLINE":
                reasons.append("Facility power supply completely OFFLINE")
            if is_seismic_emergency:
                reasons.append("Severe seismic ground acceleration detected")

            reason = "; ".join(reasons)
            evidence = inputs.to_dict()

            # Note: If already in EMERGENCY, state remains EMERGENCY
            # Transition from DEGRADED or WARNING to EMERGENCY
            # If from NORMAL, emergency transitions must be permitted via safety override
            is_valid = (target in VALID_TRANSITIONS.get(curr, set())) or (curr == SafetyState.NORMAL) or (curr == target)
            return SafetyStateEvaluation(
                from_state=curr,
                to_state=target,
                is_transition_triggered=(curr != target),
                is_valid_transition=is_valid,
                trigger_reason=reason,
                evidence=evidence,
            )

        # 3. DEGRADED guards
        # Critical gravity, high structural risk, critical low power, comms severed, or telemetry < 0.40
        if (
            inputs.gravity_stability.upper() == "CRITICAL"
            or inputs.structural_risk.upper() == "HIGH"
            or inputs.power_state.upper() == "CRITICAL_LOW"
            or inputs.communication_state.upper() == "DISCONNECTED"
            or inputs.telemetry_reliability < 0.40
        ):
            # If coming from EMERGENCY, cannot jump directly to DEGRADED without RECOVERY
            if curr == SafetyState.EMERGENCY:
                target = SafetyState.RECOVERY
                reason = "Emergency conditions subsided; entering RECOVERY inspection phase"
            else:
                target = SafetyState.DEGRADED
                reasons = []
                if inputs.gravity_stability.upper() == "CRITICAL":
                    reasons.append("Gravity stability CRITICAL")
                if inputs.structural_risk.upper() == "HIGH":
                    reasons.append("Structural member stress HIGH")
                if inputs.power_state.upper() == "CRITICAL_LOW":
                    reasons.append("Power system at CRITICAL_LOW capacity")
                if inputs.communication_state.upper() == "DISCONNECTED":
                    reasons.append("Telemetry communication link severed")
                if inputs.telemetry_reliability < 0.40:
                    reasons.append(f"Severe telemetry unreliability: {inputs.telemetry_reliability:.1%}")
                reason = "; ".join(reasons)

            is_valid = target in VALID_TRANSITIONS.get(curr, set()) or curr == target
            return SafetyStateEvaluation(
                from_state=curr,
                to_state=target,
                is_transition_triggered=(curr != target),
                is_valid_transition=is_valid,
                trigger_reason=reason,
                evidence=inputs.to_dict(),
            )

        # 4. WARNING guards
        # Warning gravity, moderate structural risk, backup power, degraded comms, or telemetry < 0.75
        if (
            inputs.gravity_stability.upper() == "WARNING"
            or inputs.structural_risk.upper() == "MODERATE"
            or inputs.power_state.upper() == "BACKUP"
            or inputs.communication_state.upper() == "DEGRADED"
            or inputs.telemetry_reliability < 0.75
        ):
            if curr == SafetyState.EMERGENCY:
                target = SafetyState.RECOVERY
                reason = "Transitioning from emergency to RECOVERY"
            elif curr == SafetyState.DEGRADED:
                target = SafetyState.WARNING
                reason = "Conditions improving from DEGRADED to WARNING"
            else:
                target = SafetyState.WARNING
                reasons = []
                if inputs.gravity_stability.upper() == "WARNING":
                    reasons.append("Gravity stability field WARNING")
                if inputs.structural_risk.upper() == "MODERATE":
                    reasons.append("Structural risk MODERATE")
                if inputs.power_state.upper() == "BACKUP":
                    reasons.append("Facility running on BACKUP generator")
                if inputs.communication_state.upper() == "DEGRADED":
                    reasons.append("Telemetry packet loss / network degraded")
                if inputs.telemetry_reliability < 0.75:
                    reasons.append(f"Telemetry reliability sub-optimal: {inputs.telemetry_reliability:.1%}")
                reason = "; ".join(reasons)

            is_valid = target in VALID_TRANSITIONS.get(curr, set()) or curr == target
            return SafetyStateEvaluation(
                from_state=curr,
                to_state=target,
                is_transition_triggered=(curr != target),
                is_valid_transition=is_valid,
                trigger_reason=reason,
                evidence=inputs.to_dict(),
            )

        # 5. Recovery progression: If in EMERGENCY or RECOVERY with all nominal inputs
        if curr in (SafetyState.EMERGENCY, SafetyState.RECOVERY):
            if curr == SafetyState.EMERGENCY:
                target = SafetyState.RECOVERY
                reason = "Emergency hazards cleared; starting RECOVERY protocol"
            else:
                target = SafetyState.NORMAL
                reason = "Recovery verification complete: all metrics returned to NOMINAL"

            is_valid = target in VALID_TRANSITIONS.get(curr, set()) or curr == target
            return SafetyStateEvaluation(
                from_state=curr,
                to_state=target,
                is_transition_triggered=(curr != target),
                is_valid_transition=is_valid,
                trigger_reason=reason,
                evidence=inputs.to_dict(),
            )

        # 6. Return to NORMAL (from WARNING or MAINTENANCE)
        target = SafetyState.NORMAL
        reason = "All inputs within baseline operating thresholds"
        is_valid = target in VALID_TRANSITIONS.get(curr, set()) or curr == target
        return SafetyStateEvaluation(
            from_state=curr,
            to_state=target,
            is_transition_triggered=(curr != target),
            is_valid_transition=is_valid,
            trigger_reason=reason,
            evidence=inputs.to_dict(),
        )
