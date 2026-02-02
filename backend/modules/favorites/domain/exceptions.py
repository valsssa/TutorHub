"""
Domain exceptions for the favorites module.

These exceptions represent domain-level errors that can occur during
favorite operations. They are independent of infrastructure concerns.
"""


class FavoriteError(Exception):
    """Base exception for all favorite-related domain errors."""

    def __init__(self, message: str = "A favorite error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class FavoriteNotFoundError(FavoriteError):
    """Raised when a favorite relationship cannot be found."""

    def __init__(
        self,
        favorite_id: int | None = None,
        student_id: int | None = None,
        tutor_profile_id: int | None = None,
    ) -> None:
        if favorite_id:
            message = f"Favorite with ID {favorite_id} not found"
        elif student_id and tutor_profile_id:
            message = f"Favorite for student {student_id} and tutor profile {tutor_profile_id} not found"
        elif student_id:
            message = f"No favorites found for student {student_id}"
        else:
            message = "Favorite not found"
        super().__init__(message)
        self.favorite_id = favorite_id
        self.student_id = student_id
        self.tutor_profile_id = tutor_profile_id


class DuplicateFavoriteError(FavoriteError):
    """Raised when attempting to add a duplicate favorite."""

    def __init__(
        self,
        student_id: int | None = None,
        tutor_profile_id: int | None = None,
    ) -> None:
        if student_id and tutor_profile_id:
            message = f"Student {student_id} has already favorited tutor profile {tutor_profile_id}"
        else:
            message = "Tutor is already in favorites"
        super().__init__(message)
        self.student_id = student_id
        self.tutor_profile_id = tutor_profile_id


class InvalidFavoriteTargetError(FavoriteError):
    """Raised when the target of a favorite operation is invalid."""

    def __init__(
        self,
        tutor_profile_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        if tutor_profile_id and reason:
            message = f"Cannot favorite tutor profile {tutor_profile_id}: {reason}"
        elif tutor_profile_id:
            message = f"Invalid favorite target: tutor profile {tutor_profile_id}"
        elif reason:
            message = f"Invalid favorite target: {reason}"
        else:
            message = "Invalid favorite target"
        super().__init__(message)
        self.tutor_profile_id = tutor_profile_id
        self.reason = reason


class SelfFavoriteNotAllowedError(FavoriteError):
    """Raised when a user attempts to favorite their own tutor profile."""

    def __init__(
        self,
        user_id: int | None = None,
        tutor_profile_id: int | None = None,
    ) -> None:
        if user_id and tutor_profile_id:
            message = f"User {user_id} cannot favorite their own tutor profile {tutor_profile_id}"
        else:
            message = "Users cannot favorite their own tutor profile"
        super().__init__(message)
        self.user_id = user_id
        self.tutor_profile_id = tutor_profile_id
