"""Unit and integration tests for Authentication, JWT Lifecycle, Account Protection, and RBAC."""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from starlette.testclient import TestClient

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from app.core.rbac import ROLE_PERMISSIONS, check_permission
from app.schemas.auth import RoleEnum, UserCreate, LoginRequest, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.models.user import User


# ============================================================================
# 1. Unit Tests: Password Hashing & JWT Lifecycle
# ============================================================================

def test_password_hashing_and_verification():
    """Verify bcrypt hash generation and constant-time password verification."""
    password = "SuperSecretSecurePass123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_token_encoding_and_decoding():
    """Verify access and refresh token creation, payload signing, and claims validation."""
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "email": "operator@risk2relief.ai",
        "role": RoleEnum.SAFETY_OPERATOR.value,
    }
    access_token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    decoded = decode_token(access_token)

    assert decoded["sub"] == user_id
    assert decoded["email"] == "operator@risk2relief.ai"
    assert decoded["role"] == RoleEnum.SAFETY_OPERATOR.value
    assert decoded["type"] == "access"
    assert "jti" in decoded
    assert "exp" in decoded


def test_refresh_token_type():
    """Verify refresh token creates valid token with refresh type claim."""
    user_id = str(uuid.uuid4())
    payload = {"sub": user_id, "email": "admin@risk2relief.ai", "role": RoleEnum.SYSTEM_ADMIN.value}
    refresh_token = create_refresh_token(payload, expires_delta=timedelta(days=7))
    decoded = decode_token(refresh_token)

    assert decoded["sub"] == user_id
    assert decoded["type"] == "refresh"


def test_token_revocation_blacklist():
    """Verify revoked tokens are recorded and flagged as revoked."""
    jti = str(uuid.uuid4())
    assert is_token_revoked(jti) is False

    revoke_token(jti, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    assert is_token_revoked(jti) is True


# ============================================================================
# 2. RBAC Permissions Matrix
# ============================================================================

def test_rbac_matrix_coverage():
    """Verify all 7 roles have well-defined, least-privilege permission mappings."""
    all_roles = [
        RoleEnum.SUPER_ADMIN,
        RoleEnum.SYSTEM_ADMIN,
        RoleEnum.BUILDING_OPERATOR,
        RoleEnum.SAFETY_OPERATOR,
        RoleEnum.MAINTENANCE_OPERATOR,
        RoleEnum.ANALYST,
        RoleEnum.VIEWER,
    ]
    for role in all_roles:
        perms = ROLE_PERMISSIONS.get(role) or ROLE_PERMISSIONS.get(role.value)
        assert perms is not None
        assert isinstance(perms, set)

    # Super admin possesses all permissions
    assert check_permission(RoleEnum.SUPER_ADMIN.value, "users:manage") is True
    assert check_permission(RoleEnum.SUPER_ADMIN.value, "safety:manage") is True
    assert check_permission(RoleEnum.SUPER_ADMIN.value, "audit:read") is True

    # Viewer has read-only permissions
    assert check_permission(RoleEnum.VIEWER.value, "building:read") is True
    assert check_permission(RoleEnum.VIEWER.value, "telemetry:read") is True
    assert check_permission(RoleEnum.VIEWER.value, "safety:manage") is False
    assert check_permission(RoleEnum.VIEWER.value, "users:manage") is False
    assert check_permission(RoleEnum.VIEWER.value, "audit:read") is False

    # Safety operator has safety management but not user management
    assert check_permission(RoleEnum.SAFETY_OPERATOR.value, "safety:manage") is True
    assert check_permission(RoleEnum.SAFETY_OPERATOR.value, "alerts:manage") is True
    assert check_permission(RoleEnum.SAFETY_OPERATOR.value, "users:manage") is False


# ============================================================================
# 3. Integration Tests: AuthService & Account Lockout
# ============================================================================

@pytest.mark.asyncio
async def test_auth_service_register_and_authenticate(db_session):
    """Verify user registration and subsequent successful authentication."""
    auth_service = AuthService(db_session)
    user_data = UserCreate(
        username="analyst_test_user",
        email="analyst@risk2relief.ai",
        password="ValidPassword123#",
        full_name="Structural Analyst",
        role=RoleEnum.ANALYST,
    )
    user = await auth_service.register(user_data)
    assert user.id is not None
    assert user.email == "analyst@risk2relief.ai"
    assert user.role == RoleEnum.ANALYST.value
    assert user.is_locked is False

    tokens = await auth_service.authenticate(
        LoginRequest(username="analyst_test_user", password="ValidPassword123#"),
        client_ip="127.0.0.1",
    )
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_account_lockout_after_five_failed_attempts(db_session):
    """Verify account protection locks user out after 5 consecutive failed login attempts."""
    auth_service = AuthService(db_session)
    user_data = UserCreate(
        username="lockout_target_user",
        email="target@risk2relief.ai",
        password="SecureOriginalPassword123!",
        full_name="Lockout Target",
        role=RoleEnum.VIEWER,
    )
    await auth_service.register(user_data)

    # Attempt 5 invalid logins
    for i in range(5):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate(
                LoginRequest(username="lockout_target_user", password=f"WrongPasswordAttempt{i}!"),
                client_ip="192.168.1.100",
            )
        assert exc_info.value.status_code in (401, 403)

    # 6th attempt: Must be locked out (HTTP 403 Forbidden)
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate(
            LoginRequest(username="lockout_target_user", password="SecureOriginalPassword123!"),  # Even correct password is now rejected
            client_ip="192.168.1.100",
        )
    assert exc_info.value.status_code == 403
    assert "locked" in exc_info.value.detail.lower()


# ============================================================================
# 4. API Endpoints: /api/v1/auth Lifecycle & Logout
# ============================================================================

def test_api_auth_full_lifecycle(client: TestClient):
    """Test full HTTP auth flow: register, login, me, refresh, and logout."""
    username = f"usr_{uuid.uuid4().hex[:6]}"
    email = f"{username}@risk2relief.ai"
    password = "SuperStrongPassword123!"

    # 1. Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "API Test User",
            "role": "BUILDING_OPERATOR",
        },
    )
    assert reg_resp.status_code == 201
    user_info = reg_resp.json()
    assert user_info["email"] == email

    # 2. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 3. Authenticated /me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == email
    assert "building:read" in me_data["permissions"]

    # 4. Refresh Token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    new_access_token = new_tokens["access_token"]
    assert new_access_token is not None

    # 5. Logout (Revocation)
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "revoked"

    # 6. Verify revoked token is rejected
    post_logout_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert post_logout_resp.status_code == 401
