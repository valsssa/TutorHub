"""SQLAlchemy repository implementations for notifications module.

Provides concrete implementations of the notification repository protocols
defined in the domain layer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, update
from sqlalchemy.orm import Session

from models.notifications import Notification, NotificationPreferences
from modules.notifications.domain.entities import (
    NotificationBatch,
    NotificationDeliveryAttempt,
    NotificationEntity,
    NotificationPreference,
)
from modules.notifications.domain.value_objects import (
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationRepositoryImpl:
    """SQLAlchemy implementation of NotificationRepository."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, notification_id: int) -> NotificationEntity | None:
        """Get a notification by its ID.

        Args:
            notification_id: Notification's unique identifier

        Returns:
            NotificationEntity if found, None otherwise
        """
        model = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

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
        """Get notifications for a user with optional filtering.

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
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if category is not None:
            query = query.filter(Notification.category == category.value)

        if notification_type is not None:
            query = query.filter(Notification.type == notification_type.value)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if not include_dismissed:
            query = query.filter(Notification.dismissed_at.is_(None))

        if from_date is not None:
            query = query.filter(Notification.created_at >= from_date)

        if to_date is not None:
            query = query.filter(Notification.created_at <= to_date)

        query = query.order_by(Notification.created_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        return [self._to_entity(m) for m in models]

    def create(self, notification: NotificationEntity) -> NotificationEntity:
        """Create a new notification.

        Args:
            notification: Notification entity to create

        Returns:
            Created notification with populated ID
        """
        model = self._to_model(notification)
        self.db.add(model)
        self.db.flush()
        return self._to_entity(model)

    def update(self, notification: NotificationEntity) -> NotificationEntity:
        """Update an existing notification.

        Args:
            notification: Notification entity with updated fields

        Returns:
            Updated notification entity

        Raises:
            ValueError: If notification ID is None or not found
        """
        if notification.id is None:
            raise ValueError("Cannot update notification without ID")

        model = (
            self.db.query(Notification)
            .filter(Notification.id == notification.id)
            .first()
        )
        if not model:
            raise ValueError(f"Notification {notification.id} not found")

        model.type = notification.type.value
        model.title = notification.title
        model.message = notification.message
        model.is_read = notification.is_read
        model.read_at = notification.read_at
        model.dismissed_at = notification.dismissed_at
        model.category = notification.category.value if notification.category else None
        model.priority = notification.priority.value
        model.link = notification.link
        model.action_url = notification.action_url
        model.action_label = notification.action_label
        model.extra_data = notification.extra_data
        model.sent_at = notification.sent_at

        self.db.flush()
        return self._to_entity(model)

    def mark_as_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if marked, False if not found or not owned by user
        """
        now = datetime.now(UTC)
        result = (
            self.db.execute(
                update(Notification)
                .where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                        Notification.is_read == False,  # noqa: E712
                    )
                )
                .values(is_read=True, read_at=now)
            )
        )
        self.db.flush()
        return result.rowcount > 0

    def mark_all_as_read(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
    ) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: User's ID
            category: Optional category filter

        Returns:
            Number of notifications marked as read
        """
        now = datetime.now(UTC)

        conditions = [
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        ]

        if category is not None:
            conditions.append(Notification.category == category.value)

        result = (
            self.db.execute(
                update(Notification)
                .where(and_(*conditions))
                .values(is_read=True, read_at=now)
            )
        )
        self.db.flush()
        return result.rowcount

    def dismiss(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """Dismiss a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if dismissed, False if not found or not owned by user
        """
        now = datetime.now(UTC)
        result = (
            self.db.execute(
                update(Notification)
                .where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                        Notification.dismissed_at.is_(None),
                    )
                )
                .values(dismissed_at=now)
            )
        )
        self.db.flush()
        return result.rowcount > 0

    def delete(
        self,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """Delete a notification (hard delete).

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found or not owned by user
        """
        result = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .delete()
        )
        self.db.flush()
        return result > 0

    def count_unread(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
    ) -> int:
        """Count unread notifications for a user.

        Args:
            user_id: User's ID
            category: Optional category filter

        Returns:
            Count of unread notifications
        """
        query = self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
                Notification.dismissed_at.is_(None),
            )
        )

        if category is not None:
            query = query.filter(Notification.category == category.value)

        return query.scalar() or 0

    def count_by_user(
        self,
        user_id: int,
        *,
        category: NotificationCategory | None = None,
        is_read: bool | None = None,
        include_dismissed: bool = False,
    ) -> int:
        """Count notifications for a user.

        Args:
            user_id: User's ID
            category: Optional category filter
            is_read: Optional read status filter
            include_dismissed: Include dismissed notifications

        Returns:
            Total count of matching notifications
        """
        query = self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        )

        if category is not None:
            query = query.filter(Notification.category == category.value)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if not include_dismissed:
            query = query.filter(Notification.dismissed_at.is_(None))

        return query.scalar() or 0

    def get_recent_by_type(
        self,
        user_id: int,
        notification_type: NotificationType,
        *,
        since: datetime,
    ) -> list[NotificationEntity]:
        """Get recent notifications of a specific type.

        Useful for deduplication and rate limiting.

        Args:
            user_id: User's ID
            notification_type: Type of notification
            since: Start datetime

        Returns:
            List of matching notifications
        """
        models = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == notification_type.value,
                    Notification.created_at >= since,
                )
            )
            .order_by(Notification.created_at.desc())
            .all()
        )

        return [self._to_entity(m) for m in models]

    def delete_expired(self) -> int:
        """Delete all expired notifications.

        Notifications are considered expired if they have an expires_at
        field set in extra_data and that time has passed.

        Note: This is a simplified implementation. In production, you may
        want to add a dedicated expires_at column to the Notification model.

        Returns:
            Number of notifications deleted
        """
        # For now, we don't have a direct expires_at column in the model.
        # This would need to be implemented based on business requirements.
        # A common pattern is to delete very old notifications.
        cutoff = datetime.now(UTC) - timedelta(days=90)

        result = (
            self.db.query(Notification)
            .filter(Notification.created_at < cutoff)
            .delete()
        )
        self.db.flush()
        return result

    def _to_entity(self, model: Notification) -> NotificationEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: Notification SQLAlchemy model

        Returns:
            NotificationEntity domain entity
        """
        notification_type = NotificationType(model.type)

        category = None
        if model.category:
            try:
                category = NotificationCategory(model.category)
            except ValueError:
                category = NotificationCategory.from_notification_type(notification_type)

        priority = NotificationPriority.NORMAL
        if model.priority:
            try:
                priority = NotificationPriority(model.priority)
            except ValueError:
                priority = NotificationPriority.NORMAL

        extra_data: dict[str, Any] = {}
        if model.extra_data:
            extra_data = dict(model.extra_data) if model.extra_data else {}

        return NotificationEntity(
            id=model.id,
            user_id=model.user_id,
            type=notification_type,
            title=model.title,
            message=model.message,
            is_read=model.is_read,
            read_at=model.read_at,
            dismissed_at=model.dismissed_at,
            category=category,
            priority=priority,
            link=model.link,
            action_url=model.action_url,
            action_label=model.action_label,
            extra_data=extra_data,
            created_at=model.created_at,
            sent_at=model.sent_at,
            expires_at=None,  # Not stored directly in model
        )

    def _to_model(self, entity: NotificationEntity) -> Notification:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: NotificationEntity domain entity

        Returns:
            Notification SQLAlchemy model
        """
        return Notification(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type.value,
            title=entity.title,
            message=entity.message,
            is_read=entity.is_read,
            read_at=entity.read_at,
            dismissed_at=entity.dismissed_at,
            category=entity.category.value if entity.category else None,
            priority=entity.priority.value,
            link=entity.link,
            action_url=entity.action_url,
            action_label=entity.action_label,
            extra_data=entity.extra_data if entity.extra_data else None,
            sent_at=entity.sent_at,
        )


class NotificationPreferenceRepositoryImpl:
    """SQLAlchemy implementation of NotificationPreferenceRepository."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_user(self, user_id: int) -> NotificationPreference | None:
        """Get notification preferences for a user.

        Args:
            user_id: User's ID

        Returns:
            NotificationPreference if found, None otherwise
        """
        model = (
            self.db.query(NotificationPreferences)
            .filter(NotificationPreferences.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_or_create(self, user_id: int) -> NotificationPreference:
        """Get notification preferences for a user, creating defaults if needed.

        Args:
            user_id: User's ID

        Returns:
            NotificationPreference (existing or newly created)
        """
        existing = self.get_by_user(user_id)
        if existing:
            return existing

        default_prefs = NotificationPreference(
            id=None,
            user_id=user_id,
        )
        model = self._to_model(default_prefs)
        self.db.add(model)
        self.db.flush()
        return self._to_entity(model)

    def update(self, preference: NotificationPreference) -> NotificationPreference:
        """Update notification preferences.

        Args:
            preference: Preference entity with updated fields

        Returns:
            Updated preference entity

        Raises:
            ValueError: If preference ID is None or not found
        """
        if preference.id is None:
            raise ValueError("Cannot update preference without ID")

        model = (
            self.db.query(NotificationPreferences)
            .filter(NotificationPreferences.id == preference.id)
            .first()
        )
        if not model:
            raise ValueError(f"Preference {preference.id} not found")

        model.email_enabled = preference.email_enabled
        model.push_enabled = preference.push_enabled
        model.sms_enabled = preference.sms_enabled
        model.session_reminders_enabled = preference.session_reminders_enabled
        model.booking_requests_enabled = preference.booking_requests_enabled
        model.learning_nudges_enabled = preference.learning_nudges_enabled
        model.review_prompts_enabled = preference.review_prompts_enabled
        model.achievements_enabled = preference.achievements_enabled
        model.marketing_enabled = preference.marketing_enabled
        model.quiet_hours_start = self._time_str_to_time(preference.quiet_hours_start)
        model.quiet_hours_end = self._time_str_to_time(preference.quiet_hours_end)
        model.preferred_notification_time = self._time_str_to_time(
            preference.preferred_notification_time
        )
        model.max_daily_notifications = preference.max_daily_notifications
        model.max_weekly_nudges = preference.max_weekly_nudges
        model.updated_at = datetime.now(UTC)

        self.db.flush()
        return self._to_entity(model)

    def get_users_with_channel_enabled(
        self,
        channel: DeliveryChannel,
        *,
        notification_type: NotificationType | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> list[int]:
        """Get user IDs with a specific channel enabled.

        Useful for batch notifications.

        Args:
            channel: Delivery channel to check
            notification_type: Optional type to check
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of user IDs
        """
        channel_column_map = {
            DeliveryChannel.EMAIL: NotificationPreferences.email_enabled,
            DeliveryChannel.PUSH: NotificationPreferences.push_enabled,
            DeliveryChannel.SMS: NotificationPreferences.sms_enabled,
            DeliveryChannel.IN_APP: NotificationPreferences.email_enabled,  # Default
        }

        channel_column = channel_column_map.get(
            channel, NotificationPreferences.email_enabled
        )

        query = self.db.query(NotificationPreferences.user_id).filter(
            channel_column == True  # noqa: E712
        )

        if notification_type is not None:
            type_column_map = {
                NotificationType.BOOKING_REMINDER: (
                    NotificationPreferences.session_reminders_enabled
                ),
                NotificationType.BOOKING_REQUEST: (
                    NotificationPreferences.booking_requests_enabled
                ),
                NotificationType.LEARNING_NUDGE: (
                    NotificationPreferences.learning_nudges_enabled
                ),
                NotificationType.REVIEW_PROMPT: (
                    NotificationPreferences.review_prompts_enabled
                ),
                NotificationType.ACHIEVEMENT_UNLOCKED: (
                    NotificationPreferences.achievements_enabled
                ),
                NotificationType.SYSTEM_ANNOUNCEMENT: (
                    NotificationPreferences.marketing_enabled
                ),
            }
            type_column = type_column_map.get(notification_type)
            if type_column is not None:
                query = query.filter(type_column == True)  # noqa: E712

        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        return [r[0] for r in results]

    def _to_entity(self, model: NotificationPreferences) -> NotificationPreference:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: NotificationPreferences SQLAlchemy model

        Returns:
            NotificationPreference domain entity
        """
        return NotificationPreference(
            id=model.id,
            user_id=model.user_id,
            email_enabled=model.email_enabled or True,
            push_enabled=model.push_enabled or True,
            sms_enabled=model.sms_enabled or False,
            in_app_enabled=True,  # Not stored in model, default to True
            session_reminders_enabled=model.session_reminders_enabled or True,
            booking_requests_enabled=model.booking_requests_enabled or True,
            learning_nudges_enabled=model.learning_nudges_enabled or True,
            review_prompts_enabled=model.review_prompts_enabled or True,
            achievements_enabled=model.achievements_enabled or True,
            marketing_enabled=model.marketing_enabled or False,
            quiet_hours_start=self._time_to_str(model.quiet_hours_start),
            quiet_hours_end=self._time_to_str(model.quiet_hours_end),
            preferred_notification_time=self._time_to_str(
                model.preferred_notification_time
            ),
            max_daily_notifications=model.max_daily_notifications,
            max_weekly_nudges=model.max_weekly_nudges,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: NotificationPreference) -> NotificationPreferences:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: NotificationPreference domain entity

        Returns:
            NotificationPreferences SQLAlchemy model
        """
        now = datetime.now(UTC)
        return NotificationPreferences(
            id=entity.id,
            user_id=entity.user_id,
            email_enabled=entity.email_enabled,
            push_enabled=entity.push_enabled,
            sms_enabled=entity.sms_enabled,
            session_reminders_enabled=entity.session_reminders_enabled,
            booking_requests_enabled=entity.booking_requests_enabled,
            learning_nudges_enabled=entity.learning_nudges_enabled,
            review_prompts_enabled=entity.review_prompts_enabled,
            achievements_enabled=entity.achievements_enabled,
            marketing_enabled=entity.marketing_enabled,
            quiet_hours_start=self._time_str_to_time(entity.quiet_hours_start),
            quiet_hours_end=self._time_str_to_time(entity.quiet_hours_end),
            preferred_notification_time=self._time_str_to_time(
                entity.preferred_notification_time
            ),
            max_daily_notifications=entity.max_daily_notifications,
            max_weekly_nudges=entity.max_weekly_nudges,
            created_at=entity.created_at or now,
            updated_at=entity.updated_at or now,
        )

    @staticmethod
    def _time_to_str(time_obj: Any) -> str | None:
        """Convert time object to HH:MM string format.

        Args:
            time_obj: Python time object or None

        Returns:
            String in HH:MM format or None
        """
        if time_obj is None:
            return None
        return time_obj.strftime("%H:%M")

    @staticmethod
    def _time_str_to_time(time_str: str | None) -> Any:
        """Convert HH:MM string to time object.

        Args:
            time_str: String in HH:MM format or None

        Returns:
            Python time object or None
        """
        if time_str is None:
            return None
        from datetime import time as time_type

        parts = time_str.split(":")
        if len(parts) >= 2:
            return time_type(int(parts[0]), int(parts[1]))
        return None


class NotificationDeliveryRepositoryImpl:
    """SQLAlchemy implementation of NotificationDeliveryRepository.

    Note: This implementation uses in-memory storage as there is no
    dedicated database table for delivery attempts in the current schema.
    For production use, add a notification_delivery_attempts table.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._attempts: dict[int, NotificationDeliveryAttempt] = {}
        self._next_id = 1

    def create_attempt(
        self,
        attempt: NotificationDeliveryAttempt,
    ) -> NotificationDeliveryAttempt:
        """Record a delivery attempt.

        Args:
            attempt: Delivery attempt entity

        Returns:
            Created attempt with populated ID
        """
        attempt_id = self._next_id
        self._next_id += 1

        new_attempt = NotificationDeliveryAttempt(
            id=attempt_id,
            notification_id=attempt.notification_id,
            channel=attempt.channel,
            attempted_at=attempt.attempted_at,
            success=attempt.success,
            message_id=attempt.message_id,
            error_message=attempt.error_message,
            retry_count=attempt.retry_count,
        )
        self._attempts[attempt_id] = new_attempt
        return new_attempt

    def get_attempts_for_notification(
        self,
        notification_id: int,
    ) -> list[NotificationDeliveryAttempt]:
        """Get all delivery attempts for a notification.

        Args:
            notification_id: Notification ID

        Returns:
            List of delivery attempts
        """
        return [
            a for a in self._attempts.values()
            if a.notification_id == notification_id
        ]

    def get_failed_attempts_for_retry(
        self,
        *,
        max_retry_count: int = 3,
        older_than_minutes: int = 5,
        limit: int = 100,
    ) -> list[NotificationDeliveryAttempt]:
        """Get failed delivery attempts eligible for retry.

        Args:
            max_retry_count: Maximum retry count threshold
            older_than_minutes: Only attempts older than this
            limit: Maximum number to return

        Returns:
            List of delivery attempts to retry
        """
        cutoff = datetime.now(UTC) - timedelta(minutes=older_than_minutes)

        eligible = [
            a for a in self._attempts.values()
            if (
                not a.success
                and a.retry_count < max_retry_count
                and a.attempted_at < cutoff
            )
        ]

        eligible.sort(key=lambda x: x.attempted_at)
        return eligible[:limit]

    def update_attempt(
        self,
        attempt: NotificationDeliveryAttempt,
    ) -> NotificationDeliveryAttempt:
        """Update a delivery attempt record.

        Args:
            attempt: Delivery attempt with updated fields

        Returns:
            Updated delivery attempt
        """
        if attempt.id is None:
            raise ValueError("Cannot update attempt without ID")

        self._attempts[attempt.id] = attempt
        return attempt


class NotificationBatchRepositoryImpl:
    """SQLAlchemy implementation of NotificationBatchRepository.

    Note: This implementation uses in-memory storage as there is no
    dedicated database table for batches in the current schema.
    For production use, add a notification_batches table.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._batches: dict[int, NotificationBatch] = {}
        self._next_id = 1

    def create(self, batch: NotificationBatch) -> NotificationBatch:
        """Create a new notification batch.

        Args:
            batch: Batch entity to create

        Returns:
            Created batch with populated ID
        """
        batch_id = self._next_id
        self._next_id += 1

        new_batch = NotificationBatch(
            id=batch_id,
            name=batch.name,
            notification_type=batch.notification_type,
            title=batch.title,
            message=batch.message,
            total_count=batch.total_count,
            sent_count=batch.sent_count,
            failed_count=batch.failed_count,
            status=batch.status,
            created_at=batch.created_at or datetime.now(UTC),
            completed_at=batch.completed_at,
            extra_data=batch.extra_data,
        )
        self._batches[batch_id] = new_batch
        return new_batch

    def get_by_id(self, batch_id: int) -> NotificationBatch | None:
        """Get a batch by its ID.

        Args:
            batch_id: Batch's unique identifier

        Returns:
            NotificationBatch if found, None otherwise
        """
        return self._batches.get(batch_id)

    def update(self, batch: NotificationBatch) -> NotificationBatch:
        """Update a batch record.

        Args:
            batch: Batch entity with updated fields

        Returns:
            Updated batch entity

        Raises:
            ValueError: If batch ID is None or not found
        """
        if batch.id is None:
            raise ValueError("Cannot update batch without ID")

        if batch.id not in self._batches:
            raise ValueError(f"Batch {batch.id} not found")

        self._batches[batch.id] = batch
        return batch

    def get_pending_batches(self) -> list[NotificationBatch]:
        """Get all pending batches ready for processing.

        Returns:
            List of pending batches
        """
        return [b for b in self._batches.values() if b.status == "pending"]

    def increment_sent_count(self, batch_id: int) -> None:
        """Increment the sent count for a batch.

        Args:
            batch_id: Batch ID
        """
        batch = self._batches.get(batch_id)
        if batch:
            batch.sent_count += 1
            self._batches[batch_id] = batch

    def increment_failed_count(self, batch_id: int) -> None:
        """Increment the failed count for a batch.

        Args:
            batch_id: Batch ID
        """
        batch = self._batches.get(batch_id)
        if batch:
            batch.failed_count += 1
            self._batches[batch_id] = batch
