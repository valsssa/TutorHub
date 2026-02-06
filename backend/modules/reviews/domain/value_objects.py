"""
Value objects for the reviews domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from dataclasses import dataclass
from typing import NewType

from modules.reviews.domain.exceptions import InvalidRatingError, InvalidReviewContentError

# Type alias for review IDs - provides type safety without runtime overhead
ReviewId = NewType("ReviewId", int)
BookingId = NewType("BookingId", int)
StudentId = NewType("StudentId", int)
TutorId = NewType("TutorId", int)
TutorProfileId = NewType("TutorProfileId", int)

# Constants
MIN_RATING = 1
MAX_RATING = 5
MAX_CONTENT_LENGTH = 2000
EDIT_WINDOW_HOURS = 24


@dataclass(frozen=True)
class Rating:
    """
    Value object representing a review rating (1-5 stars).

    Immutable and validates that the rating is within the valid range.
    """

    value: int

    def __post_init__(self) -> None:
        """Validate rating is within allowed range."""
        if not isinstance(self.value, int):
            raise InvalidRatingError(self.value)
        if self.value < MIN_RATING or self.value > MAX_RATING:
            raise InvalidRatingError(self.value)

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __str__(self) -> str:
        """String representation."""
        return str(self.value)

    def __lt__(self, other: "Rating | int") -> bool:
        """Compare less than."""
        if isinstance(other, Rating):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: "Rating | int") -> bool:
        """Compare less than or equal."""
        if isinstance(other, Rating):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: "Rating | int") -> bool:
        """Compare greater than."""
        if isinstance(other, Rating):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: "Rating | int") -> bool:
        """Compare greater than or equal."""
        if isinstance(other, Rating):
            return self.value >= other.value
        return self.value >= other

    def __eq__(self, other: object) -> bool:
        """Compare equality."""
        if isinstance(other, Rating):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)

    @property
    def is_positive(self) -> bool:
        """Check if this is a positive rating (4 or 5 stars)."""
        return self.value >= 4

    @property
    def is_negative(self) -> bool:
        """Check if this is a negative rating (1 or 2 stars)."""
        return self.value <= 2

    @property
    def is_neutral(self) -> bool:
        """Check if this is a neutral rating (3 stars)."""
        return self.value == 3

    @property
    def stars_display(self) -> str:
        """Get star display representation."""
        return "*" * self.value

    @classmethod
    def from_int(cls, value: int) -> "Rating":
        """Create Rating from integer value."""
        return cls(value)

    @classmethod
    def excellent(cls) -> "Rating":
        """Create a 5-star rating."""
        return cls(5)

    @classmethod
    def good(cls) -> "Rating":
        """Create a 4-star rating."""
        return cls(4)

    @classmethod
    def average(cls) -> "Rating":
        """Create a 3-star rating."""
        return cls(3)

    @classmethod
    def poor(cls) -> "Rating":
        """Create a 2-star rating."""
        return cls(2)

    @classmethod
    def terrible(cls) -> "Rating":
        """Create a 1-star rating."""
        return cls(1)


@dataclass(frozen=True)
class ReviewContent:
    """
    Value object representing review text content (comment).

    Immutable and validates maximum length.
    """

    value: str | None

    def __post_init__(self) -> None:
        """Validate content length."""
        if self.value is not None:
            if not isinstance(self.value, str):
                raise InvalidReviewContentError("Content must be a string")
            if len(self.value) > MAX_CONTENT_LENGTH:
                raise InvalidReviewContentError(
                    f"Content exceeds maximum length of {MAX_CONTENT_LENGTH} characters "
                    f"(got {len(self.value)})"
                )

    def __str__(self) -> str:
        """String representation."""
        return self.value or ""

    def __bool__(self) -> bool:
        """Check if content is non-empty."""
        return bool(self.value and self.value.strip())

    def __len__(self) -> int:
        """Get content length."""
        return len(self.value) if self.value else 0

    @property
    def is_empty(self) -> bool:
        """Check if content is empty or None."""
        return not bool(self)

    @property
    def word_count(self) -> int:
        """Count words in content."""
        if not self.value:
            return 0
        return len(self.value.split())

    @property
    def truncated(self) -> str:
        """Get truncated version for previews (first 100 chars)."""
        if not self.value:
            return ""
        if len(self.value) <= 100:
            return self.value
        return self.value[:97] + "..."

    def sanitized(self) -> "ReviewContent":
        """Get sanitized content (trimmed whitespace)."""
        if not self.value:
            return ReviewContent(None)
        stripped = self.value.strip()
        return ReviewContent(stripped if stripped else None)

    @classmethod
    def empty(cls) -> "ReviewContent":
        """Create empty content."""
        return cls(None)

    @classmethod
    def from_string(cls, value: str | None) -> "ReviewContent":
        """Create ReviewContent from string, handling empty strings as None."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return cls(None)
        return cls(value.strip())


@dataclass(frozen=True)
class AverageRating:
    """
    Value object representing an average rating for a tutor.

    Stores the average rating and the count of reviews used to calculate it.
    """

    value: float
    review_count: int

    def __post_init__(self) -> None:
        """Validate average rating."""
        if self.review_count < 0:
            raise ValueError("Review count cannot be negative")
        if self.review_count == 0 and self.value != 0.0:
            raise ValueError("Average must be 0 when review count is 0")
        if (
            self.review_count > 0
            and (self.value < MIN_RATING or self.value > MAX_RATING)
        ):
            raise ValueError(
                f"Average rating must be between {MIN_RATING} and {MAX_RATING}"
            )

    @property
    def rounded_value(self) -> float:
        """Get average rounded to 2 decimal places."""
        return round(self.value, 2)

    @property
    def display_value(self) -> str:
        """Get formatted display value."""
        if self.review_count == 0:
            return "No reviews"
        return f"{self.rounded_value:.1f}/5 ({self.review_count} reviews)"

    @property
    def has_reviews(self) -> bool:
        """Check if there are any reviews."""
        return self.review_count > 0

    @classmethod
    def no_reviews(cls) -> "AverageRating":
        """Create an AverageRating for a tutor with no reviews."""
        return cls(value=0.0, review_count=0)

    @classmethod
    def from_ratings(cls, ratings: list[int]) -> "AverageRating":
        """Calculate average from a list of rating values."""
        if not ratings:
            return cls.no_reviews()
        avg = sum(ratings) / len(ratings)
        return cls(value=avg, review_count=len(ratings))
