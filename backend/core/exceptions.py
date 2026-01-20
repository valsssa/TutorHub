"""Custom exception classes."""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: dict | None = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", details: dict | None = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=422, details=details)


class DuplicateError(AppException):
    """Raised when trying to create a duplicate resource."""

    def __init__(self, resource: str, field: str, value: Any):
        message = f"{resource} with {field}='{value}' already exists"
        super().__init__(message, status_code=400, details={"field": field, "value": value})


class BusinessRuleError(AppException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, rule: str | None = None):
        details = {"rule": rule} if rule else {}
        super().__init__(message, status_code=400, details=details)
