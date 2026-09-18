"""Unit tests for Phase 2 Domain Services."""

import uuid
from datetime import datetime, timezone
import pytest

from app.services.building_service import BuildingService
from app.services.telemetry_service import TelemetryService
from app.services.configuration_service import ConfigurationService
from app.services.simulation_scenario_service import SimulationScenarioService

from app.schemas.building import BuildingCreate, FloorCreate, ZoneCreate
from app.schemas.node import StructuralNodeCreate, AntiGravityNodeCreate, NodeTypeEnum, AntiGravityNodeStateEnum
from app.schemas.telemetry import TelemetrySourceCreate, TelemetryReadingCreate, SourceTypeEnum
from app.schemas.configuration import (
    GravityConfigCreate,
    SafetyThresholdCreate,
    SimulationScenarioCreate,
    ScenarioTypeEnum,
)


@pytest.mark.asyncio
async def test_building_service_validation(db_session):
    """Test business validation in BuildingService."""
    service = BuildingService(db_session)

    bld_data = BuildingCreate(name="Empire Complex", code="EMP-01", number_of_floors=10)
    building = await service.create_building(bld_data)
    assert building.id is not None

    # Duplicate code rejection
    with pytest.raises(ValueError, match="already exists"):
        await service.create_building(bld_data)

    # Add floor
    floor_data = FloorCreate(floor_number=1, name="Level 1")
    floor = await service.add_floor(building.id, floor_data)
    assert floor.floor_number == 1

    # Duplicate floor rejection
    with pytest.raises(ValueError, match="already exists"):
        await service.add_floor(building.id, floor_data)

    # Add zone
    zone_data = ZoneCreate(zone_code="Z-A", name="Zone Alpha", area_sqm=200.0)
    zone = await service.add_zone(floor.id, zone_data)
    assert zone.zone_code == "Z-A"

    # Negative area rejection via schema or service validation
    with pytest.raises((ValueError, Exception)):
        await service.add_zone(floor.id, ZoneCreate(zone_code="Z-B", name="Zone B", area_sqm=-10.0))

    # Anti-gravity node registration
    ag_data = AntiGravityNodeCreate(
        building_id=building.id,
        node_identifier="AG-TEST-01",
        name="Virtual Offset 1",
        operating_state=AntiGravityNodeStateEnum.SIMULATED,
    )
    ag_node = await service.register_antigravity_node(ag_data)
    assert ag_node.is_simulated == "true"


@pytest.mark.asyncio
async def test_telemetry_service_deduplication_and_quality(db_session):
    """Test TelemetryService deduplication and anomaly detection."""
    b_service = BuildingService(db_session)
    building = await b_service.create_building(
        BuildingCreate(name="Telemetry Lab", code="TLAB-01", number_of_floors=2)
    )

    t_service = TelemetryService(db_session)
    source = await t_service.register_source(
        TelemetrySourceCreate(
            source_identifier="SRC-TEST-01",
            name="Strain Sensor 1",
            source_type=SourceTypeEnum.STRAIN_GAUGE,
            building_id=building.id,
        )
    )

    now = datetime.now(timezone.utc)
    reading_data = TelemetryReadingCreate(
        source_id=source.id,
        building_id=building.id,
        metric="strain_microstrain",
        value=250.0,
        unit="um/m",
        timestamp=now,
        event_id="EVT-DEDUP-001",
    )

    # First ingestion -> VALID, no quality incident
    reading, quality_rec, _ = await t_service.ingest_reading(reading_data)
    assert reading.quality == "VALID"
    assert quality_rec is None

    # Duplicate ingestion with same event_id -> quality incident generated
    reading_dup, quality_rec_dup, _ = await t_service.ingest_reading(reading_data)
    assert quality_rec_dup is not None
    assert quality_rec_dup.flagged_quality == "DUPLICATE"


@pytest.mark.asyncio
async def test_configuration_service_safety_barrier(db_session):
    """Verify ConfigurationService enforces hardware actuation barrier."""
    b_service = BuildingService(db_session)
    building = await b_service.create_building(
        BuildingCreate(name="Safety Test Lab", code="SAFE-01", number_of_floors=3)
    )

    cfg_service = ConfigurationService(db_session)

    # Valid gravity config
    valid_gravity = GravityConfigCreate(
        building_id=building.id,
        target_gravity_offset_percentage=10.0,
    )
    saved_cfg = await cfg_service.update_gravity_config(valid_gravity)
    assert saved_cfg.hardware_actuation_enabled is False
    assert saved_cfg.in_silico_only is True

    # Valid safety threshold
    threshold_data = SafetyThresholdCreate(
        building_id=building.id,
        warning_threshold_percentage=75.0,
        interlock_trip_threshold_percentage=90.0,
    )
    saved_threshold = await cfg_service.set_safety_thresholds(threshold_data)
    assert saved_threshold.warning_threshold_percentage == 75.0


@pytest.mark.asyncio
async def test_simulation_scenario_service(db_session):
    """Verify SimulationScenarioService creation and activation."""
    b_service = BuildingService(db_session)
    building = await b_service.create_building(
        BuildingCreate(name="Scenario Lab", code="SCEN-01", number_of_floors=5)
    )

    scen_service = SimulationScenarioService(db_session)
    scen_data = SimulationScenarioCreate(
        building_id=building.id,
        name="Field Imbalance Test",
        scenario_type=ScenarioTypeEnum.FIELD_IMBALANCE,
        duration_seconds=120,
    )
    created = await scen_service.create_scenario(scen_data)
    assert created.id is not None
    assert created.is_active is False

    # Activate
    activated = await scen_service.activate_scenario(created.id, building.id)
    assert activated.is_active is True
