"""
Notification domain layer.

Contains domain entities, value objects, exceptions, and repository protocols
for the notification system.
"""

from modules.notifications.domain.entities import (
    NotificationBatch,
    NotificationDeliveryAttempt,
    NotificationEntity,
    NotificationPreference,
)
from modules.notifications.domain.exceptions import (
    InvalidNotificationTypeError,
    NotificationDeliveryError,
    NotificationError,
    NotificationNotFoundError,
    NotificationPreferencesBlockedError,
    QuietHoursActiveError,
    RateLimitExceededError,
    RecipientNotFoundError,
)
from modules.notifications.domain.repositories import (
    NotificationBatchRepository,
    NotificationDeliveryRepository,
    NotificationPreferenceRepository,
    NotificationRepository,
)
from modules.notifications.domain.value_objects import (
    DeliveryChannel,
    DeliveryResult,
    NotificationCategory,
    NotificationChannel,
    NotificationId,
    NotificationPriority,
    NotificationType,
)

__all__ = [
    # Entities
    "NotificationEntity",
    "NotificationPreference",
    "NotificationDeliveryAttempt",
    "NotificationBatch",
    # Value Objects
    "NotificationId",
    "NotificationType",
    "NotificationPriority",
    "NotificationCategory",
    "NotificationChannel",
    "DeliveryChannel",
    "DeliveryResult",
    # Exceptions
    "NotificationError",
    "NotificationNotFoundError",
    "InvalidNotificationTypeError",
    "NotificationDeliveryError",
    "RecipientNotFoundError",
    "NotificationPreferencesBlockedError",
    "QuietHoursActiveError",
    "RateLimitExceededError",
    # Repositories
    "NotificationRepository",
    "NotificationPreferenceRepository",
    "NotificationDeliveryRepository",
    "NotificationBatchRepository",
]
