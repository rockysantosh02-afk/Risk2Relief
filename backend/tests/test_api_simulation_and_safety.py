"""API tests for Simulation, Structural Health, Environmental, Safety, Incidents, Alerts, and Reports."""

import uuid
from starlette.testclient import TestClient


def test_simulation_and_physics_api(client: TestClient):
    """Verify simulation execution, status, and pure gravity calculation endpoints."""
    # 1. Simulation Status
    status_resp = client.get("/api/v1/simulation/status")
    assert status_resp.status_code == 200
    stat_data = status_resp.json()
    assert stat_data["mode"] == "in-silico-only"
    assert stat_data["safety_boundary"]["hardware_actuators_allowed"] is False

    # 2. Setup Building for Simulation Execution
    bld_code = f"SIM-{uuid.uuid4().hex[:6].upper()}"
    bld_resp = client.post("/api/v1/buildings", json={"name": "Physics Center", "code": bld_code, "number_of_floors": 4})
    assert bld_resp.status_code == 201
    bld_id = bld_resp.json()["id"]

    # 3. Execute Simulation Run
    exec_payload = {
        "scenario_type": "NORMAL",
        "step_count": 3,
        "step_duration_seconds": 1.0,
        "target_offset_percentage": 15.0,
    }
    exec_resp = client.post(f"/api/v1/simulation/{bld_id}/execute", json=exec_payload)
    assert exec_resp.status_code == 201
    run_data = exec_resp.json()
    run_id = run_data["id"]
    assert run_data["status"] == "COMPLETED"
    assert len(run_data["step_results_json"]) == 3

    # 4. List Simulation Runs
    list_runs_resp = client.get(f"/api/v1/simulation/runs?building_id={bld_id}")
    assert list_runs_resp.status_code == 200
    assert list_runs_resp.json()["total"] >= 1

    # 5. Get Simulation Run Details
    detail_resp = client.get(f"/api/v1/simulation/runs/{run_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == run_id

    # 6. Ad-Hoc Gravity Field Calculation
    field_payload = {
        "nodes": [
            {"node_id": "N1", "x": 0.0, "y": 0.0, "z": 0.0, "capacity_kn": 600.0, "is_active": True}
        ],
        "eval_points": [
            {"point_id": "P1", "x": 5.0, "y": 0.0, "z": 0.0}
        ],
    }
    field_resp = client.post("/api/v1/simulation/gravity/field?target_offset_percentage=15.0", json=field_payload)
    assert field_resp.status_code == 200
    field_data = field_resp.json()
    assert "mean_offset_percentage" in field_data
    assert "In-silico pure mathematical calculation" in field_data["disclaimer"]


def test_structural_health_and_risk_api(client: TestClient):
    """Verify structural member load redistribution and composite risk calculation."""
    # 1. Structural Health
    health_payload = {
        "members": [
            {
                "node_id": "COL-101",
                "node_code": "C1",
                "node_type": "COLUMN",
                "floor_number": 1,
                "zone_code": "CORE",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "dead_load_kn": 1200.0,
                "live_load_kn": 300.0,
                "capacity_kn": 3000.0,
            }
        ]
    }
    h_resp = client.post("/api/v1/structural/health?relief_percentage=15.0", json=health_payload["members"])
    assert h_resp.status_code == 200
    members = h_resp.json()
    assert len(members) == 1
    assert members[0]["utilization_ratio"] < 0.60
    assert members[0]["gravity_relief_kn"] > 0.0

    # 2. Structural Risk Calculation
    r_resp = client.post("/api/v1/structural/risk?utilization_ratio=0.55&strain_microstrain=500.0")
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert "risk_score" in r_data
    assert r_data["overall_risk_level"] in ("LOW", "MODERATE")
    assert len(r_data["contributing_factors"]) > 0


def test_environmental_and_safety_api(client: TestClient):
    """Verify environmental assessments, safety state transitions, failure injection, and incidents."""
    bld_code = f"SAF-{uuid.uuid4().hex[:6].upper()}"
    bld_resp = client.post("/api/v1/buildings", json={"name": "Safety Core", "code": bld_code, "number_of_floors": 6})
    bld_id = bld_resp.json()["id"]

    # 1. Environmental State
    env_resp = client.get(f"/api/v1/environmental/{bld_id}/state")
    assert env_resp.status_code == 200
    assert env_resp.json()["status"] == "NORMAL"

    # 2. Environmental Hazard Assessment
    assess_payload = {
        "building_id": bld_id,
        "ambient_temperature_c": 32.0,
        "wind_speed_mps": 12.0,
        "seismic_pga_g": 0.15,
    }
    assess_resp = client.post(f"/api/v1/environmental/{bld_id}/assess", json=assess_payload)
    assert assess_resp.status_code == 200
    assert assess_resp.json()["seismic_risk"] == "MODERATE"

    # 3. Safety State Machine Transition (Escalate to WARNING)
    trans_payload = {
        "gravity_stability": "WARNING",
        "structural_risk": "MODERATE",
        "telemetry_reliability": 0.85,
        "power_state": "NOMINAL",
        "communication_state": "CONNECTED",
    }
    trans_resp = client.post(f"/api/v1/safety/{bld_id}/transition", json=trans_payload)
    assert trans_resp.status_code == 200
    assert trans_resp.json()["evaluation"]["to_state"] == "WARNING"

    # 4. Current State
    state_resp = client.get(f"/api/v1/safety/{bld_id}/state")
    assert state_resp.status_code == 200
    assert state_resp.json()["safety_state"] == "WARNING"

    # 5. Transitions Audit History
    hist_resp = client.get(f"/api/v1/safety/{bld_id}/transitions")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1

    # 6. Failure Injection Endpoint
    fi_payload = {
        "scenario": "sensor_failure",
        "initial_safety_state": "NORMAL",
    }
    fi_resp = client.post("/api/v1/safety/failure-injection", json=fi_payload)
    assert fi_resp.status_code == 200
    assert fi_resp.json()["detected"] is True
    assert fi_resp.json()["data_integrity_preserved"] is True

    # 7. Incident Lifecycle
    inc_payload = {
        "building_id": bld_id,
        "title": "Simulated Expansion Joint Deflection",
        "severity": "HIGH",
        "status": "OPEN",
        "initial_safety_state": "WARNING",
        "escalated_safety_state": "DEGRADED",
        "root_cause": "Differential displacement across core",
    }
    inc_resp = client.post("/api/v1/incidents", json=inc_payload)
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["id"]

    inc_list = client.get(f"/api/v1/incidents?building_id={bld_id}&status=OPEN")
    assert inc_list.status_code == 200
    assert len(inc_list.json()) >= 1

    patch_resp = client.patch(f"/api/v1/incidents/{inc_id}", json={"status": "RESOLVED"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "RESOLVED"

    # 8. Alert Dispatch
    alert_payload = {
        "building_id": bld_id,
        "severity": "HIGH",
        "event_type": "STRUCTURAL_ALERT",
        "message": "Elevated vibration detected on Level 4",
    }
    alt_resp = client.post("/api/v1/alerts/dispatch", json=alert_payload)
    assert alt_resp.status_code == 201

    alerts_list = client.get("/api/v1/alerts?limit=10")
    assert alerts_list.status_code == 200
    assert len(alerts_list.json()) >= 1

    # 9. Scenarios
    sc_payload = {
        "building_id": bld_id,
        "name": "Extreme Wind Shear Scenario",
        "scenario_type": "STRUCTURAL_OVERLOAD",
        "duration_seconds": 60.0,
        "severity": "HIGH",
        "expected_behavior": "Simulated structural deflection increases",
    }
    sc_resp = client.post("/api/v1/scenarios", json=sc_payload)
    assert sc_resp.status_code == 201
    sc_id = sc_resp.json()["id"]

    sc_get = client.get(f"/api/v1/scenarios/{sc_id}")
    assert sc_get.status_code == 200

    # 10. Report Generation
    rep_payload = {
        "building_id": bld_id,
        "report_type": "FACILITY_COMPREHENSIVE",
    }
    rep_resp = client.post("/api/v1/reports/generate", json=rep_payload)
    assert rep_resp.status_code == 201
    rep_id = rep_resp.json()["report_id"]

    rep_get = client.get(f"/api/v1/reports/{rep_id}")
    assert rep_get.status_code == 200
    assert len(rep_get.json()["sections"]) >= 2
