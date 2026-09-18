"""Authentication and RBAC Pydantic v2 schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleEnum(str, Enum):
    """Platform RBAC Roles."""
    SUPER_ADMIN = "SUPER_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    BUILDING_OPERATOR = "BUILDING_OPERATOR"
    SAFETY_OPERATOR = "SAFETY_OPERATOR"
    MAINTENANCE_OPERATOR = "MAINTENANCE_OPERATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class LoginRequest(BaseModel):
    """User login credential payload."""
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Token refresh payload."""
    refresh_token: str


class Token(BaseModel):
    """JWT response payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: str
    username: str
    role: str
    exp: int
    jti: Optional[str] = None


class UserCreate(BaseModel):
    """User registration/creation schema."""
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.VIEWER
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Public user response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    is_locked: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserProfileResponse(BaseModel):
    """Current authenticated user profile and effective permissions."""
    user: UserResponse
    permissions: List[str]
