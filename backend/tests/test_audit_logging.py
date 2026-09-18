"""Integration and unit tests for Audit Logging, Compliance Trail, and Security Headers Middleware."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository
from app.models.audit import AuditLog


# ============================================================================
# 1. Unit & Repository Tests: Audit Event Recording & Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_audit_service_record_and_query(db_session):
    """Verify recording and querying audit trail records with filters."""
    service = AuditService(db_session)
    now = datetime.now(timezone.utc)

    # Record 3 events
    await service.record_event(
        actor="operator_alice",
        action="CONFIG_UPDATE",
        resource="gravity_config",
        result="SUCCESS",
        details={"offset_change": 5.0},
        client_ip="10.0.0.5",
        correlation_id="corr-111",
    )
    await service.record_event(
        actor="operator_bob",
        action="SIMULATION_RUN",
        resource="simulation_engine",
        result="SUCCESS",
        details={"scenario": "EMERGENCY_RECOVERY"},
        client_ip="10.0.0.6",
        correlation_id="corr-222",
    )
    await service.record_event(
        actor="operator_alice",
        action="SAFETY_OVERRIDE",
        resource="safety_state_machine",
        result="DENIED",
        details={"reason": "Insufficient permissions"},
        client_ip="10.0.0.5",
        correlation_id="corr-333",
    )

    # 1. Query all
    items, total = await service.query_logs(page=1, page_size=10)
    assert total >= 3

    # 2. Filter by actor
    alice_items, alice_total = await service.query_logs(actor="operator_alice", page=1, page_size=10)
    assert alice_total == 2
    for item in alice_items:
        assert item.actor == "operator_alice"

    # 3. Filter by action
    sim_items, sim_total = await service.query_logs(action="SIMULATION_RUN", page=1, page_size=10)
    assert sim_total == 1
    assert sim_items[0].actor == "operator_bob"

    # 4. Filter by result
    denied_items, denied_total = await service.query_logs(result="DENIED", page=1, page_size=10)
    assert denied_total == 1
    assert denied_items[0].action == "SAFETY_OVERRIDE"


@pytest.mark.asyncio
async def test_audit_pagination(db_session):
    """Verify audit log query pagination behaves correctly."""
    service = AuditService(db_session)

    # Record 15 distinct audit records
    for i in range(15):
        await service.record_event(
            actor=f"user_{i}",
            action="BATCH_ACTION",
            resource=f"resource_{i}",
            result="SUCCESS",
            details={"index": i},
        )

    # Fetch page 1 with page_size=5
    p1_items, total = await service.query_logs(action="BATCH_ACTION", page=1, page_size=5)
    assert total == 15
    assert len(p1_items) == 5

    # Fetch page 2 with page_size=5
    p2_items, _ = await service.query_logs(action="BATCH_ACTION", page=2, page_size=5)
    assert len(p2_items) == 5

    # Ensure page 1 and page 2 items are disjoint
    p1_actors = {item.actor for item in p1_items}
    p2_actors = {item.actor for item in p2_items}
    assert len(p1_actors.intersection(p2_actors)) == 0


# ============================================================================
# 2. API Endpoints: /api/v1/audit Access Control & Query
# ============================================================================

def test_api_audit_read_permission_enforcement(client: TestClient):
    """Verify audit endpoints require audit:read permission (e.g. SUPER_ADMIN, SYSTEM_ADMIN, ANALYST)."""
    # 1. Viewer role lacks audit:read -> 403 Forbidden
    viewer_resp = client.get(
        "/api/v1/audit",
        headers={"X-Test-Role": "VIEWER", "X-Test-User": "viewer_user"},
    )
    assert viewer_resp.status_code == 403

    # 2. Building Operator lacks audit:read -> 403 Forbidden
    bld_resp = client.get(
        "/api/v1/audit",
        headers={"X-Test-Role": "BUILDING_OPERATOR", "X-Test-User": "bld_operator"},
    )
    assert bld_resp.status_code == 403

    # 3. Analyst has audit:read -> 200 OK
    analyst_resp = client.get(
        "/api/v1/audit",
        headers={"X-Test-Role": "ANALYST", "X-Test-User": "analyst_user"},
    )
    assert analyst_resp.status_code == 200
    data = analyst_resp.json()
    assert "items" in data
    assert "total" in data

    # 4. Super Admin has audit:read -> 200 OK
    admin_resp = client.get(
        "/api/v1/audit",
        headers={"X-Test-Role": "SUPER_ADMIN", "X-Test-User": "super_user"},
    )
    assert admin_resp.status_code == 200


# ============================================================================
# 3. Security Hardening Middleware: Headers & Correlation ID
# ============================================================================

def test_security_headers_and_correlation_id_middleware(client: TestClient):
    """Verify security headers and correlation ID propagation in HTTP responses."""
    custom_corr_id = f"test-trace-{uuid.uuid4().hex[:8]}"

    # Send request with custom correlation ID
    resp = client.get(
        "/health",
        headers={"X-Correlation-ID": custom_corr_id},
    )
    assert resp.status_code == 200

    # Correlation ID must match request header
    assert resp.headers.get("X-Correlation-ID") == custom_corr_id

    # Security headers must be present and correctly set
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in resp.headers

    # Auto-generate correlation ID when omitted
    resp_auto = client.get("/health")
    assert resp_auto.status_code == 200
    auto_id = resp_auto.headers.get("X-Correlation-ID")
    assert auto_id is not None
    assert len(auto_id) > 8
