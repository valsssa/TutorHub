"""
Repository interfaces for reviews module.

Defines the contracts for review persistence operations.
"""

from decimal import Decimal
from typing import Protocol

from modules.reviews.domain.entities import ReviewEntity, ReviewSummary
from modules.reviews.domain.value_objects import (
    BookingId,
    ReviewId,
    StudentId,
    TutorProfileId,
)


class ReviewRepository(Protocol):
    """
    Protocol for review repository operations.

    Implementations should handle:
    - Review CRUD operations
    - Student and tutor-based queries
    - Rating calculations
    - Pagination
    """

    def get_by_id(self, review_id: ReviewId) -> ReviewEntity | None:
        """
        Get a review by its ID.

        Args:
            review_id: Review's unique identifier

        Returns:
            ReviewEntity if found, None otherwise
        """
        ...

    def get_by_booking(self, booking_id: BookingId) -> ReviewEntity | None:
        """
        Get a review for a specific booking.

        Since each booking can only have one review, this returns
        a single entity or None.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            ReviewEntity if found, None otherwise
        """
        ...

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        only_public: bool = True,
        min_rating: int | None = None,
        max_rating: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ReviewEntity]:
        """
        Get reviews for a tutor with optional filtering.

        Args:
            tutor_profile_id: Tutor's profile ID
            only_public: Only return public reviews
            min_rating: Filter by minimum rating
            max_rating: Filter by maximum rating
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching reviews, ordered by created_at descending
        """
        ...

    def get_by_student(
        self,
        student_id: StudentId,
        *,
        tutor_profile_id: TutorProfileId | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ReviewEntity]:
        """
        Get reviews written by a student.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Optional filter by tutor
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of reviews by the student, ordered by created_at descending
        """
        ...

    def create(self, review: ReviewEntity) -> ReviewEntity:
        """
        Create a new review.

        Args:
            review: Review entity to create

        Returns:
            Created review with populated ID and timestamps

        Raises:
            DuplicateReviewError: If a review already exists for the booking
        """
        ...

    def update(self, review: ReviewEntity) -> ReviewEntity:
        """
        Update an existing review.

        Args:
            review: Review entity with updated fields

        Returns:
            Updated review entity
        """
        ...

    def delete(self, review_id: ReviewId) -> bool:
        """
        Delete a review.

        Args:
            review_id: ID of the review to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def calculate_average_rating(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> tuple[Decimal, int]:
        """
        Calculate average rating for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Tuple of (average_rating, total_review_count)
            Returns (Decimal("0.00"), 0) if no reviews exist
        """
        ...

    def get_summary(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> ReviewSummary:
        """
        Get review summary statistics for a tutor.

        Includes average rating, total count, and rating distribution.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            ReviewSummary with statistics
        """
        ...

    def count_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        only_public: bool = True,
    ) -> int:
        """
        Count reviews for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            only_public: Only count public reviews

        Returns:
            Count of matching reviews
        """
        ...

    def count_by_student(
        self,
        student_id: StudentId,
    ) -> int:
        """
        Count reviews written by a student.

        Args:
            student_id: Student's user ID

        Returns:
            Count of reviews by student
        """
        ...

    def exists_for_booking(self, booking_id: BookingId) -> bool:
        """
        Check if a review exists for a booking.

        Used to prevent duplicate reviews.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            True if review exists, False otherwise
        """
        ...

    def get_recent_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        limit: int = 5,
    ) -> list[ReviewEntity]:
        """
        Get the most recent reviews for a tutor.

        Convenience method for displaying recent reviews on tutor profiles.

        Args:
            tutor_profile_id: Tutor's profile ID
            limit: Maximum number of reviews to return

        Returns:
            List of recent public reviews
        """
        ...

    def get_featured_reviews(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        limit: int = 3,
    ) -> list[ReviewEntity]:
        """
        Get featured reviews for a tutor (high-rated with content).

        Selects reviews that are:
        - Public
        - Rating of 4 or 5
        - Has non-empty content

        Args:
            tutor_profile_id: Tutor's profile ID
            limit: Maximum number of reviews to return

        Returns:
            List of featured reviews
        """
        ...
