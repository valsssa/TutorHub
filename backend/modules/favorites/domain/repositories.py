"""
Repository interfaces for favorites module.

Defines the contracts for favorite persistence operations.
"""

from typing import Protocol

from modules.favorites.domain.entities import FavoriteEntity
from modules.favorites.domain.value_objects import (
    FavoriteId,
    TutorProfileId,
    UserId,
)


class FavoriteRepository(Protocol):
    """
    Protocol for favorite repository operations.

    Implementations should handle:
    - Favorite CRUD operations
    - Student and tutor-based queries
    - Duplicate prevention
    """

    def get_by_id(self, favorite_id: FavoriteId) -> FavoriteEntity | None:
        """
        Get a favorite by its ID.

        Args:
            favorite_id: Favorite's unique identifier

        Returns:
            FavoriteEntity if found, None otherwise
        """
        ...

    def get_by_student(
        self,
        student_id: UserId,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[FavoriteEntity]:
        """
        Get all favorites for a student with pagination.

        Args:
            student_id: Student's user ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of favorite entities for the student
        """
        ...

    def is_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> bool:
        """
        Check if a tutor is favorited by a student.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            True if the tutor is favorited, False otherwise
        """
        ...

    def get_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> FavoriteEntity | None:
        """
        Get a specific favorite by student and tutor profile.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            FavoriteEntity if found, None otherwise
        """
        ...

    def add_favorite(self, favorite: FavoriteEntity) -> FavoriteEntity:
        """
        Add a new favorite.

        Args:
            favorite: Favorite entity to create

        Returns:
            Created favorite with populated ID

        Raises:
            DuplicateFavoriteError: If the favorite already exists
        """
        ...

    def remove_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> bool:
        """
        Remove a favorite by student and tutor profile.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            True if removed, False if not found
        """
        ...

    def remove_by_id(self, favorite_id: FavoriteId) -> bool:
        """
        Remove a favorite by its ID.

        Args:
            favorite_id: Favorite's unique identifier

        Returns:
            True if removed, False if not found
        """
        ...

    def count_by_student(self, student_id: UserId) -> int:
        """
        Count favorites for a student.

        Args:
            student_id: Student's user ID

        Returns:
            Total count of favorites for the student
        """
        ...

    def count_by_tutor(self, tutor_profile_id: TutorProfileId) -> int:
        """
        Count how many students have favorited a tutor.

        This can be useful for analytics or showing popularity.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Total count of students who favorited this tutor
        """
        ...

    def get_tutor_profile_ids_for_student(
        self,
        student_id: UserId,
    ) -> list[TutorProfileId]:
        """
        Get all favorited tutor profile IDs for a student.

        This is a convenience method for checking multiple tutors
        against a student's favorites list efficiently.

        Args:
            student_id: Student's user ID

        Returns:
            List of tutor profile IDs the student has favorited
        """
        ...
