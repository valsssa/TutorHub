"""
Domain entities for reviews module.

These are pure data classes representing the core review domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from core.datetime_utils import utc_now

from modules.reviews.domain.exceptions import ReviewEditWindowExpiredError
from modules.reviews.domain.value_objects import (
    EDIT_WINDOW_HOURS,
    BookingId,
    Rating,
    ReviewContent,
    ReviewId,
    StudentId,
    TutorId,
    TutorProfileId,
)


@dataclass
class ReviewEntity:
    """
    Core review domain entity.

    Represents a student's review of a completed tutoring session.
    Reviews are linked to bookings and can only be created after
    a session has been completed successfully.
    """

    id: ReviewId | None
    booking_id: BookingId
    student_id: StudentId
    tutor_id: TutorId
    tutor_profile_id: TutorProfileId

    # Review content
    rating: int
    content: str | None = None

    # Visibility
    is_public: bool = True

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Tutor response
    response: str | None = None
    responded_at: datetime | None = None

    # Booking snapshot (immutable record of what was reviewed)
    booking_snapshot: str | None = None

    @property
    def rating_vo(self) -> Rating:
        """Get rating as value object."""
        return Rating(self.rating)

    @property
    def content_vo(self) -> ReviewContent:
        """Get content as value object."""
        return ReviewContent(self.content)

    @property
    def has_content(self) -> bool:
        """Check if review has text content."""
        return bool(self.content and self.content.strip())

    @property
    def has_response(self) -> bool:
        """Check if tutor has responded to this review."""
        return bool(self.response and self.response.strip())

    @property
    def is_positive(self) -> bool:
        """Check if this is a positive review (4-5 stars)."""
        return self.rating >= 4

    @property
    def is_negative(self) -> bool:
        """Check if this is a negative review (1-2 stars)."""
        return self.rating <= 2

    @property
    def is_editable(self) -> bool:
        """Check if review is within the edit window."""
        if self.created_at is None:
            return True
        now = utc_now()
        created = self.created_at.replace(tzinfo=UTC) if self.created_at.tzinfo is None else self.created_at
        edit_deadline = created + timedelta(hours=EDIT_WINDOW_HOURS)
        return now <= edit_deadline

    @property
    def hours_since_creation(self) -> float | None:
        """Calculate hours since review was created."""
        if self.created_at is None:
            return None
        now = utc_now()
        created = self.created_at.replace(tzinfo=UTC) if self.created_at.tzinfo is None else self.created_at
        delta = now - created
        return delta.total_seconds() / 3600

    @property
    def hours_until_edit_expires(self) -> float | None:
        """Calculate hours until edit window expires."""
        if self.created_at is None:
            return None
        hours_since = self.hours_since_creation
        if hours_since is None:
            return None
        remaining = EDIT_WINDOW_HOURS - hours_since
        return max(0.0, remaining)

    def can_edit(self) -> tuple[bool, str | None]:
        """
        Check if review can be edited.

        Returns:
            tuple: (can_edit, error_message)
        """
        if not self.is_editable:
            return False, f"Review edit window of {EDIT_WINDOW_HOURS} hours has expired"
        return True, None

    def update_content(
        self,
        rating: int | None = None,
        content: str | None = None,
    ) -> "ReviewEntity":
        """
        Create a new entity with updated content.

        Args:
            rating: New rating (if None, keeps current)
            content: New content (if None, keeps current)

        Returns:
            New ReviewEntity with updated fields

        Raises:
            ReviewEditWindowExpiredError: If edit window has expired
        """
        if not self.is_editable:
            raise ReviewEditWindowExpiredError(
                review_id=self.id,
                hours_since_creation=self.hours_since_creation,
                edit_window_hours=EDIT_WINDOW_HOURS,
            )

        return ReviewEntity(
            id=self.id,
            booking_id=self.booking_id,
            student_id=self.student_id,
            tutor_id=self.tutor_id,
            tutor_profile_id=self.tutor_profile_id,
            rating=rating if rating is not None else self.rating,
            content=content if content is not None else self.content,
            is_public=self.is_public,
            created_at=self.created_at,
            updated_at=utc_now(),
            response=self.response,
            responded_at=self.responded_at,
            booking_snapshot=self.booking_snapshot,
        )

    def add_response(self, response: str) -> "ReviewEntity":
        """
        Create a new entity with tutor response.

        Args:
            response: Tutor's response text

        Returns:
            New ReviewEntity with response
        """
        return ReviewEntity(
            id=self.id,
            booking_id=self.booking_id,
            student_id=self.student_id,
            tutor_id=self.tutor_id,
            tutor_profile_id=self.tutor_profile_id,
            rating=self.rating,
            content=self.content,
            is_public=self.is_public,
            created_at=self.created_at,
            updated_at=utc_now(),
            response=response.strip() if response else None,
            responded_at=utc_now() if response else None,
            booking_snapshot=self.booking_snapshot,
        )

    def toggle_visibility(self) -> "ReviewEntity":
        """
        Create a new entity with toggled visibility.

        Returns:
            New ReviewEntity with toggled is_public
        """
        return ReviewEntity(
            id=self.id,
            booking_id=self.booking_id,
            student_id=self.student_id,
            tutor_id=self.tutor_id,
            tutor_profile_id=self.tutor_profile_id,
            rating=self.rating,
            content=self.content,
            is_public=not self.is_public,
            created_at=self.created_at,
            updated_at=utc_now(),
            response=self.response,
            responded_at=self.responded_at,
            booking_snapshot=self.booking_snapshot,
        )


@dataclass
class ReviewSummary:
    """Summary statistics for a tutor's reviews."""

    tutor_profile_id: TutorProfileId
    total_reviews: int
    average_rating: float
    five_star_count: int = 0
    four_star_count: int = 0
    three_star_count: int = 0
    two_star_count: int = 0
    one_star_count: int = 0

    @property
    def has_reviews(self) -> bool:
        """Check if tutor has any reviews."""
        return self.total_reviews > 0

    @property
    def positive_count(self) -> int:
        """Count of positive reviews (4-5 stars)."""
        return self.five_star_count + self.four_star_count

    @property
    def negative_count(self) -> int:
        """Count of negative reviews (1-2 stars)."""
        return self.one_star_count + self.two_star_count

    @property
    def neutral_count(self) -> int:
        """Count of neutral reviews (3 stars)."""
        return self.three_star_count

    @property
    def positive_percentage(self) -> float:
        """Percentage of positive reviews."""
        if self.total_reviews == 0:
            return 0.0
        return (self.positive_count / self.total_reviews) * 100

    @property
    def rating_distribution(self) -> dict[int, int]:
        """Get rating distribution as a dictionary."""
        return {
            5: self.five_star_count,
            4: self.four_star_count,
            3: self.three_star_count,
            2: self.two_star_count,
            1: self.one_star_count,
        }

    @classmethod
    def empty(cls, tutor_profile_id: TutorProfileId) -> "ReviewSummary":
        """Create empty summary for tutor with no reviews."""
        return cls(
            tutor_profile_id=tutor_profile_id,
            total_reviews=0,
            average_rating=0.0,
        )
