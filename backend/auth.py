"""JWT authentication and password hashing - Backward compatibility layer.

DEPRECATED: This module is being phased out. Use core.dependencies for user dependencies.
Only password hashing and token functions remain here for backward compatibility.
"""

from datetime import timedelta
from typing import Optional

# Re-export for backward compatibility - will be removed in future version
from core.dependencies import (  # noqa: E402,F401
    get_current_admin_user,
    get_current_student_user,
    get_current_tutor_user,
    get_current_user,
    oauth2_scheme,
)
from core.security import PasswordHasher, TokenManager

# ============================================================================
# Password and Token Functions (kept for backward compatibility)
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return PasswordHasher.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt with 12 rounds."""
    return PasswordHasher.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    return TokenManager.create_access_token(data, expires_delta)
