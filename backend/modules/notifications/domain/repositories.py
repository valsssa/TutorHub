"""
Repository interface for notifications module.

Defines the contract for notification persistence operations.
"""

from datetime import datetime
from typing import Protocol

from modules.notifications.domain.entities import (
    NotificationBatch,
    NotificationDeliveryAttempt,
    NotificationEntity,
    NotificationPreference,
)
from modules.notifications.domain.value_objects import (
    DeliveryChannel,
    NotificationCategory,
    NotificationType,
)


class NotificationRepository(Protocol):
    """
    Protocol for notification repository operations.

    Implementations should handle:
    - Notification CRUD operations
    - User-based queries
    - Read/unread status management
    """

    def get_by_id(self, notification_id: int) -> NotificationEntity | None:
        """
        Get a notification by its ID.

        Args:
            notification_id: Notification's unique identifier

        Returns:
            NotificationEntity if found, None otherwise
        """
        ...

    def get_by_user(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
        notification_type: NotificationType | None = None,
        is_read: bool | None = None,
        include_dismissed: bool = False,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[NotificationEntity]:
        """
        Get notifications for a user with optional filtering.

        Args:
            user_id: User's ID
            category: Filter by category
            notification_type: Filter by type
            is_read: Filter by read status
            include_dismissed: Include dismissed notifications
            from_date: Filter by start date
            to_date: Filter by end date
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching notifications
        """
        ...

    def create(self, notification: NotificationEntity) -> NotificationEntity:
        """
        Create a new notification.

        Args:
            notification: Notification entity to create

        Returns:
            Created notification with populated ID
        """
        ...

    def update(self, notification: NotificationEntity) -> NotificationEntity:
        """
        Update an existing notification.

        Args:
            notification: Notification entity with updated fields

        Returns:
            Updated notification entity
        """
        ...

    def mark_as_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if marked, False if not found or not owned by user
        """
        ...

    def mark_all_as_read(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
    ) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User's ID
            category: Optional category filter

        Returns:
            Number of notifications marked as read
        """
        ...

    def dismiss(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """
        Dismiss a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if dismissed, False if not found or not owned by user
        """
        ...

    def delete(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """
        Delete a notification (hard delete).

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found or not owned by user
        """
        ...

    def count_unread(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
    ) -> int:
        """
        Count unread notifications for a user.

        Args:
            user_id: User's ID
            category: Optional category filter

        Returns:
            Count of unread notifications
        """
        ...

    def count_by_user(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
        is_read: bool | None = None,
        include_dismissed: bool = False,
    ) -> int:
        """
        Count notifications for a user.

        Args:
            user_id: User's ID
            category: Optional category filter
            is_read: Optional read status filter
            include_dismissed: Include dismissed notifications

        Returns:
            Total count of matching notifications
        """
        ...

    def get_recent_by_type(
        self,
        user_id: int,
        notification_type: NotificationType,
        *,
        since: datetime,
    ) -> list[NotificationEntity]:
        """
        Get recent notifications of a specific type.

        Useful for deduplication and rate limiting.

        Args:
            user_id: User's ID
            notification_type: Type of notification
            since: Start datetime

        Returns:
            List of matching notifications
        """
        ...

    def delete_expired(self) -> int:
        """
        Delete all expired notifications.

        Returns:
            Number of notifications deleted
        """
        ...


class NotificationPreferenceRepository(Protocol):
    """
    Protocol for notification preference repository operations.

    Implementations should handle:
    - Preference CRUD operations
    - Default preference creation
    """

    def get_by_user(self, user_id: int) -> NotificationPreference | None:
        """
        Get notification preferences for a user.

        Args:
            user_id: User's ID

        Returns:
            NotificationPreference if found, None otherwise
        """
        ...

    def get_or_create(self, user_id: int) -> NotificationPreference:
        """
        Get notification preferences for a user, creating defaults if needed.

        Args:
            user_id: User's ID

        Returns:
            NotificationPreference (existing or newly created)
        """
        ...

    def update(self, preference: NotificationPreference) -> NotificationPreference:
        """
        Update notification preferences.

        Args:
            preference: Preference entity with updated fields

        Returns:
            Updated preference entity
        """
        ...

    def get_users_with_channel_enabled(
        self,
        channel: DeliveryChannel,
        *,
        notification_type: NotificationType | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> list[int]:
        """
        Get user IDs with a specific channel enabled.

        Useful for batch notifications.

        Args:
            channel: Delivery channel to check
            notification_type: Optional type to check
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of user IDs
        """
        ...


class NotificationDeliveryRepository(Protocol):
    """
    Protocol for notification delivery tracking operations.

    Implementations should handle:
    - Delivery attempt tracking
    - Retry management
    """

    def create_attempt(
        self,
        attempt: NotificationDeliveryAttempt,
    ) -> NotificationDeliveryAttempt:
        """
        Record a delivery attempt.

        Args:
            attempt: Delivery attempt entity

        Returns:
            Created attempt with populated ID
        """
        ...

    def get_attempts_for_notification(
        self,
        notification_id: int,
    ) -> list[NotificationDeliveryAttempt]:
        """
        Get all delivery attempts for a notification.

        Args:
            notification_id: Notification ID

        Returns:
            List of delivery attempts
        """
        ...

    def get_failed_attempts_for_retry(
        self,
        *,
        max_retry_count: int = 3,
        older_than_minutes: int = 5,
        limit: int = 100,
    ) -> list[NotificationDeliveryAttempt]:
        """
        Get failed delivery attempts eligible for retry.

        Args:
            max_retry_count: Maximum retry count threshold
            older_than_minutes: Only attempts older than this
            limit: Maximum number to return

        Returns:
            List of delivery attempts to retry
        """
        ...

    def update_attempt(
        self,
        attempt: NotificationDeliveryAttempt,
    ) -> NotificationDeliveryAttempt:
        """
        Update a delivery attempt record.

        Args:
            attempt: Delivery attempt with updated fields

        Returns:
            Updated delivery attempt
        """
        ...


class NotificationBatchRepository(Protocol):
    """
    Protocol for notification batch operations.

    Implementations should handle:
    - Batch CRUD operations
    - Progress tracking
    """

    def create(self, batch: NotificationBatch) -> NotificationBatch:
        """
        Create a new notification batch.

        Args:
            batch: Batch entity to create

        Returns:
            Created batch with populated ID
        """
        ...

    def get_by_id(self, batch_id: int) -> NotificationBatch | None:
        """
        Get a batch by its ID.

        Args:
            batch_id: Batch's unique identifier

        Returns:
            NotificationBatch if found, None otherwise
        """
        ...

    def update(self, batch: NotificationBatch) -> NotificationBatch:
        """
        Update a batch record.

        Args:
            batch: Batch entity with updated fields

        Returns:
            Updated batch entity
        """
        ...

    def get_pending_batches(self) -> list[NotificationBatch]:
        """
        Get all pending batches ready for processing.

        Returns:
            List of pending batches
        """
        ...

    def increment_sent_count(self, batch_id: int) -> None:
        """
        Increment the sent count for a batch.

        Args:
            batch_id: Batch ID
        """
        ...

    def increment_failed_count(self, batch_id: int) -> None:
        """
        Increment the failed count for a batch.

        Args:
            batch_id: Batch ID
        """
        ...
