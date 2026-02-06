"""
Domain exceptions for admin module.

These exceptions represent business rule violations specific to admin operations.
"""


class AdminError(Exception):
    """Base exception for admin domain errors."""

    pass


class UnauthorizedAdminAccessError(AdminError):
    """Raised when a user attempts to access admin resources without authorization."""

    def __init__(
        self,
        user_id: int | None = None,
        resource: str | None = None,
        message: str | None = None,
    ):
        self.user_id = user_id
        self.resource = resource
        if message:
            super().__init__(message)
        elif user_id and resource:
            super().__init__(
                f"User {user_id} is not authorized to access admin resource: {resource}"
            )
        elif user_id:
            super().__init__(f"User {user_id} is not authorized for admin access")
        else:
            super().__init__("Unauthorized admin access")


class FeatureFlagNotFoundError(AdminError):
    """Raised when a feature flag is not found."""

    def __init__(self, flag_name: str | None = None, flag_id: int | None = None):
        self.flag_name = flag_name
        self.flag_id = flag_id
        if flag_name:
            super().__init__(f"Feature flag not found: {flag_name}")
        elif flag_id:
            super().__init__(f"Feature flag with ID {flag_id} not found")
        else:
            super().__init__("Feature flag not found")


class InvalidFeatureFlagError(AdminError):
    """Raised when feature flag data is invalid."""

    def __init__(
        self,
        reason: str,
        flag_name: str | None = None,
    ):
        self.reason = reason
        self.flag_name = flag_name
        message = (
            f"Invalid feature flag '{flag_name}': {reason}"
            if flag_name
            else f"Invalid feature flag: {reason}"
        )
        super().__init__(message)


class AdminActionNotAllowedError(AdminError):
    """Raised when an admin action is not permitted."""

    def __init__(
        self,
        action: str,
        reason: str | None = None,
        admin_id: int | None = None,
        target_id: int | None = None,
    ):
        self.action = action
        self.reason = reason
        self.admin_id = admin_id
        self.target_id = target_id

        if reason:
            message = f"Admin action '{action}' not allowed: {reason}"
        else:
            message = f"Admin action '{action}' is not allowed"

        super().__init__(message)


class FeatureFlagAlreadyExistsError(AdminError):
    """Raised when attempting to create a feature flag that already exists."""

    def __init__(self, flag_name: str):
        self.flag_name = flag_name
        super().__init__(f"Feature flag already exists: {flag_name}")


class LastAdminRemovalError(AdminError):
    """Raised when attempting to remove or demote the last admin user."""

    def __init__(self, user_id: int, action: str = "remove"):
        self.user_id = user_id
        self.action = action
        super().__init__(
            f"Cannot {action} user {user_id}: would leave platform without any admin"
        )


class AdminSelfModificationError(AdminError):
    """Raised when an admin attempts a prohibited self-modification."""

    def __init__(self, action: str, admin_id: int):
        self.action = action
        self.admin_id = admin_id
        super().__init__(f"Admin {admin_id} cannot {action} their own account")
