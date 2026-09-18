"""Configuration domain service enforcing system bounds and safety invariants."""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    BuildingConfiguration,
    GravityConfiguration,
    SafetyThresholdConfiguration,
    EnvironmentalConfiguration,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    BuildingConfigCreate,
    GravityConfigCreate,
    SafetyThresholdCreate,
    EnvironmentalConfigCreate,
)


class ConfigurationService:
    """Domain service managing building configurations and enforcing safety invariants."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ConfigurationRepository(session)

    async def update_building_config(self, data: BuildingConfigCreate) -> BuildingConfiguration:
        """Update or create active building configuration."""
        existing = await self.repo.get_active_building_config(data.building_id)
        next_version = (existing.version + 1) if existing else 1

        if existing:
            existing.is_active = False

        config = BuildingConfiguration(
            building_id=data.building_id,
            version=next_version,
            is_active=True,
            timezone=data.timezone,
            data_retention_days=data.data_retention_days,
            telemetry_buffer_size=data.telemetry_buffer_size,
            alarm_notification_channels=data.alarm_notification_channels or [],
            config_metadata=data.config_metadata or {},
        )
        return await self.repo.save_building_config(config)

    async def update_gravity_config(self, data: GravityConfigCreate) -> GravityConfiguration:
        """Update or create digital-twin in-silico gravity simulation configuration.

        HARD SYSTEM SAFETY BOUNDARY:
        Hardware actuation is permanently forbidden by system invariant.
        """
        if data.hardware_actuation_enabled is not False:
            raise ValueError(
                "CRITICAL SAFETY VIOLATION: Hardware actuation cannot be enabled in this digital-twin system."
            )
        if data.in_silico_only is not True:
            raise ValueError(
                "CRITICAL SAFETY VIOLATION: Simulation must strictly remain in-silico."
            )

        existing = await self.repo.get_active_gravity_config(data.building_id)
        next_version = (existing.version + 1) if existing else 1

        if existing:
            existing.is_active = False

        config = GravityConfiguration(
            building_id=data.building_id,
            version=next_version,
            is_active=True,
            simulation_model=data.simulation_model,
            target_gravity_offset_percentage=data.target_gravity_offset_percentage,
            max_compensation_kn=data.max_compensation_kn,
            field_distribution_algorithm=data.field_distribution_algorithm,
            in_silico_only=True,
            hardware_actuation_enabled=False,
            damping_factor=data.damping_factor,
            parameters_json=data.parameters_json or {},
        )
        return await self.repo.save_gravity_config(config)

    async def set_safety_thresholds(self, data: SafetyThresholdCreate) -> SafetyThresholdConfiguration:
        """Validate threshold ordering and persist engineering bounds."""
        if data.warning_threshold_percentage >= data.interlock_trip_threshold_percentage:
            raise ValueError(
                "warning_threshold_percentage must be strictly less than interlock_trip_threshold_percentage"
            )

        existing = await self.repo.get_safety_thresholds(data.building_id)
        if existing:
            existing.max_tensile_stress_mpa = data.max_tensile_stress_mpa
            existing.max_compressive_stress_mpa = data.max_compressive_stress_mpa
            existing.max_deflection_mm = data.max_deflection_mm
            existing.max_vibration_amplitude_g = data.max_vibration_amplitude_g
            existing.warning_threshold_percentage = data.warning_threshold_percentage
            existing.interlock_trip_threshold_percentage = data.interlock_trip_threshold_percentage
            existing.auto_trip_enabled = data.auto_trip_enabled
            existing.interlock_action = data.interlock_action
            return await self.repo.save_safety_thresholds(existing)

        config = SafetyThresholdConfiguration(
            building_id=data.building_id,
            max_tensile_stress_mpa=data.max_tensile_stress_mpa,
            max_compressive_stress_mpa=data.max_compressive_stress_mpa,
            max_deflection_mm=data.max_deflection_mm,
            max_vibration_amplitude_g=data.max_vibration_amplitude_g,
            warning_threshold_percentage=data.warning_threshold_percentage,
            interlock_trip_threshold_percentage=data.interlock_trip_threshold_percentage,
            auto_trip_enabled=data.auto_trip_enabled,
            interlock_action=data.interlock_action,
        )
        return await self.repo.save_safety_thresholds(config)

    async def set_environmental_config(
        self, data: EnvironmentalConfigCreate
    ) -> EnvironmentalConfiguration:
        """Validate thermal range and persist environmental bounds."""
        if data.ambient_temp_min_c >= data.ambient_temp_max_c:
            raise ValueError("ambient_temp_min_c must be less than ambient_temp_max_c")

        existing = await self.repo.get_environmental_config(data.building_id)
        if existing:
            existing.ambient_temp_min_c = data.ambient_temp_min_c
            existing.ambient_temp_max_c = data.ambient_temp_max_c
            existing.max_wind_speed_mps = data.max_wind_speed_mps
            existing.seismic_zone_code = data.seismic_zone_code
            existing.thermal_expansion_coefficient = data.thermal_expansion_coefficient
            return await self.repo.save_environmental_config(existing)

        config = EnvironmentalConfiguration(
            building_id=data.building_id,
            ambient_temp_min_c=data.ambient_temp_min_c,
            ambient_temp_max_c=data.ambient_temp_max_c,
            max_wind_speed_mps=data.max_wind_speed_mps,
            seismic_zone_code=data.seismic_zone_code,
            thermal_expansion_coefficient=data.thermal_expansion_coefficient,
        )
        return await self.repo.save_environmental_config(config)
