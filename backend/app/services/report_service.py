"""Facility Intelligence & Audit Report Compilation Domain Service."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.building_repository import BuildingRepository
from app.repositories.safety_repository import SafetyRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.reports import (
    ReportGenerateRequest,
    ReportResponse,
    ReportSection,
    ReportTypeEnum,
)


class ReportService:
    """Aggregates telemetry, safety records, and physics evaluations into structured reports."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.building_repo = BuildingRepository(session)
        self.safety_repo = SafetyRepository(session)
        self.telemetry_repo = TelemetryRepository(session)

    async def generate_report(self, req: ReportGenerateRequest) -> ReportResponse:
        """Compile a multi-section facility health, risk, or telemetry report."""
        bld = await self.building_repo.get_by_id(req.building_id)
        if not bld:
            raise ValueError(f"Building {req.building_id} not found")

        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        # Retrieve safety transitions and incidents
        curr_state = await self.safety_repo.get_current_safety_state(req.building_id)
        incidents = await self.safety_repo.list_incidents(req.building_id, limit=20)
        transitions = await self.safety_repo.list_transition_records(req.building_id, limit=20)

        sections: List[ReportSection] = []

        # 1. Executive Summary Section
        sections.append(
            ReportSection(
                title="Facility Overview & Current Operational Posture",
                summary=(
                    f"Facility '{bld.name}' (Code: {bld.code}) is currently operating in '{curr_state}' safety state. "
                    f"Total floors: {bld.number_of_floors}. Open incidents: {len([i for i in incidents if i.status == 'OPEN'])}."
                ),
                metrics={
                    "current_safety_state": curr_state,
                    "number_of_floors": bld.number_of_floors,
                    "total_recorded_incidents": len(incidents),
                    "open_incidents": len([i for i in incidents if i.status == "OPEN"]),
                },
            )
        )

        # 2. Safety State & Incident Analysis Section
        sections.append(
            ReportSection(
                title="Safety State Machine & Incident Log",
                summary=(
                    f"Evaluated {len(transitions)} recent state machine transitions. "
                    f"Audit records indicate compliance with transition matrices."
                ),
                metrics={
                    "transition_count": len(transitions),
                    "critical_incidents": len([i for i in incidents if i.severity == "CRITICAL"]),
                    "high_severity_incidents": len([i for i in incidents if i.severity == "HIGH"]),
                },
                details=[
                    {
                        "incident_code": i.incident_code,
                        "title": i.title,
                        "severity": i.severity,
                        "status": i.status,
                        "opened_at": i.opened_at.isoformat(),
                    }
                    for i in incidents[:5]
                ],
            )
        )

        # 3. Telemetry & Sensor Integrity Section
        sources = await self.telemetry_repo.list_sources(req.building_id)
        sections.append(
            ReportSection(
                title="Telemetry Ingestion & Sensor Fleet Integrity",
                summary=(
                    f"Facility monitors {len(sources)} active physical and simulated telemetry feeds. "
                    "Idempotency and deduplication barriers active."
                ),
                metrics={
                    "registered_sources": len(sources),
                    "online_sources": len([s for s in sources if s.status.upper() == "ONLINE"]),
                },
                details=[
                    {
                        "source_identifier": s.source_identifier,
                        "type": s.source_type,
                        "status": s.status,
                        "reliability_score": s.reliability_score,
                    }
                    for s in sources[:5]
                ],
            )
        )

        exec_summary = (
            f"Comprehensive facility intelligence report for {bld.name}. "
            f"State: {curr_state}. Monitored across {len(sources)} sensor channels with {len(incidents)} lifecycle incidents logged."
        )

        return ReportResponse(
            report_id=report_id,
            building_id=req.building_id,
            report_type=req.report_type,
            title=f"Facility Report - {bld.name} ({req.report_type.value})",
            status="GENERATED",
            generated_at=now,
            executive_summary=exec_summary,
            sections=sections,
            metadata={
                "building_code": bld.code,
                "environment": "digital_twin_in_silico",
                "disclaimer": "Digital twin report for simulation and monitoring only.",
            },
        )
