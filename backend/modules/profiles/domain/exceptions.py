"""
Domain exceptions for profiles module.

These exceptions represent business rule violations specific to user profiles.
"""


class ProfileError(Exception):
    """Base exception for profile domain errors."""

    pass


class ProfileNotFoundError(ProfileError):
    """Raised when a profile is not found."""

    def __init__(self, identifier: int | str | None = None, by_user_id: bool = False):
        self.identifier = identifier
        self.by_user_id = by_user_id
        if identifier:
            if by_user_id:
                message = f"Profile not found for user: {identifier}"
            else:
                message = f"Profile not found: {identifier}"
        else:
            message = "Profile not found"
        super().__init__(message)


class InvalidProfileDataError(ProfileError):
    """Raised when profile data is invalid."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid profile data for '{field}': {reason}")


class AvatarUploadError(ProfileError):
    """Raised when avatar upload fails."""

    def __init__(
        self,
        reason: str,
        user_id: int | None = None,
        original_error: Exception | None = None,
    ):
        self.reason = reason
        self.user_id = user_id
        self.original_error = original_error
        message = f"Avatar upload failed: {reason}"
        if user_id:
            message = f"Avatar upload failed for user {user_id}: {reason}"
        super().__init__(message)


class InvalidTimezoneError(ProfileError):
    """Raised when an invalid IANA timezone is provided."""

    def __init__(self, timezone: str):
        self.timezone = timezone
        super().__init__(
            f"Invalid IANA timezone: '{timezone}'. "
            "Please provide a valid timezone identifier (e.g., 'America/New_York', 'UTC')"
        )
