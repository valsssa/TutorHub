"""SQLAlchemy repository implementation for auth module.

Implements the UserRepository Protocol for user persistence operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.soft_delete import filter_active
from models import User
from modules.auth.domain.entities import UserEntity

logger = logging.getLogger(__name__)


class UserRepositoryImpl:
    """
    SQLAlchemy implementation of the UserRepository Protocol.

    Handles all user persistence operations with soft delete support.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy session for database operations
        """
        self.db = db

    def get_by_id(self, user_id: int) -> UserEntity | None:
        """
        Get a user by their ID.

        Args:
            user_id: User's unique identifier

        Returns:
            UserEntity if found, None otherwise
        """
        user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user_id)
            .first()
        )
        return self._to_entity(user) if user else None

    def get_by_email(self, email: str) -> UserEntity | None:
        """
        Get a user by their email address.

        Args:
            email: User's email address (case-insensitive)

        Returns:
            UserEntity if found, None otherwise
        """
        if not email:
            return None

        user = (
            filter_active(self.db.query(User), User)
            .filter(func.lower(User.email) == email.lower())
            .first()
        )
        return self._to_entity(user) if user else None

    def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        if not email:
            return False

        return (
            filter_active(self.db.query(User), User)
            .filter(func.lower(User.email) == email.lower())
            .first()
            is not None
        )

    def create(
        self,
        user: UserEntity,
        registration_ip: str | None = None,
        trial_restricted: bool = False,
    ) -> UserEntity:
        """
        Create a new user.

        Args:
            user: User entity to create
            registration_ip: IP address at registration (for fraud detection)
            trial_restricted: Whether to restrict free trial (fraud prevention)

        Returns:
            Created user with populated ID

        Raises:
            ValueError: If email is already registered
        """
        if self.exists_by_email(user.email):
            raise ValueError(f"Email {user.email} is already registered")

        db_user = self._to_model(user)
        # Override fraud detection fields if provided
        if registration_ip is not None:
            db_user.registration_ip = registration_ip
        if trial_restricted:
            db_user.trial_restricted = trial_restricted

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        logger.info(f"Created user with ID {db_user.id}")
        return self._to_entity(db_user)

    def update(self, user: UserEntity) -> UserEntity:
        """
        Update an existing user.

        Args:
            user: User entity with updated fields

        Returns:
            Updated user entity

        Raises:
            ValueError: If user not found
        """
        if user.id is None:
            raise ValueError("Cannot update user without ID")

        db_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user.id)
            .first()
        )
        if not db_user:
            raise ValueError(f"User with ID {user.id} not found")

        db_user.email = user.email.lower()
        db_user.hashed_password = user.hashed_password
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.role = user.role
        db_user.is_active = user.is_active
        db_user.is_verified = user.is_verified
        db_user.timezone = user.timezone
        db_user.currency = user.currency
        db_user.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(db_user)

        logger.info(f"Updated user with ID {user.id}")
        return self._to_entity(db_user)

    def delete(self, user_id: int) -> bool:
        """
        Soft delete a user.

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user_id)
            .first()
        )
        if not db_user:
            return False

        db_user.deleted_at = datetime.now(UTC)
        self.db.commit()

        logger.info(f"Soft deleted user with ID {user_id}")
        return True

    def list_users(
        self,
        *,
        role: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[UserEntity]:
        """
        List users with optional filtering.

        Args:
            role: Filter by role
            is_active: Filter by active status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching users
        """
        query = filter_active(self.db.query(User), User)

        if role is not None:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        offset = (page - 1) * page_size
        users = query.order_by(User.id).offset(offset).limit(page_size).all()

        return [self._to_entity(user) for user in users]

    def count_users(
        self,
        *,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """
        Count users with optional filtering.

        Args:
            role: Filter by role
            is_active: Filter by active status

        Returns:
            Total count of matching users
        """
        query = filter_active(self.db.query(User), User)

        if role is not None:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return query.count()

    def update_password(
        self,
        user_id: int,
        hashed_password: str,
    ) -> bool:
        """
        Update a user's password hash.

        Args:
            user_id: User ID
            hashed_password: New password hash

        Returns:
            True if updated, False if user not found
        """
        db_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user_id)
            .first()
        )
        if not db_user:
            return False

        now = datetime.now(UTC)
        db_user.hashed_password = hashed_password
        db_user.password_changed_at = now
        db_user.updated_at = now

        self.db.commit()

        logger.info(f"Updated password for user ID {user_id}")
        return True

    def update_last_login(self, user_id: int) -> bool:
        """
        Update a user's last login timestamp.

        Note: This implementation updates the updated_at field as a proxy
        for last login since the User model doesn't have a dedicated
        last_login field.

        Args:
            user_id: User ID

        Returns:
            True if updated, False if user not found
        """
        db_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user_id)
            .first()
        )
        if not db_user:
            return False

        db_user.updated_at = datetime.now(UTC)
        self.db.commit()

        logger.debug(f"Updated last login for user ID {user_id}")
        return True

    def verify_email(self, user_id: int) -> bool:
        """
        Mark a user's email as verified.

        Args:
            user_id: User ID

        Returns:
            True if updated, False if user not found
        """
        db_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == user_id)
            .first()
        )
        if not db_user:
            return False

        db_user.is_verified = True
        db_user.updated_at = datetime.now(UTC)

        self.db.commit()

        logger.info(f"Verified email for user ID {user_id}")
        return True

    def _to_entity(self, model: User) -> UserEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy User model instance

        Returns:
            UserEntity domain object
        """
        return UserEntity(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            first_name=model.first_name,
            last_name=model.last_name,
            role=model.role,
            is_active=model.is_active,
            is_verified=model.is_verified,
            timezone=model.timezone or "UTC",
            currency=model.currency or "USD",
            created_at=model.created_at,
            updated_at=model.updated_at,
            password_changed_at=model.password_changed_at,
            registration_ip=str(model.registration_ip) if model.registration_ip else None,
            trial_restricted=model.trial_restricted or False,
        )

    def _to_model(self, entity: UserEntity) -> User:
        """
        Convert domain entity to ORM model.

        Note: This creates a new model instance. For updates, use the
        update() method which modifies an existing model.

        Args:
            entity: UserEntity domain object

        Returns:
            SQLAlchemy User model instance
        """
        return User(
            id=entity.id,
            email=entity.email.lower(),
            hashed_password=entity.hashed_password,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            timezone=entity.timezone,
            currency=entity.currency,
            registration_ip=entity.registration_ip,
            trial_restricted=entity.trial_restricted,
        )


    # Backwards compatibility methods for legacy code
    def find_by_id(self, user_id: int) -> UserEntity | None:
        """Alias for get_by_id for backwards compatibility."""
        return self.get_by_id(user_id)

    def find_by_email(self, email: str | None) -> UserEntity | None:
        """Alias for get_by_email for backwards compatibility."""
        if not email:
            return None
        return self.get_by_email(email)

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[UserEntity]:
        """
        Find all users with pagination for backwards compatibility.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Filter to only active users

        Returns:
            List of user entities
        """
        query = filter_active(self.db.query(User), User)

        if active_only:
            query = query.filter(User.is_active.is_(True))

        users = query.order_by(User.id).offset(skip).limit(limit).all()
        return [self._to_entity(user) for user in users]

    def count(self, active_only: bool = False) -> int:
        """
        Count total users for backwards compatibility.

        Args:
            active_only: Filter to only active users

        Returns:
            Total count of users
        """
        query = filter_active(self.db.query(User), User)

        if active_only:
            query = query.filter(User.is_active.is_(True))

        return query.count()

    def find_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserEntity]:
        """
        Find users by role with pagination for backwards compatibility.

        Args:
            role: Role to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user entities with the given role
        """
        users = (
            filter_active(self.db.query(User), User)
            .filter(User.role == role)
            .order_by(User.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_entity(user) for user in users]


# Note: UserRepository is the Protocol from domain/repositories.py
# UserRepositoryImpl is the concrete implementation
# They have the same name for backwards compatibility but different roles
