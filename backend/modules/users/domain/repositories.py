"""
Repository interfaces for users module.

Defines the contracts for user persistence operations.
"""

from typing import Protocol

from modules.users.domain.entities import UserEntity, UserPreferences
from modules.users.domain.value_objects import (
    AvatarKey,
    Currency,
    Timezone,
    UserId,
)


class UserRepository(Protocol):
    """
    Protocol for user repository operations.

    Implementations should handle:
    - User CRUD operations
    - Email and ID lookups
    - Preference updates
    - Avatar management
    """

    def get_by_id(self, user_id: UserId) -> UserEntity | None:
        """
        Get a user by their ID.

        Args:
            user_id: User's unique identifier

        Returns:
            UserEntity if found, None otherwise
        """
        ...

    def get_by_email(self, email: str) -> UserEntity | None:
        """
        Get a user by their email address.

        Args:
            email: User's email address

        Returns:
            UserEntity if found, None otherwise
        """
        ...

    def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        ...

    def get_active_users(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[UserEntity]:
        """
        Get active users with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of active user entities
        """
        ...

    def update_preferences(
        self,
        user_id: UserId,
        *,
        currency: Currency | None = None,
        timezone: Timezone | None = None,
    ) -> UserEntity | None:
        """
        Update user preferences.

        Args:
            user_id: User's unique identifier
            currency: New currency code (optional)
            timezone: New timezone (optional)

        Returns:
            Updated UserEntity if found, None otherwise
        """
        ...

    def update_avatar(
        self,
        user_id: UserId,
        avatar_key: AvatarKey | None,
    ) -> UserEntity | None:
        """
        Update user's avatar key.

        Args:
            user_id: User's unique identifier
            avatar_key: New avatar key or None to remove

        Returns:
            Updated UserEntity if found, None otherwise
        """
        ...

    def get_preferences(self, user_id: UserId) -> UserPreferences | None:
        """
        Get user preferences.

        Args:
            user_id: User's unique identifier

        Returns:
            UserPreferences if found, None otherwise
        """
        ...

    def count_active_users(self) -> int:
        """
        Count all active users.

        Returns:
            Total count of active users
        """
        ...

    def count_users_by_role(self, role: str) -> int:
        """
        Count users by role.

        Args:
            role: User role to filter by

        Returns:
            Count of users with the given role
        """
        ...
