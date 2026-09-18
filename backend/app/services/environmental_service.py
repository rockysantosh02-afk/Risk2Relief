"""Environmental Monitoring and Hazard Assessment Domain Service."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.building_repository import BuildingRepository
from app.schemas.environmental import (
    EnvironmentalStateResponse,
    EnvironmentalAssessRequest,
    EnvironmentalAssessResponse,
)


class EnvironmentalService:
    """Evaluates real-time and simulated environmental factors against facility safety envelopes."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_repo = ConfigurationRepository(session)
        self.building_repo = BuildingRepository(session)

    async def get_environmental_state(self, building_id: uuid.UUID) -> EnvironmentalStateResponse:
        """Fetch current or baseline environmental observations for building surroundings."""
        bld = await self.building_repo.get_by_id(building_id)
        if not bld:
            raise ValueError(f"Building {building_id} not found")

        env_cfg = await self.config_repo.get_environmental_config(building_id)
        temp = env_cfg.ambient_temperature_baseline_c if env_cfg else 21.5
        humidity = 48.0
        wind = 4.2
        seismic = 0.01
        aqi = 32.0

        return EnvironmentalStateResponse(
            building_id=building_id,
            ambient_temperature_c=temp,
            relative_humidity_percent=humidity,
            wind_speed_mps=wind,
            seismic_pga_g=seismic,
            air_quality_index=aqi,
            status="NORMAL",
            hazard_level="LOW",
        )

    async def assess_environmental_hazard(
        self, request: EnvironmentalAssessRequest
    ) -> EnvironmentalAssessResponse:
        """Evaluate ambient conditions, wind, and seismic ground acceleration against safety envelopes."""
        bld = await self.building_repo.get_by_id(request.building_id)
        if not bld:
            raise ValueError(f"Building {request.building_id} not found")

        env_cfg = await self.config_repo.get_environmental_config(request.building_id)
        max_temp = env_cfg.ambient_temperature_max_c if env_cfg else 45.0
        min_temp = env_cfg.ambient_temperature_min_c if env_cfg else -10.0

        seismic_pga = request.seismic_pga_g or 0.0
        wind_speed = request.wind_speed_mps or 0.0
        temp = request.ambient_temperature_c or 22.0

        seismic_risk = "LOW"
        if seismic_pga >= 0.40:
            seismic_risk = "CRITICAL"
        elif seismic_pga >= 0.20:
            seismic_risk = "HIGH"
        elif seismic_pga >= 0.08:
            seismic_risk = "MODERATE"

        wind_risk = "ELEVATED" if wind_speed > 25.0 else "LOW"
        thermal_risk = "ELEVATED" if (temp > max_temp or temp < min_temp) else "LOW"

        is_emergency = seismic_risk == "CRITICAL" or (seismic_risk == "HIGH" and wind_risk == "ELEVATED")

        if is_emergency:
            hazard_level = "CRITICAL"
        elif seismic_risk == "HIGH" or wind_risk == "ELEVATED":
            hazard_level = "HIGH"
        elif seismic_risk == "MODERATE" or thermal_risk == "ELEVATED":
            hazard_level = "MODERATE"
        else:
            hazard_level = "LOW"

        recommendations = []
        if is_emergency:
            recommendations.append("EMERGENCY: Initiate automated structural deflection telemetry sweeps at 100 Hz.")
            recommendations.append("Alert facility engineering of seismic ground acceleration exceeding design spectra.")
        elif hazard_level in ("HIGH", "MODERATE"):
            recommendations.append("Increase environmental sensor monitoring cadence.")
            recommendations.append("Calibrate thermal expansion compensators for extreme ambient temperature.")
        else:
            recommendations.append("All environmental parameters within nominal structural operating tolerances.")

        return EnvironmentalAssessResponse(
            building_id=request.building_id,
            hazard_level=hazard_level,
            seismic_risk=seismic_risk,
            thermal_stress_risk=thermal_risk,
            wind_load_risk=wind_risk,
            triggers_emergency=is_emergency,
            recommended_containment_actions=recommendations,
        )
