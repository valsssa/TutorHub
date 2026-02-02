"""
Domain exceptions for the utils module.

These exceptions represent domain-level errors that can occur during
utility operations such as health checks and service status monitoring.
They are independent of infrastructure concerns.
"""


class UtilsError(Exception):
    """Base exception for all utils-related domain errors."""

    def __init__(self, message: str = "A utils error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class HealthCheckFailedError(UtilsError):
    """Raised when a health check fails for a specific service."""

    def __init__(
        self,
        service_name: str | None = None,
        reason: str | None = None,
    ) -> None:
        if service_name and reason:
            message = f"Health check failed for {service_name}: {reason}"
        elif service_name:
            message = f"Health check failed for {service_name}"
        elif reason:
            message = f"Health check failed: {reason}"
        else:
            message = "Health check failed"
        super().__init__(message)
        self.service_name = service_name
        self.reason = reason


class ServiceUnavailableError(UtilsError):
    """Raised when a required service is unavailable."""

    def __init__(
        self,
        service_name: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        if service_name:
            message = f"Service unavailable: {service_name}"
        else:
            message = "Service unavailable"
        if retry_after:
            message = f"{message}. Retry after {retry_after} seconds."
        super().__init__(message)
        self.service_name = service_name
        self.retry_after = retry_after
