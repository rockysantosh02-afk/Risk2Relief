"""Risk2Relief FastAPI Application Entrypoint.

Provides root /health, /api/v1/health, digital-twin REST APIs, and real-time WebSocket channels.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.redis import close_redis_connection
from app.api.v1.router import api_v1_router
from app.websockets import ws_router, redis_bridge
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("risk2relief.api")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")
    await redis_bridge.start()
    yield
    logger.info("Shutting down Risk2Relief application...")
    await redis_bridge.stop()
    await close_redis_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Building-Management Digital-Twin Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 and WebSocket routers
app.include_router(api_v1_router)
app.include_router(ws_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Platform Root Health Check",
    description="Inspect overall platform status and external dependencies."
)
async def get_root_health() -> HealthResponse:
    """Root health check endpoint delegating to HealthService."""
    service = HealthService()
    return await service.get_system_health()


@app.get("/", tags=["General"])
async def root():
    """Service discovery metadata root."""
    return {
        "service": "risk2relief-api",
        "description": "Production-oriented full-stack building-management digital-twin platform",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
        "websockets": "/api/v1/ws",
    }
