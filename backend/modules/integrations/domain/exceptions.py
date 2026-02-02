"""
Domain exceptions for integrations module.

These exceptions represent business rule violations specific to third-party integrations.
"""


class IntegrationError(Exception):
    """Base exception for integration domain errors."""

    def __init__(self, message: str = "Integration error occurred"):
        self.message = message
        super().__init__(message)


class IntegrationNotFoundError(IntegrationError):
    """Raised when an integration is not found."""

    def __init__(
        self,
        integration_id: int | str | None = None,
        integration_type: str | None = None,
    ):
        self.integration_id = integration_id
        self.integration_type = integration_type
        if integration_id:
            message = f"Integration not found: {integration_id}"
        elif integration_type:
            message = f"Integration of type '{integration_type}' not found"
        else:
            message = "Integration not found"
        super().__init__(message)


class IntegrationAuthError(IntegrationError):
    """Raised when integration authentication fails."""

    def __init__(
        self,
        provider: str,
        reason: str = "Authentication failed",
    ):
        self.provider = provider
        self.reason = reason
        message = f"{provider} authentication error: {reason}"
        super().__init__(message)


class IntegrationConnectionError(IntegrationError):
    """Raised when connection to integration provider fails."""

    def __init__(
        self,
        provider: str,
        reason: str = "Connection failed",
        retryable: bool = True,
    ):
        self.provider = provider
        self.reason = reason
        self.retryable = retryable
        message = f"Failed to connect to {provider}: {reason}"
        super().__init__(message)


class VideoMeetingError(IntegrationError):
    """Raised for video meeting provider errors."""

    def __init__(
        self,
        provider: str,
        reason: str,
        booking_id: int | None = None,
        retryable: bool = False,
    ):
        self.provider = provider
        self.reason = reason
        self.booking_id = booking_id
        self.retryable = retryable
        if booking_id:
            message = f"Video meeting error ({provider}) for booking {booking_id}: {reason}"
        else:
            message = f"Video meeting error ({provider}): {reason}"
        super().__init__(message)


class CalendarSyncError(IntegrationError):
    """Raised when calendar synchronization fails."""

    def __init__(
        self,
        operation: str,
        reason: str,
        event_id: str | None = None,
        retryable: bool = True,
    ):
        self.operation = operation
        self.reason = reason
        self.event_id = event_id
        self.retryable = retryable
        if event_id:
            message = f"Calendar sync failed ({operation}) for event {event_id}: {reason}"
        else:
            message = f"Calendar sync failed ({operation}): {reason}"
        super().__init__(message)


class OAuthFlowError(IntegrationError):
    """Raised for OAuth flow errors."""

    def __init__(
        self,
        provider: str,
        stage: str,
        reason: str,
    ):
        self.provider = provider
        self.stage = stage
        self.reason = reason
        message = f"OAuth flow error ({provider}) at {stage}: {reason}"
        super().__init__(message)


class TokenExpiredError(IntegrationError):
    """Raised when an OAuth token has expired and refresh failed."""

    def __init__(
        self,
        provider: str,
        user_id: int | None = None,
    ):
        self.provider = provider
        self.user_id = user_id
        message = f"{provider} token has expired"
        if user_id:
            message += f" for user {user_id}"
        message += ". Please reconnect the integration."
        super().__init__(message)


class RateLimitError(IntegrationError):
    """Raised when rate limit is exceeded for an integration."""

    def __init__(
        self,
        provider: str,
        retry_after_seconds: int | None = None,
    ):
        self.provider = provider
        self.retry_after_seconds = retry_after_seconds
        message = f"{provider} rate limit exceeded"
        if retry_after_seconds:
            message += f". Retry after {retry_after_seconds} seconds"
        super().__init__(message)


class IntegrationDisabledError(IntegrationError):
    """Raised when trying to use a disabled integration."""

    def __init__(
        self,
        provider: str,
        reason: str = "Integration is not configured",
    ):
        self.provider = provider
        self.reason = reason
        message = f"{provider} integration is disabled: {reason}"
        super().__init__(message)
