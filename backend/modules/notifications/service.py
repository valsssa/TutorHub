"""
Notification Service Layer

Handles business logic for notifications including:
- Creating notifications with preference checks
- Email delivery integration
- Scheduled notifications
- Analytics tracking
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from core.email_service import EmailDeliveryStatus, email_service
from models import Notification, NotificationAnalytics, NotificationPreferences, User

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Standard notification types."""

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


class NotificationCategory(str, Enum):
    """Notification categories for filtering."""

    BOOKING = "booking"
    PAYMENT = "payment"
    MESSAGE = "message"
    REVIEW = "review"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"
    LEARNING = "learning"


class NotificationService:
    """Service for creating and managing notifications."""

    # Map notification types to categories
    TYPE_CATEGORIES = {
        NotificationType.BOOKING_CONFIRMED: NotificationCategory.BOOKING,
        NotificationType.BOOKING_CANCELLED: NotificationCategory.BOOKING,
        NotificationType.BOOKING_REMINDER: NotificationCategory.BOOKING,
        NotificationType.BOOKING_REQUEST: NotificationCategory.BOOKING,
        NotificationType.BOOKING_COMPLETED: NotificationCategory.BOOKING,
        NotificationType.PAYMENT_RECEIVED: NotificationCategory.PAYMENT,
        NotificationType.PAYMENT_FAILED: NotificationCategory.PAYMENT,
        NotificationType.PAYOUT_COMPLETED: NotificationCategory.PAYMENT,
        NotificationType.REFUND_PROCESSED: NotificationCategory.PAYMENT,
        NotificationType.NEW_MESSAGE: NotificationCategory.MESSAGE,
        NotificationType.NEW_REVIEW: NotificationCategory.REVIEW,
        NotificationType.REVIEW_PROMPT: NotificationCategory.REVIEW,
        NotificationType.ACCOUNT_UPDATE: NotificationCategory.SYSTEM,
        NotificationType.SYSTEM_ANNOUNCEMENT: NotificationCategory.SYSTEM,
        NotificationType.ACHIEVEMENT_UNLOCKED: NotificationCategory.ACHIEVEMENT,
        NotificationType.LEARNING_NUDGE: NotificationCategory.LEARNING,
        NotificationType.PACKAGE_EXPIRING: NotificationCategory.SYSTEM,
        NotificationType.PACKAGE_EXPIRED: NotificationCategory.SYSTEM,
    }

    def _get_or_create_preferences(self, db: Session, user_id: int) -> NotificationPreferences:
        """Get user preferences or create defaults."""
        prefs = db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user_id).first()
        if not prefs:
            prefs = NotificationPreferences(user_id=user_id)
            db.add(prefs)
            db.flush()
        return prefs

    def _should_notify(
        self,
        prefs: NotificationPreferences,
        notification_type: NotificationType | str,
    ) -> tuple[bool, bool]:
        """
        Check if notification should be sent based on preferences.

        Returns: (should_create_in_app, should_send_email)
        """
        type_str = notification_type.value if isinstance(notification_type, NotificationType) else notification_type

        # Check specific preference flags based on type
        if type_str.startswith("booking_reminder"):
            if not prefs.session_reminders_enabled:
                return False, False
        elif type_str == "booking_request":
            if not prefs.booking_requests_enabled:
                return False, False
        elif type_str == "learning_nudge":
            if not prefs.learning_nudges_enabled:
                return False, False
        elif type_str == "review_prompt":
            if not prefs.review_prompts_enabled:
                return False, False
        elif type_str == "achievement_unlocked":
            if not prefs.achievements_enabled:
                return False, False
        elif type_str in ("system_announcement", "marketing") and not prefs.marketing_enabled:
            # Marketing/promotional not enabled
            return False, False

        # Check quiet hours for email
        should_email = prefs.email_enabled
        if should_email and prefs.quiet_hours_start and prefs.quiet_hours_end:
            current_time = datetime.now(UTC).time()
            if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                should_email = False

        return True, should_email

    def create_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: NotificationType | str,
        title: str,
        message: str,
        link: str | None = None,
        action_url: str | None = None,
        action_label: str | None = None,
        priority: int = 3,
        metadata: dict[str, Any] | None = None,
        send_email: bool = True,
        email_template: str | None = None,
        email_params: dict[str, Any] | None = None,
    ) -> Notification | None:
        """
        Create a notification for a user with preference checks.

        Args:
            db: Database session
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            link: Optional link for the notification
            action_url: Optional action button URL
            action_label: Optional action button label
            priority: Priority 1-5 (1=highest)
            metadata: Optional additional data
            send_email: Whether to also send email
            email_template: Optional email template name
            email_params: Optional email template parameters

        Returns:
            Created notification or None if blocked by preferences
        """
        # Get user preferences
        prefs = self._get_or_create_preferences(db, user_id)

        # Check if we should notify
        should_create, should_email = self._should_notify(prefs, notification_type)

        if not should_create:
            logger.debug(f"Notification blocked by preferences for user {user_id}: {notification_type}")
            return None

        # Determine category
        type_value = notification_type.value if isinstance(notification_type, NotificationType) else notification_type
        category = self.TYPE_CATEGORIES.get(
            NotificationType(type_value) if type_value in [t.value for t in NotificationType] else None,
            NotificationCategory.SYSTEM,
        )

        # Create notification
        notification = Notification(
            user_id=user_id,
            type=type_value,
            title=title,
            message=message,
            link=link,
            category=category.value if isinstance(category, NotificationCategory) else category,
            priority=priority,
            action_url=action_url,
            action_label=action_label,
            extra_data=metadata,  # Column renamed from 'metadata' which is reserved in SQLAlchemy
            sent_at=datetime.now(UTC),
        )
        db.add(notification)
        db.flush()

        logger.info(f"Created notification {notification.id} for user {user_id}: {type_value}")

        # Send email if enabled
        if send_email and should_email:
            self._send_email_notification(db, user_id, notification, email_template, email_params)

        # Track analytics
        self._track_analytics(
            db,
            template_key=type_value,
            user_id=user_id,
            delivery_channel="in_app",
            was_actionable=bool(action_url),
        )

        return notification

    def _send_email_notification(
        self,
        db: Session,
        user_id: int,
        notification: Notification,
        template: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send email for notification with delivery tracking.

        Args:
            db: Database session
            user_id: Target user ID
            notification: The notification object
            template: Optional email template name
            params: Optional template parameters

        Returns:
            True if email was sent successfully, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            logger.warning(
                f"Cannot send email notification: user {user_id} has no email address"
            )
            return False

        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"

        # Use generic notification email if no template specified
        if not template:
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #10b981;">{notification.title}</h1>
                    <p>Hi {name},</p>
                    <p>{notification.message}</p>
                    {f'<p><a href="{notification.action_url}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">{notification.action_label or "View"}</a></p>' if notification.action_url else ''}
                </div>
            </body>
            </html>
            """
            result = email_service._send_email_with_tracking(
                to_email=user.email,
                to_name=name,
                subject=notification.title,
                html_content=html_content,
            )

            # Log email delivery status for monitoring
            if result.success:
                logger.info(
                    f"Email notification sent for notification {notification.id}",
                    extra={
                        "notification_id": notification.id,
                        "notification_type": notification.type,
                        "user_id": user_id,
                        "email_to": user.email,
                        "message_id": result.message_id,
                        "status": result.status.value,
                    },
                )
            else:
                logger.error(
                    f"Failed to send email notification for notification {notification.id}",
                    extra={
                        "notification_id": notification.id,
                        "notification_type": notification.type,
                        "user_id": user_id,
                        "email_to": user.email,
                        "status": result.status.value,
                        "error": result.error_message,
                    },
                )

            # Track email delivery in analytics
            self._track_email_delivery(
                db=db,
                notification_id=notification.id,
                user_id=user_id,
                success=result.success,
                status=result.status,
                error_message=result.error_message,
            )

            return result.success

        return True

    def _track_email_delivery(
        self,
        db: Session,
        notification_id: int,
        user_id: int,
        success: bool,
        status: EmailDeliveryStatus,
        error_message: str | None = None,
    ) -> None:
        """
        Track email delivery attempt in analytics.

        This creates an analytics record that can be queried for
        monitoring email delivery rates and failures.
        """
        # Use template_key to encode the delivery status for easy querying
        # Format: email_delivery_<status> (e.g., email_delivery_success, email_delivery_failed_transient)
        analytics = NotificationAnalytics(
            template_key=f"email_delivery_{status.value}",
            user_id=user_id,
            sent_at=datetime.now(UTC),
            delivery_channel="email",
            was_actionable=False,
            action_taken=success,  # Use action_taken to indicate success/failure
        )
        db.add(analytics)

    def _track_analytics(
        self,
        db: Session,
        template_key: str,
        user_id: int | None,
        delivery_channel: str,
        was_actionable: bool = False,
    ) -> None:
        """Track notification analytics."""
        analytics = NotificationAnalytics(
            template_key=template_key,
            user_id=user_id,
            sent_at=datetime.now(UTC),
            delivery_channel=delivery_channel,
            was_actionable=was_actionable,
        )
        db.add(analytics)

    def get_unread_count(self, db: Session, user_id: int) -> int:
        """Get count of unread notifications for a user."""
        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.dismissed_at.is_(None),
            )
            .count()
        )

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        return True

    def mark_all_read(self, db: Session, user_id: int) -> int:
        """
        Mark all unread notifications as read for a user.

        Uses atomic bulk UPDATE for race condition safety and idempotency.
        Safe to call multiple times - if already read, returns 0.

        Args:
            db: Database session
            user_id: User whose notifications to mark as read

        Returns:
            Number of notifications that were marked as read
        """
        now = datetime.now(UTC)
        updated_count = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .update({"is_read": True, "read_at": now})
        )
        return updated_count

    def dismiss_notification(self, db: Session, notification_id: int, user_id: int) -> bool:
        """Dismiss (hide) a notification without deleting it."""
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

        if not notification:
            return False

        notification.dismissed_at = datetime.now(UTC)
        return True

    def get_user_preferences(self, db: Session, user_id: int) -> NotificationPreferences:
        """Get user notification preferences, creating defaults if needed."""
        return self._get_or_create_preferences(db, user_id)

    def update_preferences(
        self,
        db: Session,
        user_id: int,
        **kwargs: Any,
    ) -> NotificationPreferences:
        """Update user notification preferences."""
        prefs = self._get_or_create_preferences(db, user_id)

        valid_fields = {
            "email_enabled",
            "push_enabled",
            "sms_enabled",
            "session_reminders_enabled",
            "booking_requests_enabled",
            "learning_nudges_enabled",
            "review_prompts_enabled",
            "achievements_enabled",
            "marketing_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "preferred_notification_time",
            "max_daily_notifications",
            "max_weekly_nudges",
        }

        for key, value in kwargs.items():
            if key in valid_fields and value is not None:
                setattr(prefs, key, value)

        prefs.updated_at = datetime.now(UTC)
        return prefs

    # Convenience methods for common notification types

    def notify_booking_confirmed(
        self,
        db: Session,
        user_id: int,
        booking_id: int,
        subject_name: str,
        other_party_name: str,
        session_date: str,
        session_time: str,
        is_tutor: bool = False,
    ) -> Notification | None:
        """Send booking confirmation notification."""
        role = "tutor" if is_tutor else "student"
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message=f"Your {subject_name} session with {other_party_name} on {session_date} at {session_time} has been confirmed.",
            link=f"/{'tutor' if is_tutor else ''}bookings/{booking_id}",
            action_url=f"/{'tutor/' if is_tutor else ''}bookings/{booking_id}",
            action_label="View Booking",
            priority=2,
            metadata={"booking_id": booking_id, "role": role},
        )

    def notify_booking_cancelled(
        self,
        db: Session,
        user_id: int,
        booking_id: int,
        subject_name: str,
        session_date: str,
        cancelled_by: str,
    ) -> Notification | None:
        """Send booking cancellation notification."""
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.BOOKING_CANCELLED,
            title="Booking Cancelled",
            message=f"Your {subject_name} session on {session_date} has been cancelled by the {cancelled_by}.",
            link="/bookings",
            priority=2,
            metadata={"booking_id": booking_id, "cancelled_by": cancelled_by},
        )

    def notify_new_message(
        self,
        db: Session,
        user_id: int,
        sender_name: str,
        conversation_id: int,
        preview: str | None = None,
    ) -> Notification | None:
        """Send new message notification."""
        message_preview = f': "{preview[:50]}..."' if preview and len(preview) > 50 else (f': "{preview}"' if preview else "")
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.NEW_MESSAGE,
            title="New Message",
            message=f"You have a new message from {sender_name}{message_preview}",
            link=f"/messages/{conversation_id}",
            action_url=f"/messages/{conversation_id}",
            action_label="Reply",
            priority=3,
            metadata={"conversation_id": conversation_id, "sender_name": sender_name},
        )

    def notify_package_expiring(
        self,
        db: Session,
        user_id: int,
        package_id: int,
        subject_name: str,
        remaining_sessions: int,
        expires_in_days: int,
    ) -> Notification | None:
        """Send package expiring notification."""
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring Soon",
            message=f"Your {subject_name} package with {remaining_sessions} sessions remaining expires in {expires_in_days} days.",
            link="/packages",
            action_url="/packages",
            action_label="View Package",
            priority=2,
            metadata={
                "package_id": package_id,
                "remaining_sessions": remaining_sessions,
                "expires_in_days": expires_in_days,
            },
        )


# Singleton instance
notification_service = NotificationService()
