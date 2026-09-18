"""Prometheus observability metrics collection and endpoint."""

import logging
from typing import Dict, Any
from starlette.responses import Response

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger("risk2relief.metrics")

if PROMETHEUS_AVAILABLE:
    # HTTP Metrics
    HTTP_REQUESTS_TOTAL = Counter(
        "risk2relief_http_requests_total",
        "Total HTTP requests handled by the platform",
        ["method", "endpoint", "status"],
    )
    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        "risk2relief_http_request_duration_seconds",
        "HTTP request latency distribution in seconds",
        ["method", "endpoint"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Real-Time & Telemetry Metrics
    ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
        "risk2relief_active_websocket_connections",
        "Current number of connected WebSocket digital-twin subscribers",
    )
    TELEMETRY_READINGS_INGESTED_TOTAL = Counter(
        "risk2relief_telemetry_readings_ingested_total",
        "Total telemetry sensor readings ingested into the digital-twin pipeline",
        ["status"],
    )

    # Physics & Safety Metrics
    SIMULATION_RUNS_TOTAL = Counter(
        "risk2relief_simulation_runs_total",
        "Total in-silico physics simulation runs executed",
        ["scenario", "status"],
    )
    SIMULATION_DURATION_SECONDS = Histogram(
        "risk2relief_simulation_duration_seconds",
        "Computation duration for gravity and structural simulation runs",
        buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
    )
    SAFETY_STATE_GAUGE = Gauge(
        "risk2relief_safety_state",
        "Current building safety state (0=NORMAL, 1=WARNING, 2=DEGRADED, 3=EMERGENCY, 4=RECOVERY, 5=MAINTENANCE)",
        ["building_id"],
    )
else:
    HTTP_REQUESTS_TOTAL = None
    HTTP_REQUEST_DURATION_SECONDS = None
    ACTIVE_WEBSOCKET_CONNECTIONS = None
    TELEMETRY_READINGS_INGESTED_TOTAL = None
    SIMULATION_RUNS_TOTAL = None
    SIMULATION_DURATION_SECONDS = None
    SAFETY_STATE_GAUGE = None


def record_http_request(method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
    """Record HTTP request metrics if Prometheus is available."""
    if PROMETHEUS_AVAILABLE and HTTP_REQUESTS_TOTAL:
        try:
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration_seconds)
        except Exception:
            pass


def set_safety_state_metric(building_id: str, state_str: str) -> None:
    """Update current safety state gauge for a facility."""
    if PROMETHEUS_AVAILABLE and SAFETY_STATE_GAUGE:
        state_map = {
            "NORMAL": 0,
            "WARNING": 1,
            "DEGRADED": 2,
            "EMERGENCY": 3,
            "RECOVERY": 4,
            "MAINTENANCE": 5,
        }
        val = state_map.get(state_str.upper(), 0)
        try:
            SAFETY_STATE_GAUGE.labels(building_id=str(building_id)).set(val)
        except Exception:
            pass


def get_metrics_response() -> Response:
    """Generate Prometheus exposition text format response."""
    if PROMETHEUS_AVAILABLE:
        content = generate_latest()
        return Response(content=content, media_type=CONTENT_TYPE_LATEST)
    return Response(
        content="# Prometheus metrics unavailable (prometheus-client not installed)\n",
        media_type="text/plain",
    )
