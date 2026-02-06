"""
Domain entities for admin module.

These are pure data classes representing the core admin domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from modules.admin.domain.value_objects import (
    AdminActionType,
    AdminUserId,
    FeatureFlagId,
    FeatureFlagState,
    TargetType,
)


@dataclass
class FeatureFlagEntity:
    """
    Domain entity representing a feature flag.

    Feature flags control the rollout of features to users, supporting
    various strategies: global enable/disable, percentage rollout,
    and user allowlists/denylists.
    """

    id: FeatureFlagId | None
    name: str
    is_enabled: bool = False
    state: FeatureFlagState = FeatureFlagState.DISABLED
    description: str = ""

    # Rollout configuration
    percentage: int = 0  # 0-100, used when state is PERCENTAGE
    allowlist: list[str] = field(default_factory=list)  # User IDs when ALLOWLIST
    denylist: list[str] = field(default_factory=list)  # User IDs when DENYLIST

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_globally_enabled(self) -> bool:
        """Check if flag is enabled for all users."""
        return self.state == FeatureFlagState.ENABLED

    @property
    def is_globally_disabled(self) -> bool:
        """Check if flag is disabled for all users."""
        return self.state == FeatureFlagState.DISABLED

    @property
    def requires_user_context(self) -> bool:
        """Check if evaluating this flag requires user context."""
        return self.state in (
            FeatureFlagState.PERCENTAGE,
            FeatureFlagState.ALLOWLIST,
            FeatureFlagState.DENYLIST,
        )

    def enable(self) -> None:
        """Enable flag for all users."""
        self.state = FeatureFlagState.ENABLED
        self.is_enabled = True

    def disable(self) -> None:
        """Disable flag for all users."""
        self.state = FeatureFlagState.DISABLED
        self.is_enabled = False

    def set_percentage(self, percentage: int) -> None:
        """Set flag to percentage rollout mode."""
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        self.state = FeatureFlagState.PERCENTAGE
        self.percentage = percentage
        self.is_enabled = percentage > 0

    def add_to_allowlist(self, user_ids: list[str]) -> None:
        """Add users to allowlist."""
        self.state = FeatureFlagState.ALLOWLIST
        self.allowlist = list(set(self.allowlist + user_ids))
        self.is_enabled = len(self.allowlist) > 0

    def remove_from_allowlist(self, user_ids: list[str]) -> None:
        """Remove users from allowlist."""
        self.allowlist = [u for u in self.allowlist if u not in user_ids]

    def add_to_denylist(self, user_ids: list[str]) -> None:
        """Add users to denylist."""
        self.state = FeatureFlagState.DENYLIST
        self.denylist = list(set(self.denylist + user_ids))

    def remove_from_denylist(self, user_ids: list[str]) -> None:
        """Remove users from denylist."""
        self.denylist = [u for u in self.denylist if u not in user_ids]


@dataclass
class AdminActionLog:
    """
    Domain entity representing an admin action log entry.

    Records all administrative actions for audit purposes, including
    who performed the action, what was affected, and when.
    """

    id: int | None
    admin_id: AdminUserId
    action: AdminActionType
    target_type: TargetType
    target_id: str | None = None  # Can be int or string (e.g., feature flag name)

    # Action details
    details: dict[str, Any] = field(default_factory=dict)
    previous_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None

    # Context
    ip_address: str | None = None
    user_agent: str | None = None

    # Timestamp
    created_at: datetime | None = None

    @property
    def has_state_change(self) -> bool:
        """Check if action recorded a state change."""
        return self.previous_state is not None or self.new_state is not None

    def get_detail(self, key: str, default: Any = None) -> Any:
        """Get a detail value by key."""
        return self.details.get(key, default)

    def set_detail(self, key: str, value: Any) -> None:
        """Set a detail value."""
        self.details[key] = value

    def record_state_change(
        self,
        previous: dict[str, Any] | None,
        new: dict[str, Any] | None,
    ) -> None:
        """Record before/after state for the action."""
        self.previous_state = previous
        self.new_state = new


@dataclass
class AdminUserSummary:
    """
    Summary information about an admin user.

    Used for displaying admin lists and action attribution.
    """

    id: AdminUserId
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool = True

    @property
    def full_name(self) -> str:
        """Get the admin's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split("@")[0]

    @property
    def display_name(self) -> str:
        """Get display name (full name or email prefix)."""
        return self.full_name


@dataclass
class FeatureFlagAuditEntry:
    """
    Audit entry specific to feature flag changes.

    Tracks who changed what and when for feature flags.
    """

    flag_name: str
    admin_id: AdminUserId
    action: str  # 'created', 'updated', 'deleted', 'enabled', 'disabled', etc.
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    timestamp: datetime | None = None

    @property
    def is_creation(self) -> bool:
        """Check if this is a flag creation."""
        return self.action == "created"

    @property
    def is_deletion(self) -> bool:
        """Check if this is a flag deletion."""
        return self.action == "deleted"

    @property
    def is_toggle(self) -> bool:
        """Check if this is a flag toggle (enable/disable)."""
        return self.action in ("enabled", "disabled")
