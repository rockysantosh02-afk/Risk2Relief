"""Phase 5: Safety State Transitions and Incidents persistence models.

Revision ID: 003_phase5_safety
Revises: 002_phase4_simulation
Create Date: 2026-09-18 17:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_phase5_safety"
down_revision: Union[str, None] = "002_phase4_simulation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. incidents table
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("incident_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("severity", sa.String(32), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(32), server_default="OPEN", nullable=False),
        sa.Column("affected_zone_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("initial_safety_state", sa.String(32), server_default="NORMAL", nullable=False),
        sa.Column("escalated_safety_state", sa.String(32), server_default="WARNING", nullable=False),
        sa.Column("root_cause", sa.String(255), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("recommended_simulated_response", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_incidents_building_id", "incidents", ["building_id"])
    op.create_index("ix_incidents_incident_code", "incidents", ["incident_code"], unique=True)
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_bld_status", "incidents", ["building_id", "status"])
    op.create_index("ix_incidents_bld_severity", "incidents", ["building_id", "severity"])

    # 2. safety_state_transitions table
    op.create_table(
        "safety_state_transitions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.String(32), nullable=False),
        sa.Column("to_state", sa.String(32), nullable=False),
        sa.Column("trigger_reason", sa.String(255), nullable=False),
        sa.Column("inputs_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_valid_transition", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_state_transitions_building_id", "safety_state_transitions", ["building_id"])
    op.create_index("ix_state_transitions_from_state", "safety_state_transitions", ["from_state"])
    op.create_index("ix_state_transitions_to_state", "safety_state_transitions", ["to_state"])
    op.create_index("ix_state_transitions_transitioned_at", "safety_state_transitions", ["transitioned_at"])
    op.create_index("ix_state_transitions_bld_time", "safety_state_transitions", ["building_id", "transitioned_at"])


def downgrade() -> None:
    op.drop_table("safety_state_transitions")
    op.drop_table("incidents")
