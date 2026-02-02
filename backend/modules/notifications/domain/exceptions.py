"""
Domain exceptions for notifications module.

These exceptions represent business rule violations specific to notifications.
"""


class NotificationError(Exception):
    """Base exception for notification domain errors."""

    pass


class NotificationNotFoundError(NotificationError):
    """Raised when a notification is not found."""

    def __init__(self, notification_id: int | None = None):
        self.notification_id = notification_id
        if notification_id:
            message = f"Notification not found: {notification_id}"
        else:
            message = "Notification not found"
        super().__init__(message)


class InvalidNotificationTypeError(NotificationError):
    """Raised when an invalid notification type is provided."""

    def __init__(self, notification_type: str, valid_types: list[str] | None = None):
        self.notification_type = notification_type
        self.valid_types = valid_types
        message = f"Invalid notification type: {notification_type}"
        if valid_types:
            message += f". Valid types are: {', '.join(valid_types)}"
        super().__init__(message)


class NotificationDeliveryError(NotificationError):
    """Raised when notification delivery fails."""

    def __init__(
        self,
        channel: str,
        reason: str,
        notification_id: int | None = None,
        user_id: int | None = None,
        retryable: bool = False,
    ):
        self.channel = channel
        self.reason = reason
        self.notification_id = notification_id
        self.user_id = user_id
        self.retryable = retryable
        message = f"Failed to deliver notification via {channel}: {reason}"
        if notification_id:
            message += f" (notification_id={notification_id})"
        super().__init__(message)


class RecipientNotFoundError(NotificationError):
    """Raised when the notification recipient is not found."""

    def __init__(self, user_id: int | None = None, email: str | None = None):
        self.user_id = user_id
        self.email = email
        if user_id:
            message = f"Recipient not found: user_id={user_id}"
        elif email:
            message = f"Recipient not found: email={email}"
        else:
            message = "Recipient not found"
        super().__init__(message)


class NotificationPreferencesBlockedError(NotificationError):
    """Raised when notification is blocked by user preferences."""

    def __init__(
        self,
        user_id: int,
        notification_type: str,
        channel: str | None = None,
    ):
        self.user_id = user_id
        self.notification_type = notification_type
        self.channel = channel
        message = f"Notification blocked by user preferences: type={notification_type}"
        if channel:
            message += f", channel={channel}"
        super().__init__(message)


class QuietHoursActiveError(NotificationError):
    """Raised when attempting to send during user's quiet hours."""

    def __init__(
        self,
        user_id: int,
        quiet_hours_start: str,
        quiet_hours_end: str,
    ):
        self.user_id = user_id
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        super().__init__(
            f"Cannot send notification during quiet hours ({quiet_hours_start} - {quiet_hours_end})"
        )


class RateLimitExceededError(NotificationError):
    """Raised when notification rate limit is exceeded."""

    def __init__(
        self,
        user_id: int,
        limit_type: str,
        current_count: int,
        max_count: int,
    ):
        self.user_id = user_id
        self.limit_type = limit_type
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(
            f"Notification rate limit exceeded: {limit_type} "
            f"({current_count}/{max_count})"
        )
