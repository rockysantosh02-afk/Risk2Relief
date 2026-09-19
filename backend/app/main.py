"""Risk2Relief FastAPI Application Entrypoint.

Provides root /health, /api/v1/health, Prometheus /metrics, digital-twin REST APIs,
and real-time WebSocket channels hardened with enterprise security and RBAC.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.redis import close_redis_connection
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    RequestSizeLimiterMiddleware,
    RateLimiterMiddleware,
    CorrelationIdMiddleware,
)
from app.core.metrics import get_metrics_response, record_http_request
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
    title="Risk2Relief — Autonomous Parametric Climate Insurance & Instant Settlement Engine",
    version=settings.APP_VERSION,
    description="Autonomous Parametric Climate Insurance & Instant Settlement Reliability Engine platform that validates multi-source climate telemetry, performs anomaly detection and consensus, evaluates deterministic parametric triggers, calculates relief compensation, and executes idempotent simulated settlement with a complete audit trail.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Custom metric tracking middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration,
    )
    return response

# Security Hardening Middlewares (applied in reverse execution order)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimiterMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 and WebSocket routers
app.include_router(api_v1_router)
app.include_router(ws_router)


@app.get("/metrics", tags=["Observability"], summary="Prometheus Metrics")
async def metrics() -> Response:
    """Prometheus exposition metrics endpoint for Grafana/Prometheus scraper."""
    return get_metrics_response()


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Platform Root Health Check",
    description="Inspect overall platform status and external dependencies.",
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
        "name": "Risk2Relief",
        "description": "Autonomous Parametric Climate Insurance & Instant Relief Settlement Engine",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "api_v1": "/api/v1",
        "websockets": "/api/v1/ws",
    }
