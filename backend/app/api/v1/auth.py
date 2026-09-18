"""Authentication and User Management REST API endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import (
    get_current_user,
    require_permission,
    PERM_USERS_MANAGE,
    security_scheme,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserResponse,
    UserProfileResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.auth_service import AuthService

logger = logging.getLogger("risk2relief.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate User",
    description="Validates credentials and issues HMAC-SHA256 JWT access and refresh tokens.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate credentials and generate JWT tokens."""
    client_ip = request.client.host if request.client else None
    service = AuthService(session)
    return await service.authenticate(payload, client_ip=client_ip)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Access Token",
    description="Exchanges a valid refresh token for a newly minted access token.",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> Token:
    """Generate fresh access token."""
    service = AuthService(session)
    return await service.refresh_access_token(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Revokes current access token and invalidates active session.",
)
async def logout(
    request: Request,
    credentials=Depends(security_scheme),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Log out and revoke JWT access token."""
    token_str = credentials.credentials if credentials else ""
    client_ip = request.client.host if request.client else None
    service = AuthService(session)
    await service.logout(token_str, actor=current_user.username, client_ip=client_ip)
    return {"message": "Logged out successfully", "status": "revoked"}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Public or operator onboarding endpoint for new user accounts.",
)
async def register_user_endpoint(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user."""
    service = AuthService(session)
    return await service.create_user(payload, actor="self_registration")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Current User Profile",
    description="Returns current authenticated user details and active RBAC permissions.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve profile of authenticated caller."""
    service = AuthService(session)
    return await service.get_profile(current_user)


@router.get(
    "/users",
    response_model=PaginatedResponse[UserResponse],
    summary="List Users",
    description="Paginated list of platform users (requires users:manage permission).",
)
async def list_users(
    page: int = 1,
    page_size: int = 50,
    role: Optional[str] = None,
    current_user: User = Depends(require_permission(PERM_USERS_MANAGE)),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    """Retrieve platform user list."""
    service = AuthService(session)
    items, total = await service.list_users(page, page_size, role)
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Registers a new platform user with specified role (requires users:manage permission).",
)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission(PERM_USERS_MANAGE)),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new platform user."""
    service = AuthService(session)
    return await service.create_user(payload, actor=current_user.username)
