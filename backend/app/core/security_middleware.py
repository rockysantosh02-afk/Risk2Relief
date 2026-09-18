"""Security hardening, rate limiting, request size protection, and correlation middlewares."""

import time
import uuid
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger("risk2relief.middleware.security")

# Maximum permitted payload size: 10 Megabytes
MAX_PAYLOAD_BYTES = 10 * 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces enterprise security headers on all outbound HTTP responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response


class RequestSizeLimiterMiddleware(BaseHTTPMiddleware):
    """Guards against memory exhaustion and DoS by enforcing request body size limits."""

    def __init__(self, app, max_bytes: int = MAX_PAYLOAD_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > self.max_bytes:
                    logger.warning(f"Rejected oversized request: {length_int} bytes from {request.client.host if request.client else 'unknown'}")
                    return JSONResponse(
                        status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request payload exceeds maximum allowed size of 10MB"},
                    )
            except ValueError:
                pass
        return await call_next(request)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding-window in-memory rate limiter per client IP."""

    def __init__(self, app, requests_per_minute: int = 150):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        # Exclude internal health checks, metrics, and static documentation
        if path.startswith(("/health", "/metrics", "/docs", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - 60.0

        # Clean timestamps older than 60s
        self.client_records[client_ip] = [
            t for t in self.client_records[client_ip] if t > window_start
        ]

        if len(self.client_records[client_ip]) >= self.rpm:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} ({len(self.client_records[client_ip])} req/min)")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Maximum 150 requests per minute."},
                headers={"Retry-After": "60"},
            )

        self.client_records[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rpm - len(self.client_records[client_ip])))
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assigns and propagates correlation and request tracking IDs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        request.state.correlation_id = correlation_id
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        return response
