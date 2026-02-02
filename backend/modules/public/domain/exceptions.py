"""
Domain exceptions for public module.

These exceptions represent business rule violations specific to public API access.
"""


class PublicApiError(Exception):
    """Base exception for public API domain errors."""

    pass


class TutorProfileNotPublicError(PublicApiError):
    """Raised when attempting to access a tutor profile that is not public."""

    def __init__(self, tutor_id: int | None = None):
        self.tutor_id = tutor_id
        if tutor_id:
            message = f"Tutor profile {tutor_id} is not publicly accessible"
        else:
            message = "Tutor profile is not publicly accessible"
        super().__init__(message)


class InvalidSearchParametersError(PublicApiError):
    """Raised when search parameters are invalid or malformed."""

    def __init__(
        self,
        parameter: str | None = None,
        reason: str | None = None,
    ):
        self.parameter = parameter
        self.reason = reason
        if parameter and reason:
            message = f"Invalid search parameter '{parameter}': {reason}"
        elif parameter:
            message = f"Invalid search parameter: {parameter}"
        elif reason:
            message = f"Invalid search parameters: {reason}"
        else:
            message = "Invalid search parameters provided"
        super().__init__(message)


class RateLimitExceededError(PublicApiError):
    """Raised when rate limit is exceeded for public API operations."""

    def __init__(
        self,
        operation: str = "search",
        retry_after_seconds: int | None = None,
    ):
        self.operation = operation
        self.retry_after_seconds = retry_after_seconds
        message = f"Rate limit exceeded for {operation}"
        if retry_after_seconds:
            message += f". Retry after {retry_after_seconds} seconds"
        super().__init__(message)
