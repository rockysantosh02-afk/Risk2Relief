"""Authentication and User management service."""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core.rbac import get_permissions_for_role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.schemas.auth import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
    UserProfileResponse,
    RoleEnum,
)

logger = logging.getLogger("risk2relief.auth")
MAX_FAILED_ATTEMPTS = 5


class AuthService:
    """Handles user authentication, JWT session lifecycle, account locking, and registration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_service = AuditService(session)

    async def authenticate(
        self, login_data: LoginRequest, client_ip: Optional[str] = None
    ) -> Token:
        """Verify user credentials with lockout protection and issue access/refresh tokens."""
        user = await self.user_repo.get_by_username(login_data.username)
        if not user:
            logger.warning(f"Login failed: username '{login_data.username}' not found")
            await self.audit_service.record_event(
                actor=login_data.username,
                action="USER_LOGIN",
                resource="auth",
                result="FAILURE",
                details={"reason": "User not found"},
                client_ip=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if user.is_locked:
            logger.warning(f"Login attempt on locked account: '{user.username}'")
            await self.audit_service.record_event(
                actor=user.username,
                action="USER_LOGIN",
                resource="auth",
                result="LOCKED",
                details={"reason": "Account locked"},
                client_ip=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to excessive failed attempts. Contact system administrator.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        if not verify_password(login_data.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                logger.warning(f"Account locked due to failed attempts: '{user.username}'")
            await self.user_repo.update(user)
            await self.audit_service.record_event(
                actor=user.username,
                action="USER_LOGIN",
                resource="auth",
                result="FAILURE",
                details={"failed_attempts": user.failed_login_attempts, "locked": user.is_locked},
                client_ip=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Successful authentication
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)

        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        await self.audit_service.record_event(
            actor=user.username,
            action="USER_LOGIN",
            resource="auth",
            result="SUCCESS",
            details={"role": user.role},
            client_ip=client_ip,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Issue fresh access token using a valid refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        username = payload.get("username")
        user = await self.user_repo.get_by_username(username)
        if not user or not user.is_active or user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account invalid or locked",
            )

        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        }
        new_access_token = create_access_token(token_payload)
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
        )

    async def logout(self, token_str: str, actor: str, client_ip: Optional[str] = None) -> None:
        """Revoke the current access token."""
        payload = decode_token(token_str)
        if payload and payload.get("jti"):
            jti = payload["jti"]
            exp = payload.get("exp")
            revoke_token(jti, exp)

        await self.audit_service.record_event(
            actor=actor,
            action="USER_LOGOUT",
            resource="auth",
            result="SUCCESS",
            client_ip=client_ip,
        )

    async def create_user(self, user_in: UserCreate, actor: str = "system") -> UserResponse:
        """Register a new user with hashed password."""
        return await self._create_user_internal(user_in, actor)

    register = create_user

    async def _create_user_internal(self, user_in: UserCreate, actor: str = "system") -> UserResponse:
        existing_username = await self.user_repo.get_by_username(user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_in.username}' is already taken",
            )

        existing_email = await self.user_repo.get_by_email(user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{user_in.email}' is already registered",
            )

        hashed = get_password_hash(user_in.password)
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed,
            role=user_in.role.value,
            full_name=user_in.full_name,
            is_active=True,
            is_locked=False,
        )
        created = await self.user_repo.create(new_user)

        await self.audit_service.record_event(
            actor=actor,
            action="USER_CREATE",
            resource=f"user:{created.username}",
            result="SUCCESS",
            details={"role": created.role, "email": created.email},
        )
        return UserResponse.model_validate(created)

    async def get_profile(self, user: User) -> UserProfileResponse:
        """Retrieve user profile with assigned RBAC permissions."""
        permissions = get_permissions_for_role(user.role)
        return UserProfileResponse(
            user=UserResponse.model_validate(user),
            permissions=permissions,
        )

    async def list_users(
        self, page: int = 1, page_size: int = 50, role: Optional[str] = None
    ) -> Tuple[List[UserResponse], int]:
        """List platform users."""
        users, total = await self.user_repo.list_users(page, page_size, role)
        return [UserResponse.model_validate(u) for u in users], total
