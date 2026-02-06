"""
Value objects for admin module.

These are immutable objects that represent domain concepts with validation.
"""

import re
from enum import Enum
from typing import NewType

# Type-safe ID wrappers
AdminUserId = NewType("AdminUserId", int)
FeatureFlagId = NewType("FeatureFlagId", int)


class PermissionLevel(str, Enum):
    """Admin permission levels."""

    READ_ONLY = "read_only"
    STANDARD = "standard"
    FULL_ACCESS = "full_access"

    def can_read(self) -> bool:
        """Check if permission level allows read operations."""
        return True  # All levels can read

    def can_write(self) -> bool:
        """Check if permission level allows write operations."""
        return self in (PermissionLevel.STANDARD, PermissionLevel.FULL_ACCESS)

    def can_delete(self) -> bool:
        """Check if permission level allows delete operations."""
        return self == PermissionLevel.FULL_ACCESS

    def can_manage_admins(self) -> bool:
        """Check if permission level allows managing other admins."""
        return self == PermissionLevel.FULL_ACCESS


class FeatureFlagName:
    """
    Value object representing a validated feature flag name.

    Feature flag names must:
    - Be between 1 and 100 characters
    - Contain only lowercase letters, numbers, and underscores
    - Start with a letter
    """

    MIN_LENGTH = 1
    MAX_LENGTH = 100
    PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

    def __init__(self, value: str):
        self._validate(value)
        self._value = value

    def _validate(self, value: str) -> None:
        """Validate feature flag name."""
        if not value:
            raise ValueError("Feature flag name cannot be empty")

        if len(value) < self.MIN_LENGTH:
            raise ValueError(
                f"Feature flag name must be at least {self.MIN_LENGTH} character(s)"
            )

        if len(value) > self.MAX_LENGTH:
            raise ValueError(
                f"Feature flag name cannot exceed {self.MAX_LENGTH} characters"
            )

        if not self.PATTERN.match(value):
            raise ValueError(
                "Feature flag name must start with a letter and contain only "
                "lowercase letters, numbers, and underscores"
            )

    @property
    def value(self) -> str:
        """Get the flag name value."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"FeatureFlagName({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FeatureFlagName):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return False

    def __hash__(self) -> int:
        return hash(self._value)


class FeatureFlagState(str, Enum):
    """Feature flag states matching core/feature_flags.py FeatureState."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    PERCENTAGE = "percentage"
    ALLOWLIST = "allowlist"
    DENYLIST = "denylist"

    def is_globally_enabled(self) -> bool:
        """Check if flag is enabled for all users."""
        return self == FeatureFlagState.ENABLED

    def is_globally_disabled(self) -> bool:
        """Check if flag is disabled for all users."""
        return self == FeatureFlagState.DISABLED

    def requires_user_context(self) -> bool:
        """Check if flag evaluation requires user context."""
        return self in (
            FeatureFlagState.PERCENTAGE,
            FeatureFlagState.ALLOWLIST,
            FeatureFlagState.DENYLIST,
        )


class AdminActionType(str, Enum):
    """Types of admin actions for audit logging."""

    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    USER_ROLE_CHANGE = "user_role_change"

    # Tutor management
    TUTOR_APPROVE = "tutor_approve"
    TUTOR_REJECT = "tutor_reject"

    # Feature flag management
    FEATURE_FLAG_CREATE = "feature_flag_create"
    FEATURE_FLAG_UPDATE = "feature_flag_update"
    FEATURE_FLAG_DELETE = "feature_flag_delete"
    FEATURE_FLAG_TOGGLE = "feature_flag_toggle"

    # System operations
    CACHE_INVALIDATE = "cache_invalidate"
    DATA_PURGE = "data_purge"
    DATA_RESTORE = "data_restore"


class TargetType(str, Enum):
    """Types of targets for admin actions."""

    USER = "user"
    TUTOR_PROFILE = "tutor_profile"
    FEATURE_FLAG = "feature_flag"
    BOOKING = "booking"
    SYSTEM = "system"


class Percentage:
    """
    Value object representing a validated percentage (0-100).

    Used for feature flag rollout percentages.
    """

    def __init__(self, value: int):
        self._validate(value)
        self._value = value

    def _validate(self, value: int) -> None:
        """Validate percentage value."""
        if not isinstance(value, int):
            raise ValueError("Percentage must be an integer")
        if value < 0 or value > 100:
            raise ValueError("Percentage must be between 0 and 100")

    @property
    def value(self) -> int:
        """Get the percentage value."""
        return self._value

    def __int__(self) -> int:
        return self._value

    def __str__(self) -> str:
        return f"{self._value}%"

    def __repr__(self) -> str:
        return f"Percentage({self._value})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Percentage):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __hash__(self) -> int:
        return hash(self._value)
