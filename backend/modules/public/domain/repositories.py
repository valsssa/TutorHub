"""
Repository interface for public module.

Defines the contract for public tutor data access operations.
"""

from typing import Protocol

from modules.public.domain.entities import PublicTutorProfileEntity, SearchResultEntity
from modules.public.domain.value_objects import (
    PaginationParams,
    SearchFilters,
    SearchQuery,
    SortOrder,
)


class PublicTutorRepository(Protocol):
    """
    Protocol for public tutor repository operations.

    Implementations should handle:
    - Public tutor search and filtering
    - Featured tutor retrieval
    - Subject-based queries
    - Only returning approved, public profiles
    """

    def search(
        self,
        query: SearchQuery | None = None,
        filters: SearchFilters | None = None,
        pagination: PaginationParams | None = None,
        sort_by: SortOrder = SortOrder.RELEVANCE,
    ) -> SearchResultEntity:
        """
        Search for tutors with optional query, filters, and pagination.

        Args:
            query: Optional search query for text matching
            filters: Optional filters for subject, rating, price, availability
            pagination: Pagination parameters (page, page_size)
            sort_by: Sort order for results

        Returns:
            SearchResultEntity containing matching tutors and pagination info
        """
        ...

    def get_public_profile(
        self,
        tutor_id: int,
    ) -> PublicTutorProfileEntity | None:
        """
        Get a single public tutor profile by tutor profile ID.

        Only returns the profile if the tutor is approved and visible.

        Args:
            tutor_id: Tutor profile ID

        Returns:
            PublicTutorProfileEntity if found and public, None otherwise
        """
        ...

    def get_public_profile_by_user_id(
        self,
        user_id: int,
    ) -> PublicTutorProfileEntity | None:
        """
        Get a single public tutor profile by user ID.

        Only returns the profile if the tutor is approved and visible.

        Args:
            user_id: User ID of the tutor

        Returns:
            PublicTutorProfileEntity if found and public, None otherwise
        """
        ...

    def get_featured(
        self,
        limit: int = 6,
    ) -> list[PublicTutorProfileEntity]:
        """
        Get featured tutors for homepage display.

        Featured tutors are typically those with high ratings,
        many completed sessions, or manually selected.

        Args:
            limit: Maximum number of featured tutors to return

        Returns:
            List of featured tutor profiles
        """
        ...

    def get_by_subject(
        self,
        subject_id: int,
        pagination: PaginationParams | None = None,
        sort_by: SortOrder = SortOrder.RATING,
    ) -> SearchResultEntity:
        """
        Get tutors who teach a specific subject.

        Args:
            subject_id: Subject ID to filter by
            pagination: Pagination parameters
            sort_by: Sort order for results

        Returns:
            SearchResultEntity containing tutors for the subject
        """
        ...

    def get_top_rated(
        self,
        limit: int = 10,
        min_reviews: int = 3,
    ) -> list[PublicTutorProfileEntity]:
        """
        Get top-rated tutors.

        Only includes tutors with a minimum number of reviews
        to ensure statistical significance.

        Args:
            limit: Maximum number of tutors to return
            min_reviews: Minimum number of reviews required

        Returns:
            List of top-rated tutor profiles
        """
        ...

    def count_by_subject(
        self,
        subject_id: int,
    ) -> int:
        """
        Count tutors teaching a specific subject.

        Args:
            subject_id: Subject ID to filter by

        Returns:
            Number of tutors teaching the subject
        """
        ...

    def get_subjects_with_tutors(self) -> list[tuple[int, str, int]]:
        """
        Get all subjects that have active tutors.

        Returns:
            List of tuples (subject_id, subject_name, tutor_count)
        """
        ...
