"""
Domain exceptions for tutor_profile module.

These exceptions represent business rule violations specific to tutor profiles.
"""


class TutorProfileError(Exception):
    """Base exception for tutor profile domain errors."""

    pass


class TutorProfileNotFoundError(TutorProfileError):
    """Raised when a tutor profile is not found."""

    def __init__(self, user_id: int | None = None, profile_id: int | None = None):
        self.user_id = user_id
        self.profile_id = profile_id
        if user_id:
            message = f"Tutor profile not found for user {user_id}"
        elif profile_id:
            message = f"Tutor profile {profile_id} not found"
        else:
            message = "Tutor profile not found"
        super().__init__(message)


class TutorNotApprovedError(TutorProfileError):
    """Raised when a tutor is not yet approved for the requested action."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Tutor {user_id} is not approved")


class InvalidAvailabilityError(TutorProfileError):
    """Raised when availability data is invalid."""

    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message)


class InvalidHourlyRateError(TutorProfileError):
    """Raised when hourly rate is invalid."""

    def __init__(self, rate: float, currency: str, reason: str):
        self.rate = rate
        self.currency = currency
        self.reason = reason
        super().__init__(f"Invalid hourly rate {rate} {currency}: {reason}")


class SubjectNotAllowedError(TutorProfileError):
    """Raised when tutor attempts to teach a subject they're not approved for."""

    def __init__(self, user_id: int, subject_id: int):
        self.user_id = user_id
        self.subject_id = subject_id
        super().__init__(
            f"Tutor {user_id} is not approved to teach subject {subject_id}"
        )


class AvailabilityConflictError(TutorProfileError):
    """Raised when availability slot conflicts with existing slots or bookings."""

    def __init__(
        self,
        message: str,
        conflicting_slot: dict | None = None,
    ):
        self.conflicting_slot = conflicting_slot
        super().__init__(message)
