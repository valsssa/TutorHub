"""
Repository interfaces for admin module.

Defines the contracts for admin persistence operations.
These protocols are implemented by infrastructure layer.
"""

from datetime import datetime
from typing import Protocol

from modules.admin.domain.entities import (
    AdminActionLog,
    FeatureFlagEntity,
)
from modules.admin.domain.value_objects import (
    AdminActionType,
    AdminUserId,
    FeatureFlagId,
    TargetType,
)


class FeatureFlagRepository(Protocol):
    """
    Protocol for feature flag repository operations.

    Implementations should handle:
    - Feature flag CRUD operations
    - Flag lookups by name or ID
    - Listing and filtering flags
    """

    def get_by_id(self, flag_id: FeatureFlagId) -> FeatureFlagEntity | None:
        """
        Get a feature flag by its ID.

        Args:
            flag_id: Feature flag's unique identifier

        Returns:
            FeatureFlagEntity if found, None otherwise
        """
        ...

    def get_by_name(self, name: str) -> FeatureFlagEntity | None:
        """
        Get a feature flag by its name.

        Args:
            name: Feature flag's name (case-sensitive)

        Returns:
            FeatureFlagEntity if found, None otherwise
        """
        ...

    def get_all(
        self,
        *,
        is_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[FeatureFlagEntity]:
        """
        Get all feature flags with optional filtering.

        Args:
            is_enabled: Filter by enabled status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching feature flags
        """
        ...

    def create(self, flag: FeatureFlagEntity) -> FeatureFlagEntity:
        """
        Create a new feature flag.

        Args:
            flag: Feature flag entity to create

        Returns:
            Created feature flag with populated ID and timestamps

        Raises:
            FeatureFlagAlreadyExistsError: If flag name already exists
        """
        ...

    def update(self, flag: FeatureFlagEntity) -> FeatureFlagEntity:
        """
        Update an existing feature flag.

        Args:
            flag: Feature flag entity with updated fields

        Returns:
            Updated feature flag entity with new timestamp

        Raises:
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        ...

    def toggle(self, name: str, enabled: bool) -> FeatureFlagEntity:
        """
        Toggle a feature flag's enabled state.

        Args:
            name: Feature flag name
            enabled: New enabled state

        Returns:
            Updated feature flag entity

        Raises:
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        ...

    def delete(self, name: str) -> bool:
        """
        Delete a feature flag.

        Args:
            name: Feature flag name to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def exists(self, name: str) -> bool:
        """
        Check if a feature flag exists.

        Args:
            name: Feature flag name to check

        Returns:
            True if exists, False otherwise
        """
        ...

    def count(self, *, is_enabled: bool | None = None) -> int:
        """
        Count feature flags with optional filtering.

        Args:
            is_enabled: Filter by enabled status

        Returns:
            Count of matching feature flags
        """
        ...


class AdminActionLogRepository(Protocol):
    """
    Protocol for admin action log repository operations.

    Implementations should handle:
    - Creating audit log entries
    - Querying logs by admin, action type, or time range
    """

    def create(self, log: AdminActionLog) -> AdminActionLog:
        """
        Create a new admin action log entry.

        Args:
            log: Admin action log entity to create

        Returns:
            Created log entry with populated ID and timestamp
        """
        ...

    def get_by_admin(
        self,
        admin_id: AdminUserId,
        *,
        action_types: list[AdminActionType] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[AdminActionLog]:
        """
        Get action logs for a specific admin.

        Args:
            admin_id: Admin user's ID
            action_types: Filter by action types
            from_date: Filter by start date
            to_date: Filter by end date
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching admin action logs
        """
        ...

    def get_recent(
        self,
        *,
        action_types: list[AdminActionType] | None = None,
        target_type: TargetType | None = None,
        limit: int = 100,
    ) -> list[AdminActionLog]:
        """
        Get recent admin action logs.

        Args:
            action_types: Filter by action types
            target_type: Filter by target type
            limit: Maximum number of logs to return

        Returns:
            List of recent admin action logs (newest first)
        """
        ...

    def get_by_target(
        self,
        target_type: TargetType,
        target_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[AdminActionLog]:
        """
        Get action logs for a specific target.

        Args:
            target_type: Type of the target entity
            target_id: ID of the target entity
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of admin action logs for the target
        """
        ...

    def count_by_admin(
        self,
        admin_id: AdminUserId,
        *,
        action_types: list[AdminActionType] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """
        Count action logs for a specific admin.

        Args:
            admin_id: Admin user's ID
            action_types: Filter by action types
            from_date: Filter by start date
            to_date: Filter by end date

        Returns:
            Count of matching logs
        """
        ...

    def get_activity_summary(
        self,
        admin_id: AdminUserId,
        *,
        days: int = 30,
    ) -> dict[AdminActionType, int]:
        """
        Get activity summary for an admin over a time period.

        Args:
            admin_id: Admin user's ID
            days: Number of days to look back

        Returns:
            Dictionary mapping action types to counts
        """
        ...
