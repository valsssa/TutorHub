"""
Value objects for notifications module.

These are immutable domain primitives that represent notification-related concepts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import NewType


# Type-safe identifier for notifications
NotificationId = NewType("NotificationId", int)


class NotificationType(str, Enum):
    """
    Standard notification types.

    Categorized by domain:
    - Booking related: booking_*
    - Payment related: payment_*, payout_*, refund_*
    - Message related: new_message
    - Review related: *_review, review_*
    - System/Account: account_*, system_*, achievement_*, learning_*
    - Package related: package_*
    """

    # Booking related
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_REQUEST = "booking_request"
    BOOKING_COMPLETED = "booking_completed"

    # Payment related
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    PAYOUT_COMPLETED = "payout_completed"
    REFUND_PROCESSED = "refund_processed"

    # Message related
    NEW_MESSAGE = "new_message"

    # Review related
    NEW_REVIEW = "new_review"
    REVIEW_PROMPT = "review_prompt"

    # System/Account
    ACCOUNT_UPDATE = "account_update"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    LEARNING_NUDGE = "learning_nudge"

    # Package related
    PACKAGE_EXPIRING = "package_expiring"
    PACKAGE_EXPIRED = "package_expired"

    @classmethod
    def from_string(cls, value: str) -> "NotificationType":
        """
        Convert string to NotificationType.

        Args:
            value: String representation of notification type

        Returns:
            NotificationType enum member

        Raises:
            ValueError: If value is not a valid notification type
        """
        try:
            return cls(value)
        except ValueError:
            valid = [t.value for t in cls]
            raise ValueError(
                f"Invalid notification type: {value}. Valid types: {valid}"
            )


class NotificationPriority(int, Enum):
    """
    Notification priority levels.

    Lower numbers indicate higher priority.
    Used for ordering and filtering notifications.
    """

    URGENT = 1  # Critical notifications (e.g., payment failures)
    HIGH = 2  # Important notifications (e.g., booking confirmations)
    NORMAL = 3  # Standard notifications (e.g., new messages)
    LOW = 4  # Non-urgent notifications (e.g., achievements)

    @property
    def display_name(self) -> str:
        """Get human-readable priority name."""
        return self.name.lower().replace("_", " ")


class NotificationCategory(str, Enum):
    """
    Notification categories for filtering and grouping.

    Used to organize notifications in the UI and manage preferences.
    """

    BOOKING = "booking"
    PAYMENT = "payment"
    MESSAGE = "message"
    REVIEW = "review"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"
    LEARNING = "learning"
    PACKAGE = "package"

    @classmethod
    def from_notification_type(
        cls, notification_type: NotificationType
    ) -> "NotificationCategory":
        """
        Get category for a notification type.

        Args:
            notification_type: The notification type

        Returns:
            Corresponding notification category
        """
        type_to_category = {
            NotificationType.BOOKING_CONFIRMED: cls.BOOKING,
            NotificationType.BOOKING_CANCELLED: cls.BOOKING,
            NotificationType.BOOKING_REMINDER: cls.BOOKING,
            NotificationType.BOOKING_REQUEST: cls.BOOKING,
            NotificationType.BOOKING_COMPLETED: cls.BOOKING,
            NotificationType.PAYMENT_RECEIVED: cls.PAYMENT,
            NotificationType.PAYMENT_FAILED: cls.PAYMENT,
            NotificationType.PAYOUT_COMPLETED: cls.PAYMENT,
            NotificationType.REFUND_PROCESSED: cls.PAYMENT,
            NotificationType.NEW_MESSAGE: cls.MESSAGE,
            NotificationType.NEW_REVIEW: cls.REVIEW,
            NotificationType.REVIEW_PROMPT: cls.REVIEW,
            NotificationType.ACCOUNT_UPDATE: cls.SYSTEM,
            NotificationType.SYSTEM_ANNOUNCEMENT: cls.SYSTEM,
            NotificationType.ACHIEVEMENT_UNLOCKED: cls.ACHIEVEMENT,
            NotificationType.LEARNING_NUDGE: cls.LEARNING,
            NotificationType.PACKAGE_EXPIRING: cls.PACKAGE,
            NotificationType.PACKAGE_EXPIRED: cls.PACKAGE,
        }
        return type_to_category.get(notification_type, cls.SYSTEM)


class DeliveryChannel(str, Enum):
    """
    Notification delivery channels.

    Represents the different ways a notification can be delivered.
    """

    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    SMS = "sms"


@dataclass(frozen=True)
class NotificationChannel:
    """
    Target channel configuration for notification delivery.

    Immutable value object that specifies how a notification should be delivered.
    """

    channel: DeliveryChannel
    enabled: bool = True
    template_id: str | None = None
    priority_override: NotificationPriority | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def with_enabled(self, enabled: bool) -> "NotificationChannel":
        """Create a copy with updated enabled status."""
        return NotificationChannel(
            channel=self.channel,
            enabled=enabled,
            template_id=self.template_id,
            priority_override=self.priority_override,
            metadata=self.metadata,
        )

    def with_template(self, template_id: str) -> "NotificationChannel":
        """Create a copy with updated template."""
        return NotificationChannel(
            channel=self.channel,
            enabled=self.enabled,
            template_id=template_id,
            priority_override=self.priority_override,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class DeliveryResult:
    """
    Result of a notification delivery attempt.

    Immutable value object representing the outcome of sending a notification.
    """

    channel: DeliveryChannel
    success: bool
    message_id: str | None = None
    error_message: str | None = None
    retryable: bool = False

    @property
    def failed(self) -> bool:
        """Check if delivery failed."""
        return not self.success

    @classmethod
    def success_result(
        cls, channel: DeliveryChannel, message_id: str | None = None
    ) -> "DeliveryResult":
        """Create a successful delivery result."""
        return cls(channel=channel, success=True, message_id=message_id)

    @classmethod
    def failure_result(
        cls,
        channel: DeliveryChannel,
        error_message: str,
        retryable: bool = False,
    ) -> "DeliveryResult":
        """Create a failed delivery result."""
        return cls(
            channel=channel,
            success=False,
            error_message=error_message,
            retryable=retryable,
        )
