"""Firebase Admin SDK Authentication & Token Verification Module.

Used exclusively for verifying Firebase ID tokens and extracting user identities.
DO NOT use for Firestore, Storage, Analytics, or any other Firebase service.
"""

import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from app.core.config import get_settings

from jose import jwt, JWTError

logger = logging.getLogger("risk2relief.firebase_auth")
settings = get_settings()

_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase_admin() -> Optional[firebase_admin.App]:
    """Initialize Firebase Admin SDK with project credentials once."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    # Check if a default app is already initialized
    try:
        _firebase_app = firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized.")
        return _firebase_app
    except ValueError:
        pass

    try:
        project_id = getattr(settings, "FIREBASE_PROJECT_ID", "risk2relief") or "risk2relief"
        options = {"projectId": project_id}
        _firebase_app = firebase_admin.initialize_app(options=options)
        logger.info(f"Firebase Admin SDK initialized successfully for project '{project_id}'.")
        return _firebase_app
    except Exception as e:
        logger.warning(f"Firebase Admin SDK initialization deferred or failed: {str(e)}")
        return None


def verify_firebase_id_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Firebase ID token and return decoded claims.
    Returns None if the token is invalid, expired, or malformed.
    """
    if not token or not isinstance(token, str):
        return None

    # Fast-check: If token is a local HMAC-SHA256 token, immediately bypass Firebase verification
    try:
        unverified_header = jwt.get_unverified_header(token)
        if unverified_header.get("alg") == "HS256":
            return None
    except Exception:
        pass

    # Ensure app is initialized
    initialize_firebase_admin()

    try:
        # verify_id_token verifies signature, audience (projectId), issuer, and expiration
        decoded_claims = auth.verify_id_token(token, check_revoked=False)
        return decoded_claims
    except auth.InvalidIdTokenError:
        logger.warning("Firebase ID token verification failed: Invalid ID token.")
        return None
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase ID token verification failed: Token has expired.")
        return None
    except auth.RevokedIdTokenError:
        logger.warning("Firebase ID token verification failed: Token has been revoked.")
        return None
    except auth.CertificateFetchError:
        logger.warning("Firebase ID token verification failed: Could not fetch public key certificates.")
        return None
    except Exception as e:
        logger.warning(f"Firebase ID token verification error: {type(e).__name__}")
        return None
