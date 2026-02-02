"""
Repository interface for students module.

Defines the contract for student profile persistence operations.
"""

from typing import Protocol

from modules.students.domain.entities import StudentProfileEntity


class StudentProfileRepository(Protocol):
    """
    Protocol for student profile repository operations.

    Implementations should handle:
    - Student profile CRUD operations
    - User ID lookups
    - Soft delete handling (if applicable)
    """

    def get_by_id(self, profile_id: int) -> StudentProfileEntity | None:
        """
        Get a student profile by its ID.

        Args:
            profile_id: Student profile's unique identifier

        Returns:
            StudentProfileEntity if found, None otherwise
        """
        ...

    def get_by_user_id(self, user_id: int) -> StudentProfileEntity | None:
        """
        Get a student profile by the user's ID.

        Args:
            user_id: User's unique identifier

        Returns:
            StudentProfileEntity if found, None otherwise
        """
        ...

    def create(self, profile: StudentProfileEntity) -> StudentProfileEntity:
        """
        Create a new student profile.

        Args:
            profile: Student profile entity to create

        Returns:
            Created profile with populated ID

        Raises:
            InvalidStudentDataError: If profile data is invalid
        """
        ...

    def update(self, profile: StudentProfileEntity) -> StudentProfileEntity:
        """
        Update an existing student profile.

        Args:
            profile: Student profile entity with updated fields

        Returns:
            Updated profile entity

        Raises:
            StudentProfileNotFoundError: If profile doesn't exist
        """
        ...

    def delete(self, profile_id: int) -> bool:
        """
        Delete a student profile (soft delete if supported).

        Args:
            profile_id: Student profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def exists_by_user_id(self, user_id: int) -> bool:
        """
        Check if a student profile exists for the given user.

        Args:
            user_id: User ID to check

        Returns:
            True if profile exists, False otherwise
        """
        ...

    def list_profiles(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentProfileEntity]:
        """
        List student profiles with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of student profiles
        """
        ...

    def count_profiles(self) -> int:
        """
        Count total number of student profiles.

        Returns:
            Total count of profiles
        """
        ...

    def update_credit_balance(
        self,
        profile_id: int,
        amount_cents: int,
    ) -> bool:
        """
        Update a student's credit balance.

        Args:
            profile_id: Student profile ID
            amount_cents: New balance in cents

        Returns:
            True if updated, False if profile not found
        """
        ...

    def increment_session_count(self, profile_id: int) -> bool:
        """
        Increment a student's total session count.

        Args:
            profile_id: Student profile ID

        Returns:
            True if updated, False if profile not found
        """
        ...
