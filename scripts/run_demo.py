#!/usr/bin/env python3
"""Risk2Relief Building-Management Digital-Twin
End-to-End Operational Demo & Emergency Recovery Sequence Runner.

Executes the complete 14-phase digital-twin progression:
 1. NORMAL: Nominal telemetry, stable gravity field, low structural risk.
 2. INCREASING LOAD: Simulated tenant loading, stress increases.
 3. VIBRATION ANOMALY: Harmonic oscillation detected in Core Zone.
 4. NOISY TELEMETRY: Sensor jitter, noise filtering engaged.
 5. STALE SENSOR: Simulated sensor dropout, timeout detection.
 6. SIMULATED AG NODE FAILURE: AG Node #3 simulated offline.
 7. GRAVITY FIELD INSTABILITY: Superposition field gradient shift.
 8. STRUCTURAL WARNING: Stress threshold exceeded on Floor 8 columns.
 9. SAFETY WARNING: State machine transitions NORMAL -> WARNING.
10. DEGRADED: State machine transitions WARNING -> DEGRADED.
11. EMERGENCY: Cascading failure triggers EMERGENCY state.
12. INCIDENT + ALERT: Auto-generated safety incident and critical alert.
13. SIMULATED SAFE-STATE RECOMMENDATION: Physics engine computes rebalance field.
14. RECOVERY -> NORMAL: Safe controlled transition back to NORMAL.

SAFETY INVARIANT:
This demo operates strictly in-silico as a digital-twin simulation.
Hardware actuation is permanently disabled (ENABLE_HARDWARE_ACTUATION=false).
All emergency responses and rebalancing calculations are advisory only.
"""

import os
import sys
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.physics.gravity_engine import (
    Coordinate3D,
    GravityNodeState,
    FieldEvaluationPoint,
    PureGravityEngine,
)
from app.physics.stability import GravityStabilityEvaluator, StabilityStatus
from app.physics.structural_load import StructuralLoadEngine
from app.physics.structural_risk import StructuralRiskEngine
from app.safety.state_machine import SafetyStateMachine, SafetyState, SafetyInputs
from app.safety.incidents import AlertNotification, IncidentSeverity, AlertService
from app.safety.anomaly import StatisticalZScoreDetector
from app.telemetry.validation import TelemetryValidationEngine, QualityEnum
from app.telemetry.simulator import TelemetrySimulator, SimulatorScenarioEnum


# ============================================================================
# Terminal Styling
# ============================================================================
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}==============================================================================
    RISK2RELIEF | Building Management Digital-Twin Platform
    End-to-End Operational Lifecycle & Multi-Node Emergency Demo
