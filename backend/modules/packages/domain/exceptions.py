"""
Domain exceptions for the packages module.

These exceptions represent domain-level errors that can occur during
package operations. They are independent of infrastructure concerns.
"""


class PackageError(Exception):
    """Base exception for all package-related domain errors."""

    def __init__(self, message: str = "A package error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class PackageNotFoundError(PackageError):
    """Raised when a package cannot be found."""

    def __init__(self, package_id: int | None = None) -> None:
        message = f"Package with ID {package_id} not found" if package_id else "Package not found"
        super().__init__(message)
        self.package_id = package_id


class PackageExpiredError(PackageError):
    """Raised when attempting to use an expired package."""

    def __init__(self, package_id: int | None = None, expired_at: str | None = None) -> None:
        if package_id and expired_at:
            message = f"Package {package_id} expired at {expired_at}"
        elif package_id:
            message = f"Package {package_id} has expired"
        else:
            message = "Package has expired"
        super().__init__(message)
        self.package_id = package_id
        self.expired_at = expired_at


class InsufficientSessionsError(PackageError):
    """Raised when a package does not have enough sessions remaining."""

    def __init__(
        self,
        package_id: int | None = None,
        sessions_remaining: int | None = None,
        sessions_required: int = 1,
    ) -> None:
        if package_id and sessions_remaining is not None:
            message = (
                f"Package {package_id} has {sessions_remaining} sessions remaining, "
                f"but {sessions_required} required"
            )
        elif sessions_remaining is not None:
            message = f"Only {sessions_remaining} sessions remaining, but {sessions_required} required"
        else:
            message = "Insufficient sessions remaining in package"
        super().__init__(message)
        self.package_id = package_id
        self.sessions_remaining = sessions_remaining
        self.sessions_required = sessions_required


class PackageAlreadyActiveError(PackageError):
    """Raised when attempting to activate a package that is already active."""

    def __init__(self, package_id: int | None = None) -> None:
        message = (
            f"Package {package_id} is already active" if package_id else "Package is already active"
        )
        super().__init__(message)
        self.package_id = package_id


class InvalidPackageConfigError(PackageError):
    """Raised when package configuration is invalid."""

    def __init__(self, reason: str | None = None) -> None:
        message = f"Invalid package configuration: {reason}" if reason else "Invalid package configuration"
        super().__init__(message)
        self.reason = reason


class PackageNotOwnedError(PackageError):
    """Raised when a user attempts to access a package they do not own."""

    def __init__(
        self,
        package_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        if package_id and user_id:
            message = f"User {user_id} does not own package {package_id}"
        elif package_id:
            message = f"User does not own package {package_id}"
        else:
            message = "User does not own this package"
        super().__init__(message)
        self.package_id = package_id
        self.user_id = user_id


class PricingOptionNotFoundError(PackageError):
    """Raised when a pricing option cannot be found."""

    def __init__(self, pricing_option_id: int | None = None) -> None:
        message = (
            f"Pricing option with ID {pricing_option_id} not found"
            if pricing_option_id
            else "Pricing option not found"
        )
        super().__init__(message)
        self.pricing_option_id = pricing_option_id


class PricingOptionNotActiveError(PackageError):
    """Raised when attempting to use an inactive pricing option."""

    def __init__(self, pricing_option_id: int | None = None) -> None:
        message = (
            f"Pricing option {pricing_option_id} is not active"
            if pricing_option_id
            else "Pricing option is not active"
        )
        super().__init__(message)
        self.pricing_option_id = pricing_option_id
