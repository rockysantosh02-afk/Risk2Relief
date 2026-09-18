"""Integration tests for SafetyService, persistence, incident lifecycle, and state transitions."""

import uuid
from datetime import datetime, timezone
import pytest
from app.models.building import Building
from app.schemas.safety import (
    SafetyStateTransitionRequest,
    IncidentCreate,
    IncidentUpdate,
)
from app.services.safety_service import SafetyService
from app.safety.state_machine import SafetyState


@pytest.mark.asyncio
async def test_safety_service_evaluate_and_transition(db_session):
    """Verify safety state evaluation, audit record persistence, and automatic incident escalation."""
    # 1. Create building
    bld = Building(name="Safety Tower", code="SAF-01", number_of_floors=10)
    db_session.add(bld)
    await db_session.flush()

    service = SafetyService(db_session)

    # 2. Initial evaluation with nominal inputs
    req_nominal = SafetyStateTransitionRequest(
        gravity_stability="NORMAL",
        structural_risk="LOW",
        telemetry_reliability=1.0,
        power_state="NOMINAL",
        communication_state="CONNECTED",
    )
    eval1, inc1, alt1 = await service.evaluate_and_transition(bld.id, req_nominal)
    assert eval1.to_state == SafetyState.NORMAL
    assert inc1 is None
    assert alt1 is None

    # Current state should now be NORMAL
    curr_state = await service.safety_repo.get_current_safety_state(bld.id)
    assert curr_state == "NORMAL"

    # 3. Escalate to WARNING
    req_warn = SafetyStateTransitionRequest(structural_risk="MODERATE")
    eval2, inc2, alt2 = await service.evaluate_and_transition(bld.id, req_warn)
    assert eval2.from_state == SafetyState.NORMAL
    assert eval2.to_state == SafetyState.WARNING
    assert eval2.is_transition_triggered is True

    curr_state = await service.safety_repo.get_current_safety_state(bld.id)
    assert curr_state == "WARNING"

    # 4. Escalate to EMERGENCY (e.g. critical structural risk)
    req_emerg = SafetyStateTransitionRequest(structural_risk="CRITICAL")
    eval3, inc3, alt3 = await service.evaluate_and_transition(bld.id, req_emerg)
    assert eval3.to_state == SafetyState.EMERGENCY
    assert inc3 is not None
    assert inc3.severity == "CRITICAL"
    assert inc3.status == "OPEN"
    assert "EMERGENCY SIMULATION CONTAINMENT" in inc3.recommended_simulated_response
    assert alt3 is not None
    assert alt3.severity == "CRITICAL"

    # Check history
    history = await service.get_transition_history(bld.id, limit=10)
    assert len(history) >= 3


@pytest.mark.asyncio
async def test_safety_service_incident_crud_lifecycle(db_session):
    """Verify manual incident creation, lookup, list filtering, and status resolution."""
    bld = Building(name="Resilience Center", code="RES-01", number_of_floors=6)
    db_session.add(bld)
    await db_session.flush()

    service = SafetyService(db_session)

    # 1. Create Incident
    create_dto = IncidentCreate(
        building_id=bld.id,
        title="Simulated Shear Wall Deflection",
        severity="HIGH",
        status="OPEN",
        initial_safety_state="WARNING",
        escalated_safety_state="DEGRADED",
        root_cause="Lateral load drift detected on simulated Level 4 column",
        evidence_json={"drift_ratio": 0.015},
    )
    incident = await service.create_incident(create_dto)
    assert incident.id is not None
    assert incident.incident_code.startswith("INC-")
    assert incident.status == "OPEN"
    assert incident.severity == "HIGH"
    assert "HIGH PRIORITY CONTAINMENT" in incident.recommended_simulated_response

    # 2. Get Incident by ID
    fetched = await service.get_incident(incident.id)
    assert fetched is not None
    assert fetched.title == "Simulated Shear Wall Deflection"

    # 3. List Incidents
    open_incidents = await service.list_incidents(building_id=bld.id, status="OPEN")
    assert len(open_incidents) == 1
    assert open_incidents[0].id == incident.id

    # 4. Update Incident to RESOLVED
    update_dto = IncidentUpdate(
        status="RESOLVED",
        root_cause="Digital twin load re-balancing simulated successfully; strain normalized",
        resolved_at=datetime.now(timezone.utc),
    )
    updated = await service.update_incident(incident.id, update_dto)
    assert updated is not None
    assert updated.status == "RESOLVED"
    assert updated.resolved_at is not None

    # Check that status filter reflects change
    open_after = await service.list_incidents(building_id=bld.id, status="OPEN")
    assert len(open_after) == 0


def test_safety_service_failure_injection():
    """Verify synchronous failure injection execution via SafetyService wrapper."""
    # We pass None for session as failure injection is an in-memory simulation engine
    service = SafetyService(None)
    result = service.run_failure_injection("sensor_failure", "NORMAL")

    assert result.scenario == "sensor_failure"
    assert result.detected is True
    assert result.data_integrity_preserved is True
    assert result.recovery_successful is True
    assert "In-silico controlled resilience testing only" in result.safety_disclaimer
