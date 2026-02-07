"""Security utilities for authentication and authorization."""

import logging
import secrets
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from typing import Literal

import bcrypt
from jose import JWTError, jwt

from core.config import settings
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Token types for differentiation
TokenType = Literal["access", "refresh"]


class PasswordHasher:
    """Handle password hashing and verification."""

    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt with 12 rounds."""
        logger.debug("Hashing password")
        # Bcrypt has a max password length of 72 bytes
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            logger.warning("Password exceeds 72 bytes, truncating")
            password = password_bytes[:72].decode("utf-8", errors="ignore")

        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        logger.debug("Password hashed successfully")
        return hashed

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        logger.debug("Verifying password")
        try:
            result = bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            logger.debug(f"Password verification result: {result}")
            return result
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False


class TokenManager:
    """Handle JWT token creation and validation."""

    # Refresh token expiry: 7 days (configurable via settings if needed)
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a new JWT access token."""

        to_encode = data.copy()

        if expires_delta:
            expire = utc_now() + expires_delta
        else:
            expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": utc_now(),
            "type": "access",
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a new JWT refresh token.

        Refresh tokens have:
        - Longer expiry (7 days default)
        - Unique jti (JWT ID) for revocation tracking
        - Type marker for validation
        """
        to_encode = data.copy()

        if expires_delta:
            expire = utc_now() + expires_delta
        else:
            expire = utc_now() + timedelta(days=TokenManager.REFRESH_TOKEN_EXPIRE_DAYS)

        # Add unique token ID for potential revocation tracking
        jti = secrets.token_urlsafe(32)

        to_encode.update({
            "exp": expire,
            "iat": utc_now(),
            "type": "refresh",
            "jti": jti,
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str, expected_type: TokenType | None = None) -> dict:
        """Decode and validate a JWT token.

        Args:
            token: The JWT token string to decode
            expected_type: If provided, validate token type matches ("access" or "refresh")

        Raises:
            AuthenticationError: If token is invalid or type doesn't match
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

            # Validate token type if specified
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type:
                    raise AuthenticationError(
                        f"Invalid token type: expected {expected_type}, got {token_type}"
                    )

            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    @staticmethod
    def get_token_expiry_timestamp(token: str) -> int | None:
        """Get the expiry timestamp from a token without full validation.

        Returns the exp claim as Unix timestamp, or None if token is invalid.
        Useful for frontend to know when to refresh.
        """
        try:
            # Decode without verification to get expiry
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False}
            )
            return payload.get("exp")
        except JWTError:
            return None


# NOTE: Convenience functions removed from here to eliminate duplication.
# Use PasswordHasher.hash() and PasswordHasher.verify() directly,
# or import from auth.py for backward compatibility (which will be deprecated in future).
