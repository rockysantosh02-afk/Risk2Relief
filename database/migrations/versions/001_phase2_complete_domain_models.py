"""Phase 2: Complete Domain Models for Building, Telemetry, and Configuration.

Revision ID: 001_phase2_domain
Revises: 
Create Date: 2026-09-18 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_phase2_domain"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. buildings table
    op.create_table(
        "buildings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), server_default="OPERATIONAL", nullable=False),
        sa.Column("number_of_floors", sa.Integer(), server_default="1", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_buildings_name", "buildings", ["name"])
    op.create_index("ix_buildings_code", "buildings", ["code"], unique=True)

    # 2. building_floors table
    op.create_table(
        "building_floors",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("elevation_meters", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", "floor_number", name="uq_building_floor_number"),
    )
    op.create_index("ix_building_floors_bld_id", "building_floors", ["building_id"])

    # 3. building_zones table
    op.create_table(
        "building_zones",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("floor_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("zone_type", sa.String(64), server_default="CORE", nullable=False),
        sa.Column("area_sqm", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("floor_id", "zone_code", name="uq_floor_zone_code"),
    )
    op.create_index("ix_building_zones_floor_id", "building_zones", ["floor_id"])

    # 4. structural_nodes table
    op.create_table(
        "structural_nodes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("floor_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_zones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_code", sa.String(64), nullable=False),
        sa.Column("node_type", sa.String(32), server_default="COLUMN", nullable=False),
        sa.Column("position_x", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("position_y", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("position_z", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("health_status", sa.String(32), server_default="OPTIMAL", nullable=False),
        sa.Column("baseline_parameters", sa.JSON(), nullable=True),
        sa.Column("node_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("zone_id", "node_code", name="uq_zone_structural_node_code"),
    )
    op.create_index("ix_structural_nodes_bld_id", "structural_nodes", ["building_id"])
    op.create_index("ix_structural_nodes_type_health", "structural_nodes", ["node_type", "health_status"])

    # 5. antigravity_nodes table (in-silico digital-twin nodes)
    op.create_table(
        "antigravity_nodes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("node_identifier", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("position_x", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("position_y", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("position_z", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("nominal_field_strength_kn", sa.Float(), server_default="500.0", nullable=False),
        sa.Column("operating_state", sa.String(32), server_default="SIMULATED", nullable=False),
        sa.Column("health_score", sa.Float(), server_default="100.0", nullable=False),
        sa.Column("efficiency", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_simulated", sa.String(8), server_default="true", nullable=False),
        sa.Column("simulation_parameters", sa.JSON(), nullable=True),
        sa.Column("configuration_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ag_nodes_identifier", "antigravity_nodes", ["node_identifier"], unique=True)
    op.create_index("ix_ag_nodes_bld_state", "antigravity_nodes", ["building_id", "operating_state"])

    # 6. telemetry_sources table
    op.create_table(
        "telemetry_sources",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_identifier", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("structural_node_id", sa.Uuid(as_uuid=True), sa.ForeignKey("structural_nodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), server_default="ONLINE", nullable=False),
        sa.Column("reliability_score", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("sampling_rate_hz", sa.Float(), server_default="10.0", nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_telemetry_sources_ident", "telemetry_sources", ["source_identifier"], unique=True)
    op.create_index("ix_telemetry_sources_bld_type", "telemetry_sources", ["building_id", "source_type"])

    # 7. telemetry_batches table
    op.create_table(
        "telemetry_batches",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("batch_identifier", sa.String(64), nullable=False),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("readings_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), server_default="INGESTED", nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processing_duration_ms", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_telemetry_batches_ident", "telemetry_batches", ["batch_identifier"], unique=True)

    # 8. telemetry_readings table
    op.create_table(
        "telemetry_readings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.Uuid(as_uuid=True), sa.ForeignKey("telemetry_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.Uuid(as_uuid=True), sa.ForeignKey("building_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("batch_id", sa.Uuid(as_uuid=True), sa.ForeignKey("telemetry_batches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("quality", sa.String(32), server_default="VALID", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "event_id", name="uq_source_event_id"),
    )
    op.create_index("ix_readings_bld_metric_ts", "telemetry_readings", ["building_id", "metric", "timestamp"])
    op.create_index("ix_readings_source_ts", "telemetry_readings", ["source_id", "timestamp"])
    op.create_index("ix_readings_quality_ts", "telemetry_readings", ["quality", "timestamp"])

    # 9. telemetry_quality_records table
    op.create_table(
        "telemetry_quality_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("reading_id", sa.Uuid(as_uuid=True), sa.ForeignKey("telemetry_readings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_id", sa.Uuid(as_uuid=True), sa.ForeignKey("telemetry_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flagged_quality", sa.String(32), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quality_records_source", "telemetry_quality_records", ["source_id"])

    # 10. building_configurations table
    op.create_table(
        "building_configurations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("timezone", sa.String(64), server_default="UTC", nullable=False),
        sa.Column("data_retention_days", sa.Integer(), server_default="90", nullable=False),
        sa.Column("telemetry_buffer_size", sa.Integer(), server_default="1000", nullable=False),
        sa.Column("alarm_notification_channels", sa.JSON(), nullable=True),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", "version", name="uq_building_config_version"),
    )

    # 11. gravity_configurations table
    op.create_table(
        "gravity_configurations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("simulation_model", sa.String(64), server_default="DISTRIBUTED_VECTOR_FIELD_V1", nullable=False),
        sa.Column("target_gravity_offset_percentage", sa.Float(), server_default="15.0", nullable=False),
        sa.Column("max_compensation_kn", sa.Float(), server_default="5000.0", nullable=False),
        sa.Column("field_distribution_algorithm", sa.String(64), server_default="OPTIMAL_SHEAR_BALANCING", nullable=False),
        sa.Column("in_silico_only", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("hardware_actuation_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("damping_factor", sa.Float(), server_default="0.05", nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", "version", name="uq_gravity_config_version"),
    )

    # 12. safety_threshold_configurations table
    op.create_table(
        "safety_threshold_configurations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("max_tensile_stress_mpa", sa.Float(), server_default="400.0", nullable=False),
        sa.Column("max_compressive_stress_mpa", sa.Float(), server_default="450.0", nullable=False),
        sa.Column("max_deflection_mm", sa.Float(), server_default="15.0", nullable=False),
        sa.Column("max_vibration_amplitude_g", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("warning_threshold_percentage", sa.Float(), server_default="75.0", nullable=False),
        sa.Column("interlock_trip_threshold_percentage", sa.Float(), server_default="90.0", nullable=False),
        sa.Column("auto_trip_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("interlock_action", sa.String(64), server_default="SAFE_CONTAINMENT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", name="uq_safety_threshold_building"),
    )

    # 13. environmental_configurations table
    op.create_table(
        "environmental_configurations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ambient_temp_min_c", sa.Float(), server_default="-20.0", nullable=False),
        sa.Column("ambient_temp_max_c", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("max_wind_speed_mps", sa.Float(), server_default="35.0", nullable=False),
        sa.Column("seismic_zone_code", sa.String(32), server_default="ZONE_IV", nullable=False),
        sa.Column("thermal_expansion_coefficient", sa.Float(), server_default="0.000012", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", name="uq_environmental_config_building"),
    )

    # 14. simulation_scenarios table
    op.create_table(
        "simulation_scenarios",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("building_id", sa.Uuid(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("scenario_type", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default="300", nullable=False),
        sa.Column("severity", sa.String(32), server_default="MEDIUM", nullable=False),
        sa.Column("injected_parameters", sa.JSON(), nullable=True),
        sa.Column("expected_behavior", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenarios_bld_active", "simulation_scenarios", ["building_id", "is_active"])


def downgrade() -> None:
    op.drop_table("simulation_scenarios")
    op.drop_table("environmental_configurations")
    op.drop_table("safety_threshold_configurations")
    op.drop_table("gravity_configurations")
    op.drop_table("building_configurations")
    op.drop_table("telemetry_quality_records")
    op.drop_table("telemetry_readings")
    op.drop_table("telemetry_batches")
    op.drop_table("telemetry_sources")
    op.drop_table("antigravity_nodes")
    op.drop_table("structural_nodes")
    op.drop_table("building_zones")
    op.drop_table("building_floors")
    op.drop_table("buildings")
