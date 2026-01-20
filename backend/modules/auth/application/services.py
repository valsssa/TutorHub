"""Auth service layer - business logic."""

import logging
import os
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from auth import create_access_token, get_password_hash, verify_password
from core.sanitization import sanitize_email
from modules.auth.domain.entities import UserEntity
from modules.auth.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.repository = UserRepository(db)
        self.db = db

    def register_user(
        self,
        email: str,
        password: str,
        role: str = "student",
        timezone: str = "UTC",
        currency: str = "USD",
    ) -> UserEntity:
        """
        Register a new user.

        Args:
            email: User email (will be sanitized and normalized)
            password: Plain password (will be hashed)
            role: User role (defaults to student)

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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user entity
        user_entity = UserEntity(
            id=None,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
            is_verified=False,
            timezone=timezone,
            currency=currency,
        )

        # Save to database
        created_user = self.repository.create(user_entity)
        logger.info(f"User registered successfully: {created_user.email}, role: {created_user.role}")

        return created_user

    def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate user and generate token.

        Args:
            email: User email
            password: Plain password

        Returns:
            Dictionary with access_token and token_type

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

        # Create access token
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=30),
        )

        logger.info(f"User authenticated successfully: {user.email}, role: {user.role}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
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
