"""
Domain entities for notifications module.

These are pure data classes representing the core notification domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from modules.notifications.domain.value_objects import (
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationType,
)


@dataclass
class NotificationEntity:
    """
    Core notification domain entity.

    Represents a single notification sent to a user.
    """

    id: int | None
    user_id: int
    type: NotificationType
    title: str
    message: str

    # Status
    is_read: bool = False
    read_at: datetime | None = None
    dismissed_at: datetime | None = None

    # Optional fields
    category: NotificationCategory | None = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    link: str | None = None
    action_url: str | None = None
    action_label: str | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime | None = None
    sent_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set category based on type if not provided."""
        if self.category is None:
            self.category = NotificationCategory.from_notification_type(self.type)

    @property
    def is_dismissed(self) -> bool:
        """Check if notification has been dismissed."""
        return self.dismissed_at is not None

    @property
    def is_actionable(self) -> bool:
        """Check if notification has an action URL."""
        return self.action_url is not None

    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_visible(self) -> bool:
        """Check if notification should be visible to user."""
        return not self.is_dismissed and not self.is_expired

    @property
    def is_urgent(self) -> bool:
        """Check if this is an urgent notification."""
        return self.priority == NotificationPriority.URGENT

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def dismiss(self) -> None:
        """Dismiss (hide) the notification."""
        if self.dismissed_at is None:
            self.dismissed_at = datetime.utcnow()


@dataclass
class NotificationPreference:
    """
    User notification preferences entity.

    Controls how and when a user receives notifications.
    """

    id: int | None
    user_id: int

    # Channel preferences
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True

    # Type preferences
    session_reminders_enabled: bool = True
    booking_requests_enabled: bool = True
    learning_nudges_enabled: bool = True
    review_prompts_enabled: bool = True
    achievements_enabled: bool = True
    marketing_enabled: bool = False

    # Quiet hours (stored as time strings HH:MM)
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None

    # Scheduling preferences
    preferred_notification_time: str | None = None  # HH:MM format

    # Rate limiting
    max_daily_notifications: int | None = None
    max_weekly_nudges: int | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_channel_enabled(self, channel: DeliveryChannel) -> bool:
        """Check if a specific delivery channel is enabled."""
        channel_map = {
            DeliveryChannel.EMAIL: self.email_enabled,
            DeliveryChannel.PUSH: self.push_enabled,
            DeliveryChannel.SMS: self.sms_enabled,
            DeliveryChannel.IN_APP: self.in_app_enabled,
        }
        return channel_map.get(channel, False)

    def is_notification_type_enabled(self, notification_type: NotificationType) -> bool:
        """Check if a specific notification type is enabled."""
        type_checks = {
            NotificationType.BOOKING_REMINDER: self.session_reminders_enabled,
            NotificationType.BOOKING_REQUEST: self.booking_requests_enabled,
            NotificationType.LEARNING_NUDGE: self.learning_nudges_enabled,
            NotificationType.REVIEW_PROMPT: self.review_prompts_enabled,
            NotificationType.ACHIEVEMENT_UNLOCKED: self.achievements_enabled,
            NotificationType.SYSTEM_ANNOUNCEMENT: self.marketing_enabled,
        }
        # Default to enabled for types not explicitly configured
        return type_checks.get(notification_type, True)

    def is_in_quiet_hours(self, current_time: str) -> bool:
        """
        Check if current time is within quiet hours.

        Args:
            current_time: Current time in HH:MM format

        Returns:
            True if in quiet hours, False otherwise
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 - 07:00)
        if start > end:
            return current_time >= start or current_time <= end

        return start <= current_time <= end

    def can_receive_notification(
        self,
        notification_type: NotificationType,
        channel: DeliveryChannel,
        current_time: str | None = None,
    ) -> bool:
        """
        Check if user can receive a specific notification via a channel.

        Args:
            notification_type: Type of notification
            channel: Delivery channel
            current_time: Current time in HH:MM format (for quiet hours check)

        Returns:
            True if notification can be sent, False otherwise
        """
        # Check channel preference
        if not self.is_channel_enabled(channel):
            return False

        # Check notification type preference
        if not self.is_notification_type_enabled(notification_type):
            return False

        # Check quiet hours for non-urgent channels
        if current_time and channel in (DeliveryChannel.EMAIL, DeliveryChannel.PUSH):
            if self.is_in_quiet_hours(current_time):
                return False

        return True


@dataclass
class NotificationDeliveryAttempt:
    """
    Record of a notification delivery attempt.

    Tracks delivery attempts for auditing and retry purposes.
    """

    id: int | None
    notification_id: int
    channel: DeliveryChannel
    attempted_at: datetime
    success: bool
    message_id: str | None = None
    error_message: str | None = None
    retry_count: int = 0

    @property
    def is_retriable(self) -> bool:
        """Check if this delivery can be retried."""
        return not self.success and self.retry_count < 3


@dataclass
class NotificationBatch:
    """
    Batch of notifications for bulk operations.

    Used for sending multiple notifications at once (e.g., announcements).
    """

    id: int | None
    name: str
    notification_type: NotificationType
    title: str
    message: str
    total_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime | None = None
    completed_at: datetime | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete."""
        return self.status in ("completed", "failed")

    @property
    def success_rate(self) -> float:
        """Calculate the success rate for the batch."""
        if self.sent_count + self.failed_count == 0:
            return 0.0
        return self.sent_count / (self.sent_count + self.failed_count)

    @property
    def progress_percentage(self) -> float:
        """Calculate the progress percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.sent_count + self.failed_count) / self.total_count * 100
