"""Comprehensive unit and integration tests for Firebase Authentication-Only integration.

Tests:
1. verify_firebase_id_token unit function handles empty/None inputs.
2. verify_firebase_id_token handles InvalidIdTokenError gracefully.
3. verify_firebase_id_token handles ExpiredIdTokenError gracefully.
4. verify_firebase_id_token decodes valid claims.
5. Missing Authorization header on protected endpoint returns HTTP 401.
6. Invalid Firebase token returns HTTP 401.
7. Expired Firebase token returns HTTP 401.
8. Valid Firebase token extracts Firebase UID and authenticates request.
9. GET /api/v1/auth/me returns authenticated Firebase user profile and permissions.
10. Public health endpoint (/health) remains accessible without token.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from firebase_admin import auth as firebase_auth

from app.main import app
from app.core.firebase_auth import verify_firebase_id_token, initialize_firebase_admin


# ============================================================================
# 1. Unit Tests: Firebase Token Verification Helper
# ============================================================================

def test_verify_firebase_id_token_empty_and_none():
    """Verify empty/None tokens return None without throwing exceptions."""
    assert verify_firebase_id_token("") is None
    assert verify_firebase_id_token(None) is None


def test_verify_firebase_id_token_invalid_exception():
    """Verify invalid token exception is caught and returns None."""
    with patch("firebase_admin.auth.verify_id_token", side_effect=firebase_auth.InvalidIdTokenError("Invalid token", None)):
        result = verify_firebase_id_token("invalid.mock.token")
        assert result is None


def test_verify_firebase_id_token_expired_exception():
    """Verify expired token exception is caught and returns None."""
    with patch("firebase_admin.auth.verify_id_token", side_effect=firebase_auth.ExpiredIdTokenError("Expired token", None)):
        result = verify_firebase_id_token("expired.mock.token")
        assert result is None


def test_verify_firebase_id_token_mock_valid():
    """Verify mocked successful Firebase verification returns claims dictionary."""
    mock_claims = {
        "uid": "FIREBASE-USER-123456",
        "email": "farmer.ramesh@risk2relief.org",
        "name": "Ramesh Patel",
        "auth_time": 1700000000,
        "iss": "https://securetoken.google.com/risk2relief",
        "aud": "risk2relief",
        "sub": "FIREBASE-USER-123456",
    }
    with patch("firebase_admin.auth.verify_id_token", return_value=mock_claims):
        claims = verify_firebase_id_token("valid.simulated.firebase.jwt")
        assert claims is not None
        assert claims["uid"] == "FIREBASE-USER-123456"
        assert claims["email"] == "farmer.ramesh@risk2relief.org"


# ============================================================================
# 2. Integration Tests: Protected Endpoints & Token Rejection
# ============================================================================

@pytest.mark.asyncio
async def test_missing_auth_header_rejected():
    """Verify protected /api/v1/auth/me rejects request without Authorization header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/auth/me")
        assert res.status_code == 401
        assert "not provided" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_firebase_token_rejected():
    """Verify protected endpoint rejects invalid Bearer token with HTTP 401."""
    with patch("firebase_admin.auth.verify_id_token", side_effect=firebase_auth.InvalidIdTokenError("Invalid token", None)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            headers = {"Authorization": "Bearer invalid_fabricated_token_xyz"}
            res = await ac.get("/api/v1/auth/me", headers=headers)
            assert res.status_code == 401
            assert "invalid" in res.json()["detail"].lower() or "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_expired_firebase_token_rejected():
    """Verify expired token exception is handled and returned as HTTP 401."""
    with patch("firebase_admin.auth.verify_id_token", side_effect=firebase_auth.ExpiredIdTokenError("Token expired", None)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            headers = {"Authorization": "Bearer expired_firebase_token"}
            res = await ac.get("/api/v1/auth/me", headers=headers)
            assert res.status_code == 401


@pytest.mark.asyncio
async def test_valid_firebase_token_authenticates_and_extracts_identity():
    """Verify valid Firebase ID token extracts UID, creates session context, and returns profile."""
    mock_claims = {
        "uid": "FB-RAMESH-PATEL-7788",
        "email": "ramesh.patel@wayanad.risk2relief",
        "name": "Ramesh Patel",
    }
    with patch("firebase_admin.auth.verify_id_token", return_value=mock_claims):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            headers = {"Authorization": "Bearer valid_firebase_token_123"}
            res = await ac.get("/api/v1/auth/me", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert "user" in data
            assert data["user"]["email"] == "ramesh.patel@wayanad.risk2relief"
            assert "permissions" in data


# ============================================================================
# 3. Integration Tests: Public Endpoints Remain Accessible
# ============================================================================

@pytest.mark.asyncio
async def test_public_health_endpoint_accessible_without_auth():
    """Verify public health endpoint /health remains open without requiring Firebase token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] in ("healthy", "degraded", "operational")
