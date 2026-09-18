"""Unit tests for Configuration domain models and safety boundary invariants."""

import uuid
import pytest
from pydantic import ValidationError

from app.models.building import Building
from app.models.configuration import (
    BuildingConfiguration,
    GravityConfiguration,
    SafetyThresholdConfiguration,
    EnvironmentalConfiguration,
)
from app.schemas.configuration import (
    GravityConfigBase,
    SafetyThresholdBase,
    EnvironmentalConfigBase,
)


@pytest.mark.asyncio
async def test_configuration_persistence(db_session):
    """Test saving and retrieving building operational and gravity configuration."""
    building = Building(name="Config Center", code="BLD-CFG-01")
    db_session.add(building)
    await db_session.flush()

    bld_cfg = BuildingConfiguration(
        building_id=building.id,
        version=1,
        is_active=True,
        timezone="America/New_York",
        data_retention_days=180,
    )
    db_session.add(bld_cfg)

    grav_cfg = GravityConfiguration(
        building_id=building.id,
        version=1,
        is_active=True,
        target_gravity_offset_percentage=20.0,
        in_silico_only=True,
        hardware_actuation_enabled=False,
    )
    db_session.add(grav_cfg)
    await db_session.flush()

    assert bld_cfg.id is not None
    assert grav_cfg.in_silico_only is True
    assert grav_cfg.hardware_actuation_enabled is False


def test_gravity_config_safety_invariant_rejection():
    """Verify that attempting to enable hardware actuation in GravityConfig raises a ValidationError."""
    # Attempt to enable hardware actuation
    with pytest.raises(ValidationError) as excinfo:
        GravityConfigBase(
            target_gravity_offset_percentage=15.0,
            hardware_actuation_enabled=True,  # VIOLATION
        )
    assert "Safety boundary violated" in str(excinfo.value)


def test_safety_threshold_validation_order():
    """Verify warning threshold cannot be greater than or equal to interlock trip threshold."""
    # Valid
    valid_threshold = SafetyThresholdBase(
        warning_threshold_percentage=70.0,
        interlock_trip_threshold_percentage=85.0,
    )
    assert valid_threshold.warning_threshold_percentage < valid_threshold.interlock_trip_threshold_percentage

    # Invalid: warning >= trip
    with pytest.raises(ValidationError) as excinfo:
        SafetyThresholdBase(
            warning_threshold_percentage=92.0,
            interlock_trip_threshold_percentage=90.0,
        )
    assert "warning_threshold_percentage must be strictly less" in str(excinfo.value)


def test_environmental_config_temperature_bounds():
    """Verify min temperature must be less than max temperature."""
    with pytest.raises(ValidationError) as excinfo:
        EnvironmentalConfigBase(
            ambient_temp_min_c=45.0,
            ambient_temp_max_c=30.0,
        )
    assert "ambient_temp_min_c must be less than ambient_temp_max_c" in str(excinfo.value)
