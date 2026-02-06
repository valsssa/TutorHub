"""SQLAlchemy repository implementation for users module.

Provides concrete implementation of the UserRepository protocol
defined in the domain layer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User
from modules.users.domain.entities import UserEntity, UserPreferences
from modules.users.domain.value_objects import (
    AvatarKey,
    Currency,
    Language,
    Timezone,
    UserId,
)

logger = logging.getLogger(__name__)


class UserRepositoryImpl:
    """SQLAlchemy implementation of UserRepository.

    Handles persistence of user data including preferences and avatars.
    Uses soft delete for user removal.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, user_id: UserId) -> UserEntity | None:
        """Get a user by their ID.

        Args:
            user_id: User's unique identifier

        Returns:
            UserEntity if found, None otherwise
        """
        model = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_email(self, email: str) -> UserEntity | None:
        """Get a user by their email address.

        Args:
            email: User's email address

        Returns:
            UserEntity if found, None otherwise
        """
        model = (
            self.db.query(User)
            .filter(User.email == email.lower(), User.deleted_at.is_(None))
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def exists_by_email(self, email: str) -> bool:
        """Check if a user exists with the given email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        exists = (
            self.db.query(User.id)
            .filter(User.email == email.lower(), User.deleted_at.is_(None))
            .first()
        )
        return exists is not None

    def get_active_users(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[UserEntity]:
        """Get active users with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of active user entities
        """
        query = (
            self.db.query(User)
            .filter(User.is_active.is_(True), User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
        )

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def update_preferences(
        self,
        user_id: UserId,
        *,
        currency: Currency | None = None,
        timezone: Timezone | None = None,
    ) -> UserEntity | None:
        """Update user preferences.

        Args:
            user_id: User's unique identifier
            currency: New currency code (optional)
            timezone: New timezone (optional)

        Returns:
            Updated UserEntity if found, None otherwise
        """
        model = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not model:
            return None

        updated = False
        if currency is not None:
            model.currency = str(currency)
            updated = True
        if timezone is not None:
            model.timezone = str(timezone)
            updated = True

        if updated:
            model.updated_at = datetime.now(UTC)
            self.db.flush()
            logger.info(
                f"Updated preferences for user {user_id}: "
                f"currency={currency}, timezone={timezone}"
            )

        return self._to_entity(model)

    def update_avatar(
        self,
        user_id: UserId,
        avatar_key: AvatarKey | None,
    ) -> UserEntity | None:
        """Update user's avatar key.

        Args:
            user_id: User's unique identifier
            avatar_key: New avatar key or None to remove

        Returns:
            Updated UserEntity if found, None otherwise
        """
        model = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not model:
            return None

        model.avatar_key = str(avatar_key) if avatar_key else None
        model.updated_at = datetime.now(UTC)
        self.db.flush()

        action = "updated" if avatar_key else "removed"
        logger.info(f"Avatar {action} for user {user_id}")

        return self._to_entity(model)

    def get_preferences(self, user_id: UserId) -> UserPreferences | None:
        """Get user preferences.

        Args:
            user_id: User's unique identifier

        Returns:
            UserPreferences if found, None otherwise
        """
        model = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not model:
            return None

        return UserPreferences(
            user_id=UserId(model.id),
            currency=Currency(model.currency),
            timezone=Timezone(model.timezone),
            preferred_language=Language(model.preferred_language),
        )

    def count_active_users(self) -> int:
        """Count all active users.

        Returns:
            Total count of active users
        """
        count = (
            self.db.query(func.count(User.id))
            .filter(User.is_active.is_(True), User.deleted_at.is_(None))
            .scalar()
        )
        return count or 0

    def count_users_by_role(self, role: str) -> int:
        """Count users by role.

        Args:
            role: User role to filter by

        Returns:
            Count of users with the given role
        """
        count = (
            self.db.query(func.count(User.id))
            .filter(
                User.role == role,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .scalar()
        )
        return count or 0

    def _to_entity(self, model: User) -> UserEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: User SQLAlchemy model

        Returns:
            UserEntity domain entity
        """
        return UserEntity(
            id=UserId(model.id) if model.id else None,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            role=model.role,
            is_active=model.is_active,
            is_verified=model.is_verified,
            profile_incomplete=model.profile_incomplete,
            avatar_key=AvatarKey(model.avatar_key) if model.avatar_key else None,
            currency=Currency(model.currency),
            timezone=Timezone(model.timezone),
            preferred_language=Language(model.preferred_language),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