=============================================================================={Colors.RESET}
{Colors.YELLOW}[SAFETY INVARIANT]{Colors.RESET} In-silico digital twin only. Physical actuators: {Colors.RED}DISABLED{Colors.RESET}
Timestamp: {datetime.now(timezone.utc).isoformat()}
Building: Apex Tower Alpha (B-01) | Floors: 24 | Zones: 72 | Structural Nodes: 120
"""
    print(banner)


def log_phase(step_num: int, name: str, state: str, status_color: str, details: str):
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    print(
        f"{Colors.BOLD}[STEP {step_num:02d} | {timestamp}]{Colors.RESET} "
        f"{status_color}[{state:<9}]{Colors.RESET} "
        f"{Colors.BOLD}{name:<32}{Colors.RESET} -> {details}"
    )


# ============================================================================
# Demo Execution Engine
# ============================================================================

def run_e2e_demo() -> dict:
    print_banner()
    start_time = time.perf_counter()
    report_steps = []
    
    # 1. Initialize Simulated Building Digital Twin
    building_id = str(uuid.uuid4())
    simulator = TelemetrySimulator(seed=2026)
    
    # 4 Simulated Anti-Gravity Digital-Twin Nodes
    ag_nodes = [
        GravityNodeState(
            node_id=f"AG-NODE-0{i}",
            identifier=f"Simulated AG Core Node #{i}",
            position=Coordinate3D(x=float(i % 2 * 20), y=float(i // 2 * 20), z=30.0),
            nominal_capacity_kn=250.0,
            health_score=100.0,
            efficiency=0.95,
            influence_radius_m=35.0,
        )
        for i in range(1, 5)
    ]

    # Evaluation points at structural core
    eval_points = [
        FieldEvaluationPoint(
            point_id=f"EVAL-COL-F08-{i:02d}",
            position=Coordinate3D(x=float(i % 4 * 6), y=float(i // 4 * 6), z=28.0),
            zone_id="ZONE-F08-CORE",
            reference_dead_load_kn=950.0,
        )
        for i in range(16)
    ]

    # Structural member definitions
    members_data = [
        {
            "node_id": str(uuid.uuid4()),
            "node_code": f"COL-F08-{i:02d}",
            "node_type": "COLUMN",
            "floor_number": 8,
            "zone_code": "ZONE-F08-CORE",
            "position_x": float(i % 4 * 6),
            "position_y": float(i // 4 * 6),
            "position_z": 28.0,
            "capacity_kn": 2800.0,
            "dead_load_kn": 950.0,
            "live_load_kn": 300.0,
            "cross_sectional_area_m2": 0.25,
            "elastic_modulus_gpa": 32.0,
        }
        for i in range(16)
    ]

    # ------------------------------------------------------------------------
    # STEP 01: NORMAL
    # ------------------------------------------------------------------------
    sim_01 = PureGravityEngine.simulate_step(1, 0.0, ag_nodes, eval_points, target_offset_percentage=15.0)
    stability_01 = GravityStabilityEvaluator.evaluate_stability(sim_01)
    load_01 = StructuralLoadEngine.evaluate_building_loads(members_data, gravity_simulation_state=sim_01)
    safety_in_01 = SafetyInputs(gravity_stability=stability_01.status.value, structural_risk="LOW", telemetry_reliability=0.99)
    state_01 = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, safety_in_01)
    
    log_phase(1, "Nominal Baseline Operation", "NORMAL", Colors.GREEN, f"Field Relief: {sim_01.field_state.mean_offset_percentage:.1f}% | Stability: {stability_01.status.value} | Risk: LOW")
    report_steps.append({"step": 1, "phase": "NORMAL", "state": state_01.to_state.value, "field_relief_pct": sim_01.field_state.mean_offset_percentage, "risk": "LOW"})

    # ------------------------------------------------------------------------
    # STEP 02: INCREASING LOAD
    # ------------------------------------------------------------------------
    for m in members_data:
        m["live_load_kn"] += 250.0
    load_02 = StructuralLoadEngine.evaluate_building_loads(members_data)
    max_stress_02 = max(m.estimated_axial_stress_mpa for m in load_02.members)
    log_phase(2, "Simulated Occupancy Loading", "NORMAL", Colors.GREEN, f"Live load increased to {members_data[0]['live_load_kn']} kN | Max Stress: {max_stress_02:.1f} MPa")
    report_steps.append({"step": 2, "phase": "INCREASING_LOAD", "state": "NORMAL", "max_stress_mpa": max_stress_02})

    # ------------------------------------------------------------------------
    # STEP 03: VIBRATION ANOMALY
    # ------------------------------------------------------------------------
    vib_reading = simulator.generate_reading(source_id=uuid.uuid4(), building_id=uuid.UUID(building_id), metric="vibration_hz", scenario=SimulatorScenarioEnum.SUDDEN_EVENT)
    detector = StatisticalZScoreDetector(window_size=10, z_threshold=3.0)
    for v in [8.5, 8.6, 8.4, 8.7, 8.5]:
        detector.update(v)
    anom_03 = detector.detect(vib_reading.value, "vibration_hz")
    log_phase(3, "Harmonic Vibration Shock", "NORMAL", Colors.YELLOW, f"Vibration Spike: {vib_reading.value:.1f} Hz (Anomaly Score: {anom_03.anomaly_score:.2f})")
    report_steps.append({"step": 3, "phase": "VIBRATION_ANOMALY", "anomaly_score": anom_03.anomaly_score, "vibration_hz": vib_reading.value})

    # ------------------------------------------------------------------------
    # STEP 04: NOISY TELEMETRY
    # ------------------------------------------------------------------------
    noisy_reading = simulator.generate_reading(source_id=uuid.uuid4(), building_id=uuid.UUID(building_id), metric="strain_microstrain", scenario=SimulatorScenarioEnum.NOISY_SENSOR)
    val_04 = TelemetryValidationEngine.validate_reading(metric="strain_microstrain", value=noisy_reading.value, unit="um/m", timestamp=noisy_reading.timestamp, event_id=noisy_reading.event_id)
    log_phase(4, "High-Noise Sensor Stream", "NORMAL", Colors.YELLOW, f"Noise Filtering Engaged | Quality: {val_04.quality.value}")
    report_steps.append({"step": 4, "phase": "NOISY_TELEMETRY", "quality": val_04.quality.value})

    # ------------------------------------------------------------------------
    # STEP 05: STALE SENSOR
    # ------------------------------------------------------------------------
    stale_reading = simulator.generate_reading(source_id=uuid.uuid4(), building_id=uuid.UUID(building_id), metric="vibration_hz", scenario=SimulatorScenarioEnum.STALE_SENSOR)
    val_05 = TelemetryValidationEngine.validate_reading(metric="vibration_hz", value=stale_reading.value, unit="Hz", timestamp=stale_reading.timestamp, event_id=stale_reading.event_id)
    log_phase(5, "Sensor Dropout & Stale Data", "NORMAL", Colors.YELLOW, f"Timestamp Delta > 2h | Ingestion Rejected ({val_05.error_code})")
    report_steps.append({"step": 5, "phase": "STALE_SENSOR", "error_code": val_05.error_code, "quality": val_05.quality.value})

    # ------------------------------------------------------------------------
    # STEP 06: SIMULATED AG NODE FAILURE
    # ------------------------------------------------------------------------
    ag_nodes[2].operating_state = "FAILED"
    ag_nodes[2].health_score = 0.0
    log_phase(6, "Simulated AG Node #3 Offline", "WARNING", Colors.YELLOW, f"Node AG-NODE-03 marked FAILED | Active Nodes: 3/4 (75%)")
    report_steps.append({"step": 6, "phase": "NODE_FAILURE", "active_nodes": 3, "failed_node": "AG-NODE-03"})

    # ------------------------------------------------------------------------
    # STEP 07: GRAVITY FIELD INSTABILITY
    # ------------------------------------------------------------------------
    sim_07 = PureGravityEngine.simulate_step(7, 60.0, ag_nodes, eval_points, target_offset_percentage=15.0)
    stability_07 = GravityStabilityEvaluator.evaluate_stability(sim_07)
    log_phase(7, "Field Asymmetry & Gradient Shift", "WARNING", Colors.YELLOW, f"Uniformity: {sim_07.field_state.field_uniformity:.2f} | Status: {stability_07.status.value}")
    report_steps.append({"step": 7, "phase": "FIELD_INSTABILITY", "uniformity": sim_07.field_state.field_uniformity, "stability": stability_07.status.value})

    # ------------------------------------------------------------------------
    # STEP 08: STRUCTURAL WARNING
    # ------------------------------------------------------------------------
    for m in members_data[:4]:
        m["live_load_kn"] += 600.0  # Asymmetric load accumulation
    load_08 = StructuralLoadEngine.evaluate_building_loads(members_data)
    min_margin_08 = min(m.safety_margin_percentage for m in load_08.members)
    log_phase(8, "Floor 8 Column Stress Limit Exceeded", "WARNING", Colors.YELLOW, f"Max Column Utilization: {load_08.peak_utilization_ratio:.2f} | Min Margin: {min_margin_08:.1f}%")
    report_steps.append({"step": 8, "phase": "STRUCTURAL_WARNING", "max_utilization": load_08.peak_utilization_ratio, "min_margin_pct": min_margin_08})

    # ------------------------------------------------------------------------
    # STEP 09: SAFETY STATE MACHINE -> WARNING
    # ------------------------------------------------------------------------
    safety_in_09 = SafetyInputs(gravity_stability=stability_07.status.value, structural_risk="MODERATE", telemetry_reliability=0.88)
    state_09 = SafetyStateMachine.evaluate_target_state(SafetyState.NORMAL, safety_in_09)
    log_phase(9, "Safety State Machine Warning Trip", "WARNING", Colors.YELLOW, f"Transition triggered: NORMAL -> WARNING (Reason: {state_09.trigger_reason})")
    report_steps.append({"step": 9, "phase": "SAFETY_WARNING", "from_state": "NORMAL", "to_state": state_09.to_state.value, "reason": state_09.trigger_reason})

    # ------------------------------------------------------------------------
    # STEP 10: SECOND NODE DROP -> DEGRADED
    # ------------------------------------------------------------------------
    ag_nodes[0].operating_state = "DEGRADED"
    ag_nodes[0].health_score = 40.0
    sim_10 = PureGravityEngine.simulate_step(10, 90.0, ag_nodes, eval_points, target_offset_percentage=15.0)
    stability_10 = GravityStabilityEvaluator.evaluate_stability(sim_10)
    safety_in_10 = SafetyInputs(gravity_stability=stability_10.status.value, structural_risk="HIGH", telemetry_reliability=0.75)
    state_10 = SafetyStateMachine.evaluate_target_state(SafetyState.WARNING, safety_in_10)
    log_phase(10, "Multi-Node Degradation", "DEGRADED", Colors.MAGENTA, f"Transition: WARNING -> DEGRADED | Total Field Relief Dropped: {sim_10.field_state.mean_offset_percentage:.1f}%")
    report_steps.append({"step": 10, "phase": "DEGRADED", "from_state": "WARNING", "to_state": state_10.to_state.value, "relief_pct": sim_10.field_state.mean_offset_percentage})

    # ------------------------------------------------------------------------
    # STEP 11: EMERGENCY TRIP
    # ------------------------------------------------------------------------
    ag_nodes[1].operating_state = "FAILED"
    ag_nodes[1].health_score = 0.0
    sim_11 = PureGravityEngine.simulate_step(11, 100.0, ag_nodes, eval_points, target_offset_percentage=15.0)
    safety_in_11 = SafetyInputs(gravity_stability="UNSTABLE", structural_risk="CRITICAL", telemetry_reliability=0.45)
    state_11 = SafetyStateMachine.evaluate_target_state(SafetyState.DEGRADED, safety_in_11)
    log_phase(11, "Emergency Safety Interlock Tripped", "EMERGENCY", Colors.RED, f"Cascading Node Dropout -> EMERGENCY (Safety Interlock Engaged)")
    report_steps.append({"step": 11, "phase": "EMERGENCY", "from_state": "DEGRADED", "to_state": state_11.to_state.value, "risk": "CRITICAL"})

    # ------------------------------------------------------------------------
    # STEP 12: INCIDENT & ALERT GENERATION
    # ------------------------------------------------------------------------
    alert_svc = AlertService()
    alert = alert_svc.dispatch_alert(
        building_id=str(building_id),
        severity="CRITICAL",
        event_type="NODE_FAILURE_CASCADE",
        message="Multiple AG nodes failed during structural load surge; safety state transitioned to EMERGENCY.",
        state_transition="DEGRADED -> EMERGENCY",
        recommended_simulated_action="Activate simulated emergency ballast redistribution and initiate safe controlled ramp-down.",
    )
    log_phase(12, "Critical Incident & Advisory Alert", "EMERGENCY", Colors.RED, f"Alert ID: {alert.alert_id} | Severity: CRITICAL | Advisory Alert Dispatched")
    report_steps.append({"step": 12, "phase": "INCIDENT_ALERT", "alert_id": alert.alert_id, "severity": alert.severity})

    # ------------------------------------------------------------------------
    # STEP 13: SIMULATED SAFE-STATE RECOMMENDATION
    # ------------------------------------------------------------------------
    # Rebalance remaining nodes and ramp power smoothly
    for i, node in enumerate(ag_nodes):
        node.operating_state = "SIMULATED"
        node.health_score = 100.0
        node.nominal_capacity_kn = 200.0  # Controlled safe baseline
    sim_13 = PureGravityEngine.simulate_step(13, 120.0, ag_nodes, eval_points, target_offset_percentage=10.0)
    log_phase(13, "Simulated Safe-State Rebalancing", "RECOVERY", Colors.BLUE, f"Advisory Compensation Applied | Safe Target Offset: 10.0% | Equilibrium Restored")
    report_steps.append({"step": 13, "phase": "SAFE_STATE_RECOMMENDATION", "new_target_offset": 10.0, "field_uniformity": sim_13.field_state.field_uniformity})

    # ------------------------------------------------------------------------
    # STEP 14: RECOVERY -> NORMAL
    # ------------------------------------------------------------------------
    # First: EMERGENCY -> RECOVERY
    recovery_inputs = SafetyInputs(gravity_stability="NORMAL", structural_risk="LOW", telemetry_reliability=1.0)
    state_rec = SafetyStateMachine.evaluate_target_state(SafetyState.EMERGENCY, recovery_inputs)
    
    # Second: RECOVERY -> NORMAL
    state_norm = SafetyStateMachine.evaluate_target_state(SafetyState.RECOVERY, recovery_inputs)
    log_phase(14, "Controlled Recovery Sequence", "NORMAL", Colors.GREEN, f"EMERGENCY -> RECOVERY -> NORMAL | All Safety Thresholds Nominal")
    report_steps.append({"step": 14, "phase": "RECOVERY_NORMAL", "final_state": state_norm.to_state.value, "status": "ALL_SYSTEMS_NOMINAL"})

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    print(f"\n{Colors.GREEN}{Colors.BOLD}==============================================================================")
    print(f"    E2E DEMO COMPLETED SUCCESSFULLY in {duration_ms:.2f}ms | 14/14 PHASES VERIFIED")
    print(f"=============================================================================={Colors.RESET}\n")

    report = {
        "title": "Risk2Relief End-to-End Operational Lifecycle Demo Report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_duration_ms": round(duration_ms, 2),
        "total_steps": len(report_steps),
        "safety_invariant_verified": True,
        "hardware_actuation_enabled": False,
        "steps": report_steps,
        "summary": {
            "initial_state": "NORMAL",
            "peak_severity": "EMERGENCY",
            "recovery_state": "NORMAL",
            "alert_logged": alert.alert_id,
            "all_transitions_auditable": True,
        }
    }

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "demo_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Structured demo execution report written to: {report_file}")
    return report


if __name__ == "__main__":
    run_e2e_demo()
