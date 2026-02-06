"""
Domain exceptions for auth module.

These exceptions represent business rule violations specific to authentication.
"""


class AuthError(Exception):
    """Base exception for authentication domain errors."""

    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class UserNotFoundError(AuthError):
    """Raised when a user is not found."""

    def __init__(self, identifier: str | int | None = None):
        self.identifier = identifier
        message = f"User not found: {identifier}" if identifier else "User not found"
        super().__init__(message)


class EmailAlreadyExistsError(AuthError):
    """Raised when attempting to register with an existing email."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email already registered: {email}")


class AccountLockedError(AuthError):
    """Raised when account is locked due to too many failed attempts."""

    def __init__(
        self,
        user_id: int,
        locked_until: str | None = None,
        reason: str = "Too many failed login attempts",
    ):
        self.user_id = user_id
        self.locked_until = locked_until
        self.reason = reason
        message = f"Account locked: {reason}"
        if locked_until:
            message += f" until {locked_until}"
        super().__init__(message)


class AccountDeactivatedError(AuthError):
    """Raised when attempting to access a deactivated account."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Account {user_id} has been deactivated")


class TokenExpiredError(AuthError):
    """Raised when a token has expired."""

    def __init__(self, token_type: str = "access"):
        self.token_type = token_type
        super().__init__(f"{token_type.capitalize()} token has expired")


class TokenInvalidError(AuthError):
    """Raised when a token is invalid."""

    def __init__(self, reason: str = "Token signature verification failed"):
        self.reason = reason
        super().__init__(f"Invalid token: {reason}")


class PasswordTooWeakError(AuthError):
    """Raised when password doesn't meet strength requirements."""

    def __init__(self, requirements: list[str] | None = None):
        self.requirements = requirements or []
        if requirements:
            message = "Password does not meet requirements: " + ", ".join(requirements)
        else:
            message = "Password does not meet strength requirements"
        super().__init__(message)


class PasswordRecentlyUsedError(AuthError):
    """Raised when user tries to reuse a recent password."""

    def __init__(self, history_count: int = 5):
        self.history_count = history_count
        super().__init__(
            f"Cannot reuse any of your last {history_count} passwords"
        )


class EmailNotVerifiedError(AuthError):
    """Raised when action requires verified email."""

    def __init__(self, email: str):
        self.email = email
        super().__init__("Email address must be verified first")


class OAuthError(AuthError):
    """Raised for OAuth flow errors."""

    def __init__(self, provider: str, reason: str):
        self.provider = provider
        self.reason = reason
        super().__init__(f"OAuth error with {provider}: {reason}")


class RateLimitExceededError(AuthError):
    """Raised when rate limit is exceeded for auth operations."""

    def __init__(
        self,
        operation: str,
        retry_after_seconds: int | None = None,
    ):
        self.operation = operation
        self.retry_after_seconds = retry_after_seconds
        message = f"Rate limit exceeded for {operation}"
        if retry_after_seconds:
            message += f". Retry after {retry_after_seconds} seconds"
        super().__init__(message)
