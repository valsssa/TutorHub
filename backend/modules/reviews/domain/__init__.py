"""
Review domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the reviews module. This layer is independent of infrastructure concerns.
"""

from modules.reviews.domain.entities import (
    ReviewEntity,
    ReviewSummary,
)
from modules.reviews.domain.exceptions import (
    DuplicateReviewError,
    InvalidRatingError,
    InvalidReviewContentError,
    ReviewEditWindowExpiredError,
    ReviewError,
    ReviewNotAllowedError,
    ReviewNotFoundError,
    ReviewNotOwnedError,
)
from modules.reviews.domain.repositories import (
    ReviewRepository,
)
from modules.reviews.domain.value_objects import (
    EDIT_WINDOW_HOURS,
    MAX_CONTENT_LENGTH,
    MAX_RATING,
    MIN_RATING,
    AverageRating,
    BookingId,
    Rating,
    ReviewContent,
    ReviewId,
    StudentId,
    TutorId,
    TutorProfileId,
)

__all__ = [
    # Entities
    "ReviewEntity",
    "ReviewSummary",
    # Value Objects
    "ReviewId",
    "BookingId",
    "StudentId",
    "TutorId",
    "TutorProfileId",
    "Rating",
    "ReviewContent",
    "AverageRating",
    # Constants
    "MIN_RATING",
    "MAX_RATING",
    "MAX_CONTENT_LENGTH",
    "EDIT_WINDOW_HOURS",
    # Exceptions
    "ReviewError",
    "ReviewNotFoundError",
    "DuplicateReviewError",
    "InvalidRatingError",
    "ReviewNotAllowedError",
    "ReviewEditWindowExpiredError",
    "ReviewNotOwnedError",
    "InvalidReviewContentError",
    # Repository Protocols
    "ReviewRepository",
]
