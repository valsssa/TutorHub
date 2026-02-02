"""
Repository interface for subjects module.

Defines the contract for subject persistence operations.
"""

from typing import Protocol

from modules.subjects.domain.entities import SubjectEntity
from modules.subjects.domain.value_objects import SubjectCategory, SubjectLevel


class SubjectRepository(Protocol):
    """
    Protocol for subject repository operations.

    Implementations should handle:
    - Subject CRUD operations
    - Name-based lookups
    - Filtering by category, level, and active status
    - Search functionality
    """

    def get_by_id(self, subject_id: int) -> SubjectEntity | None:
        """
        Get a subject by its ID.

        Args:
            subject_id: Subject's unique identifier

        Returns:
            SubjectEntity if found, None otherwise
        """
        ...

    def get_by_name(self, name: str) -> SubjectEntity | None:
        """
        Get a subject by its name (case-insensitive).

        Args:
            name: Subject name to look up

        Returns:
            SubjectEntity if found, None otherwise
        """
        ...

    def get_all(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> list[SubjectEntity]:
        """
        Get all subjects with optional filtering.

        Args:
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching subjects
        """
        ...

    def get_active(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
    ) -> list[SubjectEntity]:
        """
        Get all active subjects with optional filtering.

        Convenience method that calls get_all with include_inactive=False.

        Args:
            category: Filter by category
            level: Filter by education level

        Returns:
            List of active subjects
        """
        ...

    def create(self, subject: SubjectEntity) -> SubjectEntity:
        """
        Create a new subject.

        Args:
            subject: Subject entity to create

        Returns:
            Created subject with populated ID

        Raises:
            DuplicateSubjectError: If a subject with the same name exists
        """
        ...

    def update(self, subject: SubjectEntity) -> SubjectEntity:
        """
        Update an existing subject.

        Args:
            subject: Subject entity with updated fields

        Returns:
            Updated subject entity

        Raises:
            SubjectNotFoundError: If subject doesn't exist
            DuplicateSubjectError: If new name conflicts with existing subject
        """
        ...

    def delete(self, subject_id: int) -> bool:
        """
        Delete a subject (soft delete by setting is_active to False).

        Args:
            subject_id: Subject ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            SubjectInUseError: If subject is still taught by tutors
        """
        ...

    def search(
        self,
        query: str,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
        limit: int = 20,
    ) -> list[SubjectEntity]:
        """
        Search subjects by name or description.

        Args:
            query: Search query string
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects
            limit: Maximum number of results

        Returns:
            List of matching subjects
        """
        ...

    def count(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
    ) -> int:
        """
        Count subjects with optional filtering.

        Args:
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects

        Returns:
            Total count of matching subjects
        """
        ...

    def exists_by_name(self, name: str) -> bool:
        """
        Check if a subject exists with the given name.

        Args:
            name: Subject name to check (case-insensitive)

        Returns:
            True if subject exists, False otherwise
        """
        ...

    def get_tutor_count(self, subject_id: int) -> int:
        """
        Get the number of tutors teaching this subject.

        Args:
            subject_id: Subject ID

        Returns:
            Number of tutors teaching this subject
        """
        ...

    def get_by_category(
        self,
        category: SubjectCategory,
        *,
        include_inactive: bool = False,
    ) -> list[SubjectEntity]:
        """
        Get all subjects in a specific category.

        Args:
            category: Category to filter by
            include_inactive: Whether to include inactive subjects

        Returns:
            List of subjects in the category
        """
        ...

    def get_popular(
        self,
        *,
        limit: int = 10,
    ) -> list[SubjectEntity]:
        """
        Get the most popular subjects based on tutor count.

        Args:
            limit: Maximum number of subjects to return

        Returns:
            List of popular subjects sorted by tutor count
        """
        ...
