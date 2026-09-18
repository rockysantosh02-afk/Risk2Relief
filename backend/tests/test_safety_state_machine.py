"""Unit tests for the Deterministic Safety State Machine."""

import pytest
from app.safety.state_machine import (
    SafetyStateMachine,
    SafetyState,
    SafetyInputs,
    VALID_TRANSITIONS,
)


def test_safety_state_machine_nominal_stays_normal():
    """Nominal inputs should preserve the NORMAL state."""
    inputs = SafetyInputs(
        gravity_stability="NORMAL",
        structural_risk="LOW",
        telemetry_reliability=0.98,
        power_state="NOMINAL",
        communication_state="CONNECTED",
    )
    eval_result = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, inputs)

    assert eval_result.from_state == SafetyState.NORMAL
    assert eval_result.to_state == SafetyState.NORMAL
    assert not eval_result.is_transition_triggered
    assert eval_result.is_valid_transition


def test_transition_normal_to_warning():
    """Sub-optimal metrics should trigger a transition to WARNING."""
    # Test moderate structural risk
    inputs = SafetyInputs(structural_risk="MODERATE")
    res = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, inputs)
    assert res.to_state == SafetyState.WARNING
    assert res.is_transition_triggered
    assert res.is_valid_transition
    assert "Structural risk MODERATE" in res.trigger_reason

    # Test warning gravity stability
    inputs_grav = SafetyInputs(gravity_stability="WARNING")
    res_grav = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, inputs_grav)
    assert res_grav.to_state == SafetyState.WARNING

    # Test degraded telemetry (< 0.75)
    inputs_tel = SafetyInputs(telemetry_reliability=0.70)
    res_tel = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, inputs_tel)
    assert res_tel.to_state == SafetyState.WARNING


def test_transition_warning_to_degraded():
    """Critical gravity or high structural risk should escalate from WARNING to DEGRADED."""
    inputs = SafetyInputs(
        gravity_stability="CRITICAL",
        structural_risk="HIGH",
    )
    res = SafetyStateMachine.evaluate_target_state(SafetyState.WARNING, inputs)
    assert res.from_state == SafetyState.WARNING
    assert res.to_state == SafetyState.DEGRADED
    assert res.is_transition_triggered
    assert res.is_valid_transition
    assert "Gravity stability CRITICAL" in res.trigger_reason
    assert "Structural member stress HIGH" in res.trigger_reason


def test_transition_degraded_to_emergency():
    """Unstable gravity, critical structural risk, or power offline triggers EMERGENCY."""
    inputs = SafetyInputs(
        gravity_stability="UNSTABLE",
        structural_risk="CRITICAL",
    )
    res = SafetyStateMachine.evaluate_target_state(SafetyState.DEGRADED, inputs)
    assert res.from_state == SafetyState.DEGRADED
    assert res.to_state == SafetyState.EMERGENCY
    assert res.is_transition_triggered
    assert res.is_valid_transition


def test_emergency_override_from_normal():
    """Direct transition from NORMAL to EMERGENCY is allowed for catastrophic hazards (e.g. seismic PGA >= 0.40g)."""
    inputs = SafetyInputs(
        environmental_conditions={"seismic_pga_g": 0.52}
    )
    res = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, inputs)
    assert res.from_state == SafetyState.NORMAL
    assert res.to_state == SafetyState.EMERGENCY
    assert res.is_transition_triggered
    assert res.is_valid_transition
    assert "Severe seismic ground acceleration detected" in res.trigger_reason


def test_emergency_cannot_bypass_recovery_to_normal():
    """From EMERGENCY, returning nominal inputs must transition to RECOVERY, never directly to NORMAL."""
    nominal_inputs = SafetyInputs()
    res = SafetyStateMachine.evaluate_target_state(SafetyState.EMERGENCY, nominal_inputs)
    assert res.from_state == SafetyState.EMERGENCY
    assert res.to_state == SafetyState.RECOVERY
    assert res.is_transition_triggered
    assert res.is_valid_transition
    assert "Emergency hazards cleared; starting RECOVERY protocol" in res.trigger_reason


def test_recovery_progression_to_normal():
    """From RECOVERY, nominal inputs successfully transition back to NORMAL."""
    nominal_inputs = SafetyInputs()
    res = SafetyStateMachine.evaluate_target_state(SafetyState.RECOVERY, nominal_inputs)
    assert res.from_state == SafetyState.RECOVERY
    assert res.to_state == SafetyState.NORMAL
    assert res.is_transition_triggered
    assert res.is_valid_transition
    assert "Recovery verification complete" in res.trigger_reason


def test_maintenance_mode_activation_and_exit():
    """Maintenance mode flags override input evaluation into MAINTENANCE and return cleanly to NORMAL."""
    # Enter maintenance from NORMAL
    maint_inputs = SafetyInputs(is_maintenance_mode=True)
    res = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, maint_inputs)
    assert res.to_state == SafetyState.MAINTENANCE
    assert res.is_transition_triggered
    assert res.is_valid_transition

    # Exit maintenance back to NORMAL
    nominal_inputs = SafetyInputs(is_maintenance_mode=False)
    exit_res = SafetyStateMachine.evaluate_target_state(SafetyState.MAINTENANCE, nominal_inputs)
    assert exit_res.to_state == SafetyState.NORMAL
    assert exit_res.is_transition_triggered
    assert exit_res.is_valid_transition


def test_valid_transitions_matrix_completeness():
    """Verify validity matrix contains all defined safety states."""
    for state in SafetyState:
        assert state in VALID_TRANSITIONS
        # Transitions must be sets of valid SafetyState instances
        for target in VALID_TRANSITIONS[state]:
            assert isinstance(target, SafetyState)
