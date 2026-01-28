"""Security utilities for authentication and authorization."""

import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from core.config import settings
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


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

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a new JWT access token."""

        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")


# NOTE: Convenience functions removed from here to eliminate duplication.
# Use PasswordHasher.hash() and PasswordHasher.verify() directly,
# or import from auth.py for backward compatibility (which will be deprecated in future).
