"""
Repository interface for auth module.

Defines the contract for user persistence operations.
"""

from typing import Protocol

from modules.auth.domain.entities import UserEntity


class UserRepository(Protocol):
    """
    Protocol for user repository operations.

    Implementations should handle:
    - User CRUD operations
    - Email lookups
    - Soft delete handling
    """

    def get_by_id(self, user_id: int) -> UserEntity | None:
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
            email: User's email address (case-insensitive)

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

    def create(self, user: UserEntity) -> UserEntity:
        """
        Create a new user.

        Args:
            user: User entity to create

        Returns:
            Created user with populated ID

        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        ...

    def update(self, user: UserEntity) -> UserEntity:
        """
        Update an existing user.

        Args:
            user: User entity with updated fields

        Returns:
            Updated user entity
        """
        ...

    def delete(self, user_id: int) -> bool:
        """
        Soft delete a user.

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

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
        ...

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
        ...

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
        ...

    def update_last_login(self, user_id: int) -> bool:
        """
        Update a user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated, False if user not found
        """
        ...

    def verify_email(self, user_id: int) -> bool:
        """
        Mark a user's email as verified.

        Args:
            user_id: User ID

        Returns:
            True if updated, False if user not found
        """
        ...
