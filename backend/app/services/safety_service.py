"""Safety, Resilience, Incident & Anomaly Domain Service."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.safety import Incident, SafetyStateTransitionRecord
from app.repositories.safety_repository import SafetyRepository
from app.repositories.building_repository import BuildingRepository
from app.safety.state_machine import (
    SafetyStateMachine,
    SafetyState,
    SafetyInputs,
    SafetyStateEvaluation,
)
from app.safety.incidents import IncidentService, AlertService, AlertNotification
from app.safety.failure_injection import FailureInjectionEngine, FailureInjectionResult, FailureMode
from app.schemas.safety import (
    SafetyStateTransitionRequest,
    IncidentCreate,
    IncidentUpdate,
)


class SafetyService:
    """Domain service managing state transitions, incidents, alerts, and resilience injections."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.safety_repo = SafetyRepository(session)
        self.building_repo = BuildingRepository(session)
        self.alert_service = AlertService()

    async def evaluate_and_transition(
        self,
        building_id: uuid.UUID,
        request: SafetyStateTransitionRequest,
    ) -> Tuple[SafetyStateEvaluation, Optional[Incident], Optional[AlertNotification]]:
        """Evaluate multi-modal inputs, execute deterministic state transition, and log audit trail."""
        building = await self.building_repo.get_by_id(building_id)
        if not building:
            raise ValueError(f"Building {building_id} not found")

        # 1. Fetch current state
        curr_state_str = await self.safety_repo.get_current_safety_state(building_id)
        curr_state = SafetyState(curr_state_str)

        # 2. Package inputs
        inputs = SafetyInputs(
            gravity_stability=request.gravity_stability,
            structural_risk=request.structural_risk,
            telemetry_reliability=request.telemetry_reliability,
            power_state=request.power_state,
            communication_state=request.communication_state,
            environmental_conditions=request.environmental_conditions or {},
            is_maintenance_mode=request.is_maintenance_mode,
        )

        # 3. Evaluate state machine
        evaluation = SafetyStateMachine.evaluate_target_state(curr_state, inputs)

        incident: Optional[Incident] = None
        alert: Optional[AlertNotification] = None

        # 4. Log transition if triggered or if first evaluation
        if evaluation.is_transition_triggered or curr_state_str == "NORMAL":
            rec = SafetyStateTransitionRecord(
                building_id=building_id,
                from_state=evaluation.from_state.value,
                to_state=evaluation.to_state.value,
                trigger_reason=evaluation.trigger_reason,
                inputs_snapshot_json=inputs.to_dict(),
                transitioned_at=evaluation.timestamp,
                is_valid_transition=evaluation.is_valid_transition,
            )
            await self.safety_repo.add_transition_record(rec)

            # Auto-escalate incident on critical state transitions
            if evaluation.to_state in (SafetyState.EMERGENCY, SafetyState.DEGRADED):
                inc_severity = "CRITICAL" if evaluation.to_state == SafetyState.EMERGENCY else "HIGH"
                inc_code = f"INC-{uuid.uuid4().hex[:6].upper()}"
                recommendation = IncidentService.generate_containment_recommendation(
                    severity=inc_severity,
                    escalated_state=evaluation.to_state.value,
                    cause=evaluation.trigger_reason,
                )

                db_incident = Incident(
                    building_id=building_id,
                    incident_code=inc_code,
                    title=f"Safety State Transition to {evaluation.to_state.value}",
                    severity=inc_severity,
                    status="OPEN",
                    initial_safety_state=evaluation.from_state.value,
                    escalated_safety_state=evaluation.to_state.value,
                    root_cause=evaluation.trigger_reason,
                    evidence_json=evaluation.evidence,
                    recommended_simulated_response=recommendation,
                    opened_at=datetime.now(timezone.utc),
                )
                incident = await self.safety_repo.add_incident(db_incident)

                # Dispatch alert notification
                alert = self.alert_service.dispatch_alert(
                    building_id=str(building_id),
                    severity=inc_severity,
                    event_type=f"STATE_TRANSITION_{evaluation.to_state.value}",
                    message=f"Building transitioned from {evaluation.from_state.value} to {evaluation.to_state.value}: {evaluation.trigger_reason}",
                    state_transition=f"{evaluation.from_state.value} -> {evaluation.to_state.value}",
                    recommended_simulated_action=recommendation,
                )

        return evaluation, incident, alert

    async def create_incident(self, data: IncidentCreate) -> Incident:
        """Create a manual or programmatic safety incident."""
        inc_code = data.incident_code or f"INC-{uuid.uuid4().hex[:6].upper()}"
        recommendation = data.recommended_simulated_response or IncidentService.generate_containment_recommendation(
            severity=data.severity,
            escalated_state=data.escalated_safety_state,
            cause=data.root_cause,
        )
        incident = Incident(
            building_id=data.building_id,
            incident_code=inc_code,
            title=data.title,
            severity=data.severity.upper(),
            status=data.status.upper(),
            affected_zone_id=data.affected_zone_id,
            initial_safety_state=data.initial_safety_state.upper(),
            escalated_safety_state=data.escalated_safety_state.upper(),
            root_cause=data.root_cause,
            evidence_json=data.evidence_json or {},
            recommended_simulated_response=recommendation,
            opened_at=datetime.now(timezone.utc),
        )
        return await self.safety_repo.add_incident(incident)

    async def get_incident(self, incident_id: uuid.UUID) -> Optional[Incident]:
        """Fetch incident by unique identifier."""
        return await self.safety_repo.get_by_id(incident_id)

    async def update_incident(self, incident_id: uuid.UUID, data: IncidentUpdate) -> Optional[Incident]:
        """Update incident status, cause, or resolution."""
        incident = await self.safety_repo.get_by_id(incident_id)
        if not incident:
            return None

        if data.status:
            incident.status = data.status.upper()
            if incident.status in ("RESOLVED", "CLOSED") and not incident.resolved_at:
                incident.resolved_at = datetime.now(timezone.utc)
        if data.root_cause:
            incident.root_cause = data.root_cause
        if data.recommended_simulated_response:
            incident.recommended_simulated_response = data.recommended_simulated_response

        await self.session.flush()
        await self.session.refresh(incident)
        return incident

    async def list_incidents(
        self,
        building_id: uuid.UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[Incident]:
        """List past or active incidents."""
        return await self.safety_repo.list_incidents(
            building_id=building_id, status=status, severity=severity, limit=limit
        )

    async def list_transitions(
        self, building_id: uuid.UUID, limit: int = 50
    ) -> Sequence[SafetyStateTransitionRecord]:
        """List state transition audit history."""
        return await self.safety_repo.list_transition_records(building_id=building_id, limit=limit)

    async def get_transition_history(
        self, building_id: uuid.UUID, limit: int = 50
    ) -> Sequence[SafetyStateTransitionRecord]:
        """Alias for list_transitions."""
        return await self.list_transitions(building_id=building_id, limit=limit)

    @staticmethod
    def run_failure_injection_test(
        scenario: str, initial_state: str = "NORMAL"
    ) -> FailureInjectionResult:
        """Execute in-silico failure injection scenario test."""
        mode = FailureMode(scenario.lower())
        init_st = SafetyState(initial_state.upper())
        return FailureInjectionEngine.execute_failure_scenario(mode, initial_state=init_st)

    @classmethod
    def run_failure_injection(
        cls, scenario: str, initial_state: str = "NORMAL"
    ) -> FailureInjectionResult:
        """Alias for run_failure_injection_test."""
        return cls.run_failure_injection_test(scenario, initial_state)

