"""
Domain exceptions for the reviews module.

These exceptions represent domain-level errors that can occur during
review operations. They are independent of infrastructure concerns.
"""


class ReviewError(Exception):
    """Base exception for all review-related domain errors."""

    def __init__(self, message: str = "A review error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class ReviewNotFoundError(ReviewError):
    """Raised when a review cannot be found."""

    def __init__(self, review_id: int | None = None) -> None:
        message = f"Review with ID {review_id} not found" if review_id else "Review not found"
        super().__init__(message)
        self.review_id = review_id


class DuplicateReviewError(ReviewError):
    """Raised when attempting to create a review for a booking that already has one."""

    def __init__(
        self,
        booking_id: int | None = None,
        existing_review_id: int | None = None,
    ) -> None:
        if booking_id:
            message = f"A review already exists for booking {booking_id}"
        else:
            message = "A review already exists for this booking"
        super().__init__(message)
        self.booking_id = booking_id
        self.existing_review_id = existing_review_id


class InvalidRatingError(ReviewError):
    """Raised when a rating value is outside the valid range (1-5)."""

    def __init__(self, rating: int | None = None) -> None:
        if rating is not None:
            message = f"Invalid rating value: {rating}. Rating must be between 1 and 5"
        else:
            message = "Invalid rating value. Rating must be between 1 and 5"
        super().__init__(message)
        self.rating = rating


class ReviewNotAllowedError(ReviewError):
    """
    Raised when a user is not allowed to create a review.

    Common scenarios:
    - The booking was not completed successfully
    - The user is not the student who attended the session
    - The booking is in an invalid state for review
    """

    def __init__(
        self,
        booking_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        if reason:
            message = reason
        elif booking_id:
            message = f"Cannot create review for booking {booking_id}"
        else:
            message = "Cannot create review for this booking"
        super().__init__(message)
        self.booking_id = booking_id
        self.reason = reason


class ReviewEditWindowExpiredError(ReviewError):
    """
    Raised when attempting to edit a review after the edit window has expired.

    Reviews can only be edited within 24 hours of creation.
    """

    def __init__(
        self,
        review_id: int | None = None,
        hours_since_creation: float | None = None,
        edit_window_hours: int = 24,
    ) -> None:
        if review_id and hours_since_creation is not None:
            message = (
                f"Cannot edit review {review_id}. "
                f"Edit window of {edit_window_hours} hours has expired "
                f"(review created {hours_since_creation:.1f} hours ago)"
            )
        elif review_id:
            message = (
                f"Cannot edit review {review_id}. "
                f"Edit window of {edit_window_hours} hours has expired"
            )
        else:
            message = f"Review edit window of {edit_window_hours} hours has expired"
        super().__init__(message)
        self.review_id = review_id
        self.hours_since_creation = hours_since_creation
        self.edit_window_hours = edit_window_hours


class ReviewNotOwnedError(ReviewError):
    """Raised when a user attempts to modify a review they do not own."""

    def __init__(
        self,
        review_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        if review_id and user_id:
            message = f"User {user_id} does not own review {review_id}"
        elif review_id:
            message = f"User does not own review {review_id}"
        else:
            message = "User does not own this review"
        super().__init__(message)
        self.review_id = review_id
        self.user_id = user_id


class InvalidReviewContentError(ReviewError):
    """Raised when review content fails validation."""

    def __init__(self, reason: str | None = None) -> None:
        message = f"Invalid review content: {reason}" if reason else "Invalid review content"
        super().__init__(message)
        self.reason = reason
