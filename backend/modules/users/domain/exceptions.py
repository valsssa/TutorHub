"""
Domain exceptions for the users module.

These exceptions represent domain-level errors that can occur during
user operations. They are independent of infrastructure concerns.
"""


class UserError(Exception):
    """Base exception for all user-related domain errors."""

    def __init__(self, message: str = "A user error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(UserError):
    """Raised when a user cannot be found."""

    def __init__(
        self,
        user_id: int | None = None,
        email: str | None = None,
    ) -> None:
        if user_id:
            message = f"User with ID {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        else:
            message = "User not found"
        super().__init__(message)
        self.user_id = user_id
        self.email = email


class DuplicateEmailError(UserError):
    """Raised when attempting to create a user with an existing email."""

    def __init__(self, email: str | None = None) -> None:
        if email:
            message = f"User with email {email} already exists"
        else:
            message = "Email already in use"
        super().__init__(message)
        self.email = email


class InvalidUserStateError(UserError):
    """Raised when a user operation is invalid for the current state."""

    def __init__(
        self,
        user_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        if user_id and reason:
            message = f"Invalid state for user {user_id}: {reason}"
        elif reason:
            message = f"Invalid user state: {reason}"
        else:
            message = "Invalid user state"
        super().__init__(message)
        self.user_id = user_id
        self.reason = reason


class UserDeactivatedError(UserError):
    """Raised when attempting to operate on a deactivated user."""

    def __init__(self, user_id: int | None = None) -> None:
        if user_id:
            message = f"User {user_id} is deactivated"
        else:
            message = "User is deactivated"
        super().__init__(message)
        self.user_id = user_id


class InvalidCurrencyError(UserError):
    """Raised when an invalid currency code is provided."""

    def __init__(self, currency: str | None = None) -> None:
        if currency:
            message = f"Invalid or unsupported currency code: {currency}"
        else:
            message = "Invalid currency code"
        super().__init__(message)
        self.currency = currency


class InvalidTimezoneError(UserError):
    """Raised when an invalid timezone is provided."""

    def __init__(self, timezone: str | None = None) -> None:
        if timezone:
            message = f"Invalid IANA timezone: {timezone}"
        else:
            message = "Invalid timezone"
        super().__init__(message)
        self.timezone = timezone


class AvatarError(UserError):
    """Base exception for avatar-related errors."""

    pass


class AvatarUploadError(AvatarError):
    """Raised when avatar upload fails."""

    def __init__(
        self,
        user_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        if user_id and reason:
            message = f"Failed to upload avatar for user {user_id}: {reason}"
        elif reason:
            message = f"Avatar upload failed: {reason}"
        else:
            message = "Avatar upload failed"
        super().__init__(message)
        self.user_id = user_id
        self.reason = reason


class InvalidAvatarError(AvatarError):
    """Raised when the provided avatar image is invalid."""

    def __init__(self, reason: str | None = None) -> None:
        if reason:
            message = f"Invalid avatar: {reason}"
        else:
            message = "Invalid avatar image"
        super().__init__(message)
        self.reason = reason
