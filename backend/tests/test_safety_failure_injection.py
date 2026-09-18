"""Unit tests for the Controlled Failure Injection Simulation Engine across 15 fault modes."""

import pytest
from app.safety.failure_injection import (
    FailureInjectionEngine,
    FailureMode,
    FailureInjectionResult,
)
from app.safety.state_machine import SafetyState


@pytest.mark.parametrize("mode", list(FailureMode))
def test_all_15_failure_injection_modes(mode: FailureMode):
    """Verify that every one of the 15 simulated failure modes executes deterministically."""
    result: FailureInjectionResult = FailureInjectionEngine.execute_failure_scenario(
        scenario=mode,
        initial_state=SafetyState.NORMAL,
    )

    assert result.scenario == mode
    assert result.detected is True
    assert result.detection_latency_ms >= 0.0
    assert result.data_integrity_preserved is True
    assert result.duplicate_prevented is True
    assert result.data_loss_count == 0
    assert result.recovery_successful is True
    assert result.safety_response_appropriate is True
    assert "In-silico controlled resilience testing only" in result.safety_disclaimer


def test_catastrophic_overload_reaches_emergency():
    """Structural overload and environmental seismic shocks must escalate directly to EMERGENCY."""
    overload = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.STRUCTURAL_OVERLOAD,
        initial_state=SafetyState.NORMAL,
    )
    assert overload.resulting_safety_state == SafetyState.EMERGENCY
    assert overload.safety_response_appropriate is True

    seismic = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.ENVIRONMENTAL_EMERGENCY,
        initial_state=SafetyState.NORMAL,
    )
    assert seismic.resulting_safety_state == SafetyState.EMERGENCY
    assert seismic.safety_response_appropriate is True


def test_multiple_node_and_corrupted_telemetry_degrade_state():
    """Multiple node failure or high-corruption telemetry must escalate to at least DEGRADED."""
    multi = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.MULTIPLE_NODE_FAILURE,
        initial_state=SafetyState.NORMAL,
    )
    assert multi.resulting_safety_state in (SafetyState.DEGRADED, SafetyState.EMERGENCY)

    corrupted = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.CORRUPTED_TELEMETRY,
        initial_state=SafetyState.NORMAL,
    )
    assert corrupted.resulting_safety_state in (SafetyState.DEGRADED, SafetyState.EMERGENCY)


def test_duplicate_and_config_tamper_preserve_integrity():
    """Duplicate sensor re-transmission and invalid config attempts preserve system integrity."""
    dup_res = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.DUPLICATE_SENSOR,
        initial_state=SafetyState.NORMAL,
    )
    assert dup_res.duplicate_prevented is True
    assert dup_res.data_integrity_preserved is True

    cfg_res = FailureInjectionEngine.execute_failure_scenario(
        FailureMode.INVALID_CONFIGURATION,
        initial_state=SafetyState.NORMAL,
    )
    assert cfg_res.data_integrity_preserved is True
    assert "Safety Barrier" in cfg_res.details["fault"]
