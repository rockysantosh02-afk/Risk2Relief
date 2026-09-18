"""Simulation Domain Service orchestrating Digital-Twin Runs, Safety Events, and Persistence.

SAFETY INVARIANT:
This service executes purely in-silico mathematical digital-twin simulations.
Hardware actuation commands are strictly forbidden and non-existent.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import SimulationRun, SafetyEvent
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.building_repository import BuildingRepository
from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.physics.gravity_engine import (
    Coordinate3D,
    GravityNodeState,
    FieldEvaluationPoint,
)
from app.simulation.runner import (
    SimulationRunner,
    SimulationRunResult,
)
from app.schemas.simulation import SimulationExecuteRequest


class SimulationResultService:
    """Coordinates digital-twin physics execution, safety event logging, and persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sim_repo = SimulationRepository(session)
        self.building_repo = BuildingRepository(session)
        self.config_repo = ConfigurationRepository(session)
        self.telemetry_repo = TelemetryRepository(session)

    async def run_simulation(
        self,
        building_id: uuid.UUID,
        request: SimulationExecuteRequest,
    ) -> Tuple[SimulationRun, SimulationRunResult]:
        """Execute an in-silico physics & structural risk simulation run and persist results."""
        # 1. Fetch building hierarchy
        building = await self.building_repo.get_with_hierarchy(building_id)
        if not building:
            raise ValueError(f"Building {building_id} not found")

        # 2. Fetch configurations
        gravity_cfg = await self.config_repo.get_active_gravity_config(building_id)
        target_offset = (
            request.target_offset_percentage
            if request.target_offset_percentage is not None
            else (gravity_cfg.target_gravity_offset_percentage if gravity_cfg else 15.0)
        )

        # 3. Map AntiGravityNodes to computational GravityNodeState
        ag_nodes: List[GravityNodeState] = []
        for n in building.antigravity_nodes:
            ag_nodes.append(
                GravityNodeState(
                    node_id=str(n.id),
                    identifier=n.node_identifier,
                    position=Coordinate3D(x=n.position_x, y=n.position_y, z=n.position_z),
                    nominal_capacity_kn=n.nominal_field_strength_kn,
                    operating_state=n.operating_state,
                    health_score=n.health_score,
                    efficiency=n.efficiency,
                    influence_radius_m=20.0,
                )
            )

        # 4. Map StructuralNodes to member data
        members_data: List[Dict[str, Any]] = []
        eval_points: List[FieldEvaluationPoint] = []

        for sn in building.structural_nodes:
            members_data.append({
                "node_id": str(sn.id),
                "node_code": sn.node_code,
                "node_type": sn.node_type,
                "floor_number": 1,  # Default or zone floor
                "zone_code": sn.zone.zone_code if sn.zone else "CORE",
                "position_x": sn.position_x,
                "position_y": sn.position_y,
                "position_z": sn.position_z,
                "capacity_kn": 2500.0,
                "dead_load_kn": 800.0,
                "live_load_kn": 300.0,
                "cross_sectional_area_m2": 0.25,
                "elastic_modulus_gpa": 30.0,
            })
            eval_points.append(
                FieldEvaluationPoint(
                    point_id=str(sn.id),
                    position=Coordinate3D(x=sn.position_x, y=sn.position_y, z=sn.position_z),
                    zone_id=str(sn.zone_id),
                    reference_dead_load_kn=800.0,
                )
            )

        # Fallback evaluation point if no structural nodes present
        if not eval_points:
            eval_points.append(
                FieldEvaluationPoint(
                    point_id="EVAL-DEFAULT-01",
                    position=Coordinate3D(x=0.0, y=0.0, z=0.0),
                    reference_dead_load_kn=1000.0,
                )
            )

        # 5. Fetch latest telemetry for structural nodes
        telemetry_by_node: Dict[str, Dict[str, float]] = {}
        for sn in building.structural_nodes:
            # Query latest readings for this node
            readings = await self.telemetry_repo.get_source_readings_window(
                source_id=sn.id, window_seconds=600.0
            )
            node_tel: Dict[str, float] = {}
            for r in readings:
                if r.metric not in node_tel:
                    node_tel[r.metric] = r.value
            telemetry_by_node[str(sn.id)] = node_tel

        # 6. Execute deterministic simulation
        run_uuid = uuid.uuid4()
        start_time = datetime.now(timezone.utc)

        sim_result = SimulationRunner.execute_simulation(
            run_id=str(run_uuid),
            scenario_type=request.scenario_type,
            nodes=ag_nodes,
            members_data=members_data,
            evaluation_points=eval_points,
            telemetry_by_node=telemetry_by_node,
            target_offset_percentage=target_offset,
            step_count=request.step_count,
            step_duration_seconds=request.step_duration_seconds,
            building_id=str(building_id),
        )

        end_time = datetime.now(timezone.utc)

        # 7. Persist SimulationRun
        serialized_steps = [
            {
                "step_number": s.step_number,
                "timestamp_seconds": s.timestamp_seconds,
                "mean_offset_percentage": s.gravity_state.field_state.mean_offset_percentage,
                "field_uniformity": s.gravity_state.field_state.field_uniformity,
                "stability_status": s.stability_assessment.status.value,
                "peak_utilization": s.load_distribution.peak_utilization_ratio,
                "risk_score": s.risk_assessment.risk_score,
                "risk_level": s.risk_assessment.overall_risk_level.value,
            }
            for s in sim_result.step_results
        ]

        db_run = SimulationRun(
            id=run_uuid,
            building_id=building_id,
            scenario_type=str(request.scenario_type),
            status="COMPLETED",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=round((end_time - start_time).total_seconds(), 4),
            step_count=request.step_count,
            peak_risk_level=sim_result.peak_risk_level.value,
            peak_risk_score=sim_result.peak_risk_score,
            final_risk_level=sim_result.final_risk_level.value,
            final_risk_score=sim_result.final_risk_score,
            worst_stability_status=sim_result.worst_stability_status.value,
            summary_metrics_json=sim_result.summary_metrics,
            step_results_json=serialized_steps,
        )
        saved_run = await self.sim_repo.add_simulation_run(db_run)

        # 8. Persist SafetyEvents
        for ev in sim_result.safety_events:
            safety_ev = SafetyEvent(
                building_id=building_id,
                simulation_run_id=saved_run.id,
                event_type=ev.get("event_type", "SIMULATION_SAFETY_EVENT"),
                severity=ev.get("severity", "WARNING"),
                trigger_source=ev.get("trigger_source", "SIMULATION_ENGINE"),
                details_json=ev.get("details", {}),
                detected_at=end_time,
            )
            await self.sim_repo.add_safety_event(safety_ev)

        return saved_run, sim_result

    async def get_simulation_run(self, run_id: uuid.UUID) -> Optional[SimulationRun]:
        """Fetch simulation run detail with safety events."""
        return await self.sim_repo.get_simulation_run_detail(run_id)

    async def list_runs(
        self,
        building_id: Optional[uuid.UUID] = None,
        scenario_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SimulationRun]:
        """List simulation runs with optional filtering."""
        if building_id:
            return await self.sim_repo.list_simulation_runs(building_id, limit=limit, offset=offset)
        from sqlalchemy import select, desc
        stmt = select(SimulationRun)
        if scenario_type:
            stmt = stmt.where(SimulationRun.scenario_type == scenario_type.upper())
        stmt = stmt.order_by(desc(SimulationRun.created_at)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_run_details(self, run_id: uuid.UUID) -> Optional[SimulationRun]:
        """Fetch simulation run details with loaded safety events."""
        return await self.sim_repo.get_simulation_run_detail(run_id)

    async def list_simulation_runs(
        self, building_id: uuid.UUID, limit: int = 50
    ) -> Sequence[SimulationRun]:
        """List past simulation runs."""
        return await self.sim_repo.list_simulation_runs(building_id, limit=limit)

    async def list_safety_events(
        self, building_id: uuid.UUID, severity: Optional[str] = None, limit: int = 50
    ) -> Sequence[SafetyEvent]:
        """List safety events for a building."""
        return await self.sim_repo.list_safety_events(building_id, severity=severity, limit=limit)

    async def get_latest_risk_summary(self, building_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get latest risk evaluation summary for a building."""
        latest_run = await self.sim_repo.get_latest_simulation_run(building_id)
        if not latest_run:
            return None
        return {
            "run_id": str(latest_run.id),
            "scenario_type": latest_run.scenario_type,
            "peak_risk_level": latest_run.peak_risk_level,
            "peak_risk_score": latest_run.peak_risk_score,
            "final_risk_level": latest_run.final_risk_level,
            "worst_stability_status": latest_run.worst_stability_status,
            "created_at": latest_run.created_at.isoformat() if latest_run.created_at else None,
            "metrics": latest_run.summary_metrics_json or {},
        }
