"""Cryptographic utilities, JWT token lifecycle, and token revocation."""

import logging
import time
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set, Union
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger("risk2relief.security")
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration defaults
SECRET_KEY = getattr(settings, "SECRET_KEY", "risk2relief-super-secret-production-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# In-memory revocation registry with expiration timestamps: {jti: expiry_unix_time}
_REVOKED_TOKENS: Dict[str, float] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plaintext password."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed HMAC-SHA256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed HMAC-SHA256 JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token signature and expiration."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            logger.warning(f"Rejected revoked token with jti: {jti}")
            return None
        return payload
    except JWTError as exc:
        logger.debug(f"JWT decode failed: {exc}")
        return None


def revoke_token(
    jti: str,
    exp_timestamp: Optional[float] = None,
    expires_at: Optional[Union[float, datetime]] = None,
) -> None:
    """Revoke a token by its unique identifier (JTI)."""
    now = time.time()
    if expires_at is not None:
        expiry = expires_at.timestamp() if isinstance(expires_at, datetime) else float(expires_at)
    elif exp_timestamp is not None:
        expiry = float(exp_timestamp)
    else:
        expiry = now + 86400.0
    _REVOKED_TOKENS[jti] = expiry
    _cleanup_expired_revocations()
    logger.info(f"Token revoked: {jti}")


def is_token_revoked(jti: str) -> bool:
    """Check if token JTI is in the revocation blacklist."""
    now = time.time()
    if jti in _REVOKED_TOKENS:
        if _REVOKED_TOKENS[jti] > now:
            return True
        else:
            del _REVOKED_TOKENS[jti]
    return False


def _cleanup_expired_revocations() -> None:
    """Housekeeping to purge naturally expired tokens from the blacklist."""
    now = time.time()
    expired_jtis = [jti for jti, exp in _REVOKED_TOKENS.items() if exp <= now]
    for jti in expired_jtis:
        _REVOKED_TOKENS.pop(jti, None)
