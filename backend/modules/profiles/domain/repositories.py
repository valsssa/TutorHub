"""
Repository interface for profiles module.

Defines the contract for profile persistence operations.
"""

from typing import Protocol

from modules.profiles.domain.entities import UserProfileEntity
from modules.profiles.domain.value_objects import ProfileId, UserId


class UserProfileRepository(Protocol):
    """
    Protocol for user profile repository operations.

    Implementations should handle:
    - Profile CRUD operations
    - User ID lookups
    - Avatar management
    """

    def get_by_id(self, profile_id: ProfileId) -> UserProfileEntity | None:
        """
        Get a profile by its ID.

        Args:
            profile_id: Profile's unique identifier

        Returns:
            UserProfileEntity if found, None otherwise
        """
        ...

    def get_by_user_id(self, user_id: UserId) -> UserProfileEntity | None:
        """
        Get a profile by user ID.

        This is the primary lookup method since profiles are one-to-one with users.

        Args:
            user_id: User's unique identifier

        Returns:
            UserProfileEntity if found, None otherwise
        """
        ...

    def create(self, profile: UserProfileEntity) -> UserProfileEntity:
        """
        Create a new user profile.

        Args:
            profile: Profile entity to create

        Returns:
            Created profile with populated ID

        Raises:
            IntegrityError: If profile already exists for user
        """
        ...

    def update(self, profile: UserProfileEntity) -> UserProfileEntity:
        """
        Update an existing profile.

        Args:
            profile: Profile entity with updated fields

        Returns:
            Updated profile entity

        Raises:
            ProfileNotFoundError: If profile does not exist
        """
        ...

    def update_avatar(
        self,
        user_id: UserId,
        avatar_key: str | None,
    ) -> bool:
        """
        Update a user's avatar key.

        Note: Avatar is stored on the User model, not UserProfile.
        This method updates the User.avatar_key field.

        Args:
            user_id: User ID
            avatar_key: New avatar storage key (or None to remove)

        Returns:
            True if updated, False if user not found
        """
        ...

    def get_or_create(self, user_id: UserId) -> UserProfileEntity:
        """
        Get a profile by user ID, creating an empty one if not found.

        Args:
            user_id: User's unique identifier

        Returns:
            Existing or newly created UserProfileEntity
        """
        ...

    def delete(self, profile_id: ProfileId) -> bool:
        """
        Delete a profile.

        Note: Profiles are typically cascade deleted with users,
        but this method allows explicit deletion if needed.

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def exists_for_user(self, user_id: UserId) -> bool:
        """
        Check if a profile exists for a given user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if profile exists, False otherwise
        """
        ...
