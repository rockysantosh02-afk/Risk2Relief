"""Phase 4: Simulation Runs and Safety Events persistence models.

Revision ID: 002_phase4_simulation
Revises: 001_phase2_domain
Create Date: 2026-09-18 17:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_phase4_simulation"
down_revision: Union[str, None] = "001_phase2_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. simulation_runs table
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", sa.Uuid(as_uuid=True), sa.ForeignKey("simulation_scenarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scenario_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="COMPLETED", nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("step_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("peak_risk_level", sa.String(32), server_default="LOW", nullable=False),
        sa.Column("peak_risk_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("final_risk_level", sa.String(32), server_default="LOW", nullable=False),
        sa.Column("final_risk_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("worst_stability_status", sa.String(32), server_default="NORMAL", nullable=False),
        sa.Column("summary_metrics_json", sa.JSON(), nullable=True),
        sa.Column("step_results_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_simulation_runs_building_id", "simulation_runs", ["building_id"])
    op.create_index("ix_simulation_runs_scenario_type", "simulation_runs", ["scenario_type"])
    op.create_index("ix_simulation_runs_peak_risk_level", "simulation_runs", ["peak_risk_level"])
    op.create_index("ix_simulation_runs_bld_risk", "simulation_runs", ["building_id", "peak_risk_level"])
    op.create_index("ix_simulation_runs_created", "simulation_runs", ["created_at"])

    # 2. safety_events table
    op.create_table(
        "safety_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("simulation_run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), server_default="WARNING", nullable=False),
        sa.Column("trigger_source", sa.String(64), server_default="SIMULATION_ENGINE", nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_safety_events_building_id", "safety_events", ["building_id"])
    op.create_index("ix_safety_events_event_type", "safety_events", ["event_type"])
    op.create_index("ix_safety_events_severity", "safety_events", ["severity"])
    op.create_index("ix_safety_events_detected_at", "safety_events", ["detected_at"])
    op.create_index("ix_safety_events_bld_sev", "safety_events", ["building_id", "severity"])


def downgrade() -> None:
    op.drop_table("safety_events")
    op.drop_table("simulation_runs")
