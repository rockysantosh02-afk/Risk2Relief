"""API v1 Aggregator Router.

Mounts all sub-domain endpoints adhering strictly to: Router -> Service -> Repository -> Database.
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.buildings import router as buildings_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.structural import router as structural_router
from app.api.v1.environmental import router as environmental_router
from app.api.v1.safety import router as safety_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.reports import router as reports_router
from app.api.v1.auth import router as auth_router
from app.api.v1.audit import router as audit_router
from app.api.v1.climate_api import router as climate_router
from app.api.v1.demo_api import router as demo_router
from app.api.v1.damage_api import router as damage_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount Risk2Relief Climate Insurance, Demo, and Damage Assessment Sub-routers
api_v1_router.include_router(climate_router)
api_v1_router.include_router(demo_router)
api_v1_router.include_router(damage_router)

# Mount foundational platform sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(buildings_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(structural_router)
api_v1_router.include_router(environmental_router)
api_v1_router.include_router(safety_router)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(reports_router)
