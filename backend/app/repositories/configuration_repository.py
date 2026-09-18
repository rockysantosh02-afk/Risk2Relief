"""Repository for Building, Gravity, Safety, and Environmental configurations."""

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import (
    BuildingConfiguration,
    GravityConfiguration,
    SafetyThresholdConfiguration,
    EnvironmentalConfiguration,
)


class ConfigurationRepository:
    """Data access repository for building operational and simulation configurations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Building Configuration
    async def get_active_building_config(self, building_id: uuid.UUID) -> Optional[BuildingConfiguration]:
        result = await self.session.execute(
            select(BuildingConfiguration).where(
                BuildingConfiguration.building_id == building_id,
                BuildingConfiguration.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def save_building_config(self, config: BuildingConfiguration) -> BuildingConfiguration:
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    # Gravity Configuration
    async def get_active_gravity_config(self, building_id: uuid.UUID) -> Optional[GravityConfiguration]:
        result = await self.session.execute(
            select(GravityConfiguration).where(
                GravityConfiguration.building_id == building_id,
                GravityConfiguration.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def save_gravity_config(self, config: GravityConfiguration) -> GravityConfiguration:
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    # Safety Threshold Configuration
    async def get_safety_thresholds(self, building_id: uuid.UUID) -> Optional[SafetyThresholdConfiguration]:
        result = await self.session.execute(
            select(SafetyThresholdConfiguration).where(
                SafetyThresholdConfiguration.building_id == building_id
            )
        )
        return result.scalar_one_or_none()

    async def save_safety_thresholds(
        self, config: SafetyThresholdConfiguration
    ) -> SafetyThresholdConfiguration:
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    # Environmental Configuration
    async def get_environmental_config(self, building_id: uuid.UUID) -> Optional[EnvironmentalConfiguration]:
        result = await self.session.execute(
            select(EnvironmentalConfiguration).where(
                EnvironmentalConfiguration.building_id == building_id
            )
        )
        return result.scalar_one_or_none()

    async def save_environmental_config(
        self, config: EnvironmentalConfiguration
    ) -> EnvironmentalConfiguration:
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config
