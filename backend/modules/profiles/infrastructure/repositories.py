"""SQLAlchemy repository implementation for profiles module.

Provides concrete implementation of the UserProfileRepository protocol
defined in the domain layer.

Note: User profile data is split across two tables:
- users: first_name, last_name, avatar_key (auth data)
- user_profiles: bio, phone, timezone, etc. (extended profile data)

This repository combines data from both tables into the UserProfileEntity.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from core.datetime_utils import utc_now

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.avatar_storage import build_avatar_url
from models import User, UserProfile
from modules.profiles.domain.entities import UserProfileEntity
from modules.profiles.domain.exceptions import ProfileNotFoundError
from modules.profiles.domain.value_objects import ProfileId, UserId

logger = logging.getLogger(__name__)


class UserProfileRepositoryImpl:
    """SQLAlchemy implementation of UserProfileRepository.

    Handles persistence of user profile data by coordinating between
    the User and UserProfile models.

    Profile fields are distributed as follows:
    - User model: first_name, last_name, avatar_key
    - UserProfile model: bio, phone, timezone, country_of_birth,
      phone_country_code, date_of_birth, age_confirmed
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, profile_id: ProfileId) -> UserProfileEntity | None:
        """Get a profile by its ID.

        Args:
            profile_id: Profile's unique identifier (from user_profiles table)

        Returns:
            UserProfileEntity if found, None otherwise
        """
        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.id == profile_id)
            .first()
        )
        if not profile:
            return None

        user = (
            self.db.query(User)
            .filter(User.id == profile.user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return None

        return self._to_entity(profile, user)

    def get_by_user_id(self, user_id: UserId) -> UserProfileEntity | None:
        """Get a profile by user ID.

        This is the primary lookup method since profiles are one-to-one with users.

        Args:
            user_id: User's unique identifier

        Returns:
            UserProfileEntity if found, None otherwise
        """
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return None

        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

        return self._to_entity(profile, user)

    def create(self, entity: UserProfileEntity) -> UserProfileEntity:
        """Create a new user profile.

        Creates or updates the UserProfile record. User record must exist.

        Args:
            entity: Profile entity to create

        Returns:
            Created profile with populated ID

        Raises:
            IntegrityError: If profile already exists for user
            ProfileNotFoundError: If user does not exist
        """
        user = (
            self.db.query(User)
            .filter(User.id == entity.user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            raise ProfileNotFoundError(entity.user_id, by_user_id=True)

        existing = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == entity.user_id)
            .first()
        )
        if existing:
            raise IntegrityError(
                "Profile already exists",
                params={"user_id": entity.user_id},
                orig=None,
            )

        profile = self._to_model(entity)

        try:
            self.db.add(profile)
            self.db.flush()
            logger.info(f"Created profile for user {entity.user_id}")
            return self._to_entity(profile, user)
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Duplicate profile for user {entity.user_id}")
            raise

    def update(self, entity: UserProfileEntity) -> UserProfileEntity:
        """Update an existing profile.

        Updates both User fields (first_name, last_name) and
        UserProfile fields (bio, phone, timezone, etc.).

        Args:
            entity: Profile entity with updated fields

        Returns:
            Updated profile entity

        Raises:
            ProfileNotFoundError: If profile does not exist
        """
        user = (
            self.db.query(User)
            .filter(User.id == entity.user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            raise ProfileNotFoundError(entity.user_id, by_user_id=True)

        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == entity.user_id)
            .first()
        )

        now = utc_now()

        if profile is None:
            profile = UserProfile(
                user_id=entity.user_id,
                bio=entity.bio,
                phone=entity.phone,
                timezone=entity.timezone,
                country_of_birth=entity.country_of_birth,
                phone_country_code=entity.phone_country_code,
                date_of_birth=entity.date_of_birth,
                age_confirmed=entity.age_confirmed,
            )
            self.db.add(profile)
        else:
            profile.bio = entity.bio
            profile.phone = entity.phone
            profile.timezone = entity.timezone
            profile.country_of_birth = entity.country_of_birth
            profile.phone_country_code = entity.phone_country_code
            profile.date_of_birth = entity.date_of_birth
            profile.age_confirmed = entity.age_confirmed
            profile.updated_at = now

        if entity.first_name is not None:
            user.first_name = entity.first_name
        if entity.last_name is not None:
            user.last_name = entity.last_name
        user.updated_at = now

        self.db.flush()
        logger.info(f"Updated profile for user {entity.user_id}")
        return self._to_entity(profile, user)

    def update_avatar(
        self,
        user_id: UserId,
        avatar_key: str | None,
    ) -> bool:
        """Update a user's avatar key.

        Note: Avatar is stored on the User model, not UserProfile.
        This method updates the User.avatar_key field.

        Args:
            user_id: User ID
            avatar_key: New avatar storage key (or None to remove)

        Returns:
            True if updated, False if user not found
        """
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return False

        user.avatar_key = avatar_key
        user.updated_at = utc_now()
        self.db.flush()

        if avatar_key:
            logger.info(f"Updated avatar for user {user_id}")
        else:
            logger.info(f"Removed avatar for user {user_id}")

        return True

    def get_or_create(self, user_id: UserId) -> UserProfileEntity:
        """Get a profile by user ID, creating an empty one if not found.

        Args:
            user_id: User's unique identifier

        Returns:
            Existing or newly created UserProfileEntity

        Raises:
            ProfileNotFoundError: If user does not exist
        """
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            raise ProfileNotFoundError(user_id, by_user_id=True)

        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

        if profile is None:
            profile = UserProfile(
                user_id=user_id,
                timezone="UTC",
                age_confirmed=False,
            )
            self.db.add(profile)
            self.db.flush()
            logger.info(f"Created empty profile for user {user_id}")

        return self._to_entity(profile, user)

    def delete(self, profile_id: ProfileId) -> bool:
        """Delete a profile.

        Note: Profiles are typically cascade deleted with users,
        but this method allows explicit deletion if needed.
        Only deletes the UserProfile record, not the User.

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.db.query(UserProfile)
            .filter(UserProfile.id == profile_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(f"Deleted profile with ID {profile_id}")
        return result > 0

    def exists_for_user(self, user_id: UserId) -> bool:
        """Check if a profile exists for a given user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if profile exists, False otherwise
        """
        exists = (
            self.db.query(UserProfile.id)
            .filter(UserProfile.user_id == user_id)
            .first()
        )
        return exists is not None

    def _to_entity(
        self,
        profile: UserProfile | None,
        user: User,
    ) -> UserProfileEntity:
        """Convert SQLAlchemy models to domain entity.

        Combines data from User and UserProfile models into a single entity.

        Args:
            profile: UserProfile SQLAlchemy model (may be None)
            user: User SQLAlchemy model (required)

        Returns:
            UserProfileEntity domain entity
        """
        avatar_url = build_avatar_url(user.avatar_key, allow_absolute=True)

        if profile is None:
            return UserProfileEntity(
                id=None,
                user_id=UserId(user.id),
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=avatar_url,
                bio=None,
                phone=None,
                timezone=user.timezone or "UTC",
                country_of_birth=None,
                phone_country_code=None,
                date_of_birth=None,
                age_confirmed=False,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

        return UserProfileEntity(
            id=ProfileId(profile.id) if profile.id else None,
            user_id=UserId(profile.user_id),
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=avatar_url,
            bio=profile.bio,
            phone=profile.phone,
            timezone=profile.timezone or user.timezone or "UTC",
            country_of_birth=profile.country_of_birth,
            phone_country_code=profile.phone_country_code,
            date_of_birth=profile.date_of_birth,
            age_confirmed=profile.age_confirmed or False,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def _to_model(self, entity: UserProfileEntity) -> UserProfile:
        """Convert domain entity to SQLAlchemy model.

        Creates a UserProfile model from the entity.
        Note: User model fields (first_name, last_name, avatar_key)
        are not included here - they should be updated separately.

        Args:
            entity: UserProfileEntity domain entity

        Returns:
            UserProfile SQLAlchemy model
        """
        return UserProfile(
            id=entity.id,
            user_id=entity.user_id,
            bio=entity.bio,
            phone=entity.phone,
            timezone=entity.timezone,
            country_of_birth=entity.country_of_birth,
            phone_country_code=entity.phone_country_code,
            date_of_birth=entity.date_of_birth,
            age_confirmed=entity.age_confirmed,
        )
