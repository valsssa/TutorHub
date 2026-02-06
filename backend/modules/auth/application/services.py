"""Auth service layer - business logic."""

import logging
import os
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from auth import create_access_token, get_password_hash, verify_password
from core.config import settings
from core.sanitization import sanitize_email
from core.security import TokenManager
from modules.auth.domain.entities import UserEntity
from modules.auth.infrastructure import UserRepositoryImpl

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.repository = UserRepositoryImpl(db)
        self.db = db

    def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "student",
        timezone: str = "UTC",
        currency: str = "USD",
        registration_ip: str | None = None,
        trial_restricted: bool = False,
    ) -> UserEntity:
        """
        Register a new user.

        Args:
            email: User email (will be sanitized and normalized)
            password: Plain password (will be hashed)
            role: User role (defaults to student)
            timezone: User timezone (defaults to UTC)
            currency: User currency (defaults to USD)
            registration_ip: IP address at registration (for fraud detection)
            trial_restricted: Whether to restrict free trial (fraud prevention)

        Returns:
            Created user entity

        Raises:
            HTTPException: If email already exists or validation fails
        """
        logger.debug(f"Registering user: {email}, role: {role}")

        # Sanitize and validate inputs
        email = sanitize_email(email)

        if not email:
            logger.warning("Invalid email format during registration")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        if not password or len(password) < 6 or len(password) > 128:
            logger.warning(f"Invalid password length during registration for: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be 6-128 characters",
            )

        if role not in ["student", "tutor", "admin"]:
            logger.warning(f"Invalid role during registration: {role} for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        # Check if email already exists
        if self.repository.exists_by_email(email):
            logger.warning(f"Registration attempt with existing email: {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Create user entity
        user_entity = UserEntity(
            id=None,
            email=email,
            hashed_password=get_password_hash(password),
            first_name=first_name.strip() if first_name else None,
            last_name=last_name.strip() if last_name else None,
            role=role,
            is_active=True,
            is_verified=False,
            timezone=timezone,
            currency=currency,
        )

        # Save to database with fraud detection fields
        created_user = self.repository.create(
            user_entity,
            registration_ip=registration_ip,
            trial_restricted=trial_restricted,
        )
        logger.info(f"User registered successfully: {created_user.email}, role: {created_user.role}")

        if trial_restricted:
            logger.warning(f"User {created_user.email} registered with trial_restricted=True")

        return created_user

    def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate user and generate tokens.

        Args:
            email: User email
            password: Plain password

        Returns:
            Dictionary with access_token, refresh_token, token_type, and expires_in

        Raises:
            HTTPException: If authentication fails
        """
        logger.debug(f"Authenticating user: {email}")

        # Sanitize email
        email = sanitize_email(email)

        # Find user
        user = self.repository.find_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Login attempt for inactive account: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        if not user.is_verified:
            logger.warning(f"Login attempt for unverified account: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email before logging in.",
            )

        # Create token data with role and password timestamp for security validation
        token_data = {
            "sub": user.email,
            "role": user.role,
        }
        # Include password_changed_at timestamp if available (for token invalidation)
        if user.password_changed_at:
            token_data["pwd_ts"] = user.password_changed_at.timestamp()

        # Create access token (short-lived)
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Create refresh token (long-lived)
        refresh_token = TokenManager.create_refresh_token(
            data=token_data,
        )

        logger.info(f"User authenticated successfully: {user.email}, role: {user.role}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an access token using a valid refresh token.

        Args:
            refresh_token: The refresh token to validate

        Returns:
            Dictionary with new access_token, token_type, and expires_in

        Raises:
            HTTPException: If refresh token is invalid or user no longer valid
        """
        from core.exceptions import AuthenticationError

        logger.debug("Attempting to refresh access token")

        try:
            # Decode and validate refresh token
            payload = TokenManager.decode_token(refresh_token, expected_type="refresh")
        except AuthenticationError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload.get("sub")
        if not email:
            logger.warning("Refresh token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Find user to verify they still exist and are active
        user = self.repository.find_by_email(email)

        if not user:
            logger.warning(f"Refresh token for non-existent user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Refresh token for inactive account: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        # Validate password timestamp - if password changed after token was issued,
        # the refresh token should be invalidated
        if user.password_changed_at:
            token_pwd_ts = payload.get("pwd_ts")
            if token_pwd_ts:
                if user.password_changed_at.timestamp() > token_pwd_ts:
                    logger.warning(f"Refresh token invalidated by password change for: {email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session invalidated by password change, please re-login",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            else:
                # Token issued before password tracking - invalidate if password has changed
                logger.warning(f"Legacy refresh token after password change for: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session invalidated by password change, please re-login",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Validate role hasn't changed
        token_role = payload.get("role")
        if token_role and token_role != user.role:
            logger.warning(f"Refresh token role mismatch for: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role changed, please re-login",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new token data with current user state
        token_data = {
            "sub": user.email,
            "role": user.role,
        }
        if user.password_changed_at:
            token_data["pwd_ts"] = user.password_changed_at.timestamp()

        # Create new access token
        new_access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        logger.info(f"Access token refreshed for user: {user.email}")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def get_user_by_email(self, email: str) -> UserEntity | None:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User entity or None
        """
        email = sanitize_email(email)
        return self.repository.find_by_email(email)

    def get_user_by_id(self, user_id: int) -> UserEntity | None:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User entity or None
        """
        return self.repository.find_by_id(user_id)

    def update_user_role(self, user_id: int, new_role: str, admin_user: UserEntity) -> UserEntity:
        """
        Update user role (admin only).

        Args:
            user_id: Target user ID
            new_role: New role to assign
            admin_user: Admin user performing the action

        Returns:
            Updated user entity

        Raises:
            HTTPException: If not authorized or validation fails
        """
        if not admin_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update user roles",
            )

        if new_role not in ["student", "tutor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        user = self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.role = new_role
        updated_user = self.repository.update(user)

        logger.info(f"User {user_id} role updated to {new_role} by admin {admin_user.email}")

        return updated_user

    def deactivate_user(self, user_id: int, admin_user: UserEntity) -> UserEntity:
        """
        Deactivate user account (admin only).

        Args:
            user_id: Target user ID
            admin_user: Admin user performing the action

        Returns:
            Updated user entity

        Raises:
            HTTPException: If not authorized or user not found
        """
        if not admin_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can deactivate users",
            )

        user = self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = False
        updated_user = self.repository.update(user)

        logger.info(f"User {user_id} deactivated by admin {admin_user.email}")

        return updated_user

    def verify_user_email(self, user_id: int) -> UserEntity:
        """
        Mark user email as verified.

        Args:
            user_id: User ID to verify

        Returns:
            Updated user entity

        Raises:
            HTTPException: If user not found
        """
        user = self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_verified = True
        updated_user = self.repository.update(user)

        logger.info(f"User {user_id} email verified")

        return updated_user
