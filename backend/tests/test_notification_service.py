"""
Comprehensive tests for the Notification Service module.

Tests cover:
- Notification creation for different types (booking, message, system)
- Email delivery via Brevo
- Notification preferences (respect user settings)
- Notification marking as read
- Notification listing and filtering
- Batch notification creation
- Notification templating
- Error handling and edge cases
"""

from datetime import UTC, datetime, time, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from models import Notification, NotificationAnalytics, NotificationPreferences, User
from modules.notifications.service import (
    NotificationCategory,
    NotificationService,
    NotificationType,
    notification_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def notification_svc() -> NotificationService:
    """Fresh NotificationService instance for each test."""
    return NotificationService()


@pytest.fixture
def user_with_preferences(db_session: Session, student_user: User) -> User:
    """Create a user with custom notification preferences."""
    prefs = NotificationPreferences(
        user_id=student_user.id,
        email_enabled=True,
        push_enabled=True,
        session_reminders_enabled=True,
        booking_requests_enabled=True,
        learning_nudges_enabled=True,
        review_prompts_enabled=True,
        achievements_enabled=True,
        marketing_enabled=False,
        max_daily_notifications=10,
        max_weekly_nudges=3,
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(student_user)
    return student_user


@pytest.fixture
def user_with_disabled_email(db_session: Session, student_user: User) -> User:
    """Create a user with email notifications disabled."""
    prefs = NotificationPreferences(
        user_id=student_user.id,
        email_enabled=False,
        push_enabled=True,
    )
    db_session.add(prefs)
    db_session.commit()
    return student_user


@pytest.fixture
def user_with_quiet_hours(db_session: Session, student_user: User) -> User:
    """Create a user with quiet hours configured (covers full day for testing)."""
    prefs = NotificationPreferences(
        user_id=student_user.id,
        email_enabled=True,
        quiet_hours_start=time(0, 0),
        quiet_hours_end=time(23, 59),
    )
    db_session.add(prefs)
    db_session.commit()
    return student_user


@pytest.fixture
def user_with_disabled_reminders(db_session: Session, student_user: User) -> User:
    """Create a user with session reminders disabled."""
    prefs = NotificationPreferences(
        user_id=student_user.id,
        email_enabled=True,
        session_reminders_enabled=False,
    )
    db_session.add(prefs)
    db_session.commit()
    return student_user


@pytest.fixture
def sample_notifications(db_session: Session, student_user: User) -> list[Notification]:
    """Create sample notifications for testing."""
    notifications = []
    types = [
        ("booking_confirmed", "Booking Confirmed", NotificationCategory.BOOKING.value),
        ("new_message", "New Message", NotificationCategory.MESSAGE.value),
        ("system_announcement", "System Update", NotificationCategory.SYSTEM.value),
        ("payment_received", "Payment Received", NotificationCategory.PAYMENT.value),
        ("new_review", "New Review", NotificationCategory.REVIEW.value),
    ]

    for i, (type_val, title, category) in enumerate(types):
        notification = Notification(
            user_id=student_user.id,
            type=type_val,
            title=title,
            message=f"Test message {i}",
            category=category,
            priority=3,
            is_read=False,
            sent_at=datetime.now(UTC),
        )
        db_session.add(notification)
        notifications.append(notification)

    db_session.commit()
    for n in notifications:
        db_session.refresh(n)

    return notifications


# =============================================================================
# Test Notification Creation for Different Types
# =============================================================================


class TestNotificationCreation:
    """Tests for creating notifications of different types."""

    def test_create_booking_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a booking confirmation notification."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            link="/bookings/123",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "booking_confirmed"
        assert notification.title == "Booking Confirmed"
        assert notification.category == NotificationCategory.BOOKING.value
        assert notification.user_id == student_user.id

    def test_create_message_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a new message notification."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.NEW_MESSAGE,
            title="New Message",
            message="You have a new message from John",
            link="/messages/456",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "new_message"
        assert notification.category == NotificationCategory.MESSAGE.value

    def test_create_system_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a system announcement notification."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="System Update",
            message="New features available",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "system_announcement"
        assert notification.category == NotificationCategory.SYSTEM.value

    def test_create_payment_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a payment notification."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            title="Payment Received",
            message="Your payment of $50 has been received",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "payment_received"
        assert notification.category == NotificationCategory.PAYMENT.value

    def test_create_review_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a review notification."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.NEW_REVIEW,
            title="New Review",
            message="You received a 5-star review",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "new_review"
        assert notification.category == NotificationCategory.REVIEW.value

    def test_create_notification_with_action_url(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a notification with action button."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_REQUEST,
            title="New Booking Request",
            message="A student wants to book a session",
            action_url="/tutor/bookings/123/respond",
            action_label="Respond",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.action_url == "/tutor/bookings/123/respond"
        assert notification.action_label == "Respond"

    def test_create_notification_with_metadata(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a notification with extra metadata."""
        metadata = {"booking_id": 123, "amount": 50.00}
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            title="Payment",
            message="Payment received",
            metadata=metadata,
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        # Note: metadata is stored in extra_data field in model

    def test_create_notification_with_priority(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a notification with high priority."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.PAYMENT_FAILED,
            title="Payment Failed",
            message="Your payment could not be processed",
            priority=1,
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.priority == 1

    def test_create_notification_with_string_type(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating a notification using string type instead of enum."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type="booking_confirmed",
            title="Booking",
            message="Your booking is confirmed",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "booking_confirmed"


# =============================================================================
# Test Email Delivery
# =============================================================================


class TestEmailDelivery:
    """Tests for email notification delivery via Brevo."""

    @patch("modules.notifications.service.email_service")
    def test_send_email_notification_success(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test successful email delivery."""
        mock_email_service._send_email.return_value = True

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            send_email=True,
        )
        db_session.commit()

        assert notification is not None
        mock_email_service._send_email.assert_called_once()

    @patch("modules.notifications.service.email_service")
    def test_email_not_sent_when_disabled(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test that email is not sent when send_email=False."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        mock_email_service._send_email.assert_not_called()

    @patch("modules.notifications.service.email_service")
    def test_email_not_sent_when_user_disabled_email(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
        user_with_disabled_email: User,
    ):
        """Test that email is not sent when user has email disabled in preferences."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=user_with_disabled_email.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            send_email=True,
        )
        db_session.commit()

        assert notification is not None
        mock_email_service._send_email.assert_not_called()

    @patch("modules.notifications.service.email_service")
    def test_email_not_sent_during_quiet_hours(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
        user_with_quiet_hours: User,
    ):
        """Test that email is not sent during user's quiet hours."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=user_with_quiet_hours.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            send_email=True,
        )
        db_session.commit()

        assert notification is not None
        mock_email_service._send_email.assert_not_called()

    @patch("modules.notifications.service.email_service")
    def test_email_delivery_failure_does_not_block_notification(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test that notification is created even if email fails."""
        mock_email_service._send_email.return_value = False

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            send_email=True,
        )
        db_session.commit()

        assert notification is not None
        assert notification.id is not None

    @patch("modules.notifications.service.email_service")
    def test_email_not_sent_for_missing_user(
        self,
        mock_email_service: MagicMock,
        db_session: Session,
        notification_svc: NotificationService,
    ):
        """Test email delivery handles missing user gracefully."""
        # Directly test _send_email_notification with invalid user
        notification = Notification(
            user_id=99999,  # Non-existent user
            type="test",
            title="Test",
            message="Test message",
        )

        result = notification_svc._send_email_notification(
            db=db_session,
            user_id=99999,
            notification=notification,
        )

        assert result is False
        mock_email_service._send_email.assert_not_called()


# =============================================================================
# Test Notification Preferences
# =============================================================================


class TestNotificationPreferences:
    """Tests for notification preference handling."""

    def test_get_or_create_preferences_creates_new(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that preferences are created if they don't exist."""
        prefs = notification_svc._get_or_create_preferences(db_session, student_user.id)
        db_session.commit()

        assert prefs is not None
        assert prefs.user_id == student_user.id
        assert prefs.email_enabled is True  # Default value

    def test_get_or_create_preferences_returns_existing(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        user_with_preferences: User,
    ):
        """Test that existing preferences are returned."""
        prefs = notification_svc._get_or_create_preferences(
            db_session, user_with_preferences.id
        )

        assert prefs is not None
        assert prefs.user_id == user_with_preferences.id

    def test_notification_blocked_by_disabled_reminders(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        user_with_disabled_reminders: User,
    ):
        """Test that booking reminders are blocked when disabled."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=user_with_disabled_reminders.id,
            notification_type=NotificationType.BOOKING_REMINDER,
            title="Reminder",
            message="Your session is tomorrow",
            send_email=False,
        )
        db_session.commit()

        # Notification should be blocked (None returned)
        assert notification is None

    def test_notification_blocked_by_disabled_booking_requests(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that booking requests are blocked when disabled."""
        # Set up preferences with booking requests disabled
        prefs = NotificationPreferences(
            user_id=student_user.id,
            booking_requests_enabled=False,
        )
        db_session.add(prefs)
        db_session.commit()

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_REQUEST,
            title="Booking Request",
            message="New booking request",
            send_email=False,
        )
        db_session.commit()

        assert notification is None

    def test_notification_blocked_by_disabled_learning_nudges(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that learning nudges are blocked when disabled."""
        prefs = NotificationPreferences(
            user_id=student_user.id,
            learning_nudges_enabled=False,
        )
        db_session.add(prefs)
        db_session.commit()

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.LEARNING_NUDGE,
            title="Learning Nudge",
            message="Time to practice!",
            send_email=False,
        )
        db_session.commit()

        assert notification is None

    def test_notification_blocked_by_disabled_review_prompts(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that review prompts are blocked when disabled."""
        prefs = NotificationPreferences(
            user_id=student_user.id,
            review_prompts_enabled=False,
        )
        db_session.add(prefs)
        db_session.commit()

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.REVIEW_PROMPT,
            title="Review Prompt",
            message="How was your session?",
            send_email=False,
        )
        db_session.commit()

        assert notification is None

    def test_notification_blocked_by_disabled_achievements(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that achievements are blocked when disabled."""
        prefs = NotificationPreferences(
            user_id=student_user.id,
            achievements_enabled=False,
        )
        db_session.add(prefs)
        db_session.commit()

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.ACHIEVEMENT_UNLOCKED,
            title="Achievement",
            message="You unlocked a badge!",
            send_email=False,
        )
        db_session.commit()

        assert notification is None

    def test_update_preferences(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test updating notification preferences."""
        prefs = notification_svc.update_preferences(
            db=db_session,
            user_id=student_user.id,
            email_enabled=False,
            push_enabled=False,
            max_daily_notifications=5,
        )
        db_session.commit()

        assert prefs.email_enabled is False
        assert prefs.push_enabled is False
        assert prefs.max_daily_notifications == 5

    def test_update_preferences_quiet_hours(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test updating quiet hours in preferences."""
        prefs = notification_svc.update_preferences(
            db=db_session,
            user_id=student_user.id,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
        )
        db_session.commit()

        assert prefs.quiet_hours_start == time(22, 0)
        assert prefs.quiet_hours_end == time(8, 0)

    def test_get_user_preferences(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test getting user preferences."""
        prefs = notification_svc.get_user_preferences(db_session, student_user.id)
        db_session.commit()

        assert prefs is not None
        assert prefs.user_id == student_user.id


# =============================================================================
# Test Notification Marking as Read
# =============================================================================


class TestMarkAsRead:
    """Tests for marking notifications as read."""

    def test_mark_notification_as_read(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        student_user: User,
    ):
        """Test marking a notification as read."""
        notification = sample_notifications[0]
        assert notification.is_read is False

        result = notification_svc.mark_as_read(
            db=db_session,
            notification_id=notification.id,
            user_id=student_user.id,
        )
        db_session.commit()

        assert result is True
        db_session.refresh(notification)
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_mark_nonexistent_notification_returns_false(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test marking non-existent notification returns False."""
        result = notification_svc.mark_as_read(
            db=db_session,
            notification_id=99999,
            user_id=student_user.id,
        )

        assert result is False

    def test_mark_other_user_notification_returns_false(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        tutor_user: User,
    ):
        """Test marking another user's notification returns False."""
        notification = sample_notifications[0]

        result = notification_svc.mark_as_read(
            db=db_session,
            notification_id=notification.id,
            user_id=tutor_user.id,
        )

        assert result is False


# =============================================================================
# Test Dismiss Notification
# =============================================================================


class TestDismissNotification:
    """Tests for dismissing notifications."""

    def test_dismiss_notification(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        student_user: User,
    ):
        """Test dismissing a notification."""
        notification = sample_notifications[0]
        assert notification.dismissed_at is None

        result = notification_svc.dismiss_notification(
            db=db_session,
            notification_id=notification.id,
            user_id=student_user.id,
        )
        db_session.commit()

        assert result is True
        db_session.refresh(notification)
        assert notification.dismissed_at is not None

    def test_dismiss_nonexistent_notification_returns_false(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test dismissing non-existent notification returns False."""
        result = notification_svc.dismiss_notification(
            db=db_session,
            notification_id=99999,
            user_id=student_user.id,
        )

        assert result is False


# =============================================================================
# Test Unread Count
# =============================================================================


class TestUnreadCount:
    """Tests for getting unread notification count."""

    def test_get_unread_count(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        student_user: User,
    ):
        """Test getting unread notification count."""
        count = notification_svc.get_unread_count(db_session, student_user.id)

        assert count == len(sample_notifications)

    def test_get_unread_count_excludes_read(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        student_user: User,
    ):
        """Test that read notifications are excluded from count."""
        # Mark one as read
        sample_notifications[0].is_read = True
        db_session.commit()

        count = notification_svc.get_unread_count(db_session, student_user.id)

        assert count == len(sample_notifications) - 1

    def test_get_unread_count_excludes_dismissed(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        sample_notifications: list[Notification],
        student_user: User,
    ):
        """Test that dismissed notifications are excluded from count."""
        # Dismiss one notification
        sample_notifications[0].dismissed_at = datetime.now(UTC)
        db_session.commit()

        count = notification_svc.get_unread_count(db_session, student_user.id)

        assert count == len(sample_notifications) - 1

    def test_get_unread_count_for_user_with_no_notifications(
        self, db_session: Session, notification_svc: NotificationService, tutor_user: User
    ):
        """Test getting unread count for user with no notifications."""
        count = notification_svc.get_unread_count(db_session, tutor_user.id)

        assert count == 0


# =============================================================================
# Test Batch Notification Creation
# =============================================================================


class TestBatchNotifications:
    """Tests for creating multiple notifications."""

    def test_create_multiple_notifications(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating multiple notifications for the same user."""
        types = [
            NotificationType.BOOKING_CONFIRMED,
            NotificationType.NEW_MESSAGE,
            NotificationType.PAYMENT_RECEIVED,
        ]

        created = []
        for i, notification_type in enumerate(types):
            notification = notification_svc.create_notification(
                db=db_session,
                user_id=student_user.id,
                notification_type=notification_type,
                title=f"Notification {i}",
                message=f"Message {i}",
                send_email=False,
            )
            if notification:
                created.append(notification)

        db_session.commit()

        assert len(created) == 3
        for notification in created:
            assert notification.id is not None

    def test_create_notifications_for_multiple_users(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
        tutor_user: User,
    ):
        """Test creating notifications for different users."""
        user_ids = [student_user.id, tutor_user.id]
        created = []

        for user_id in user_ids:
            notification = notification_svc.create_notification(
                db=db_session,
                user_id=user_id,
                notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
                title="System Update",
                message="Important update",
                send_email=False,
            )
            if notification:
                created.append(notification)

        db_session.commit()

        assert len(created) == 2
        assert created[0].user_id == student_user.id
        assert created[1].user_id == tutor_user.id


# =============================================================================
# Test Convenience Methods (Notification Templates)
# =============================================================================


class TestConvenienceMethods:
    """Tests for convenience notification methods."""

    def test_notify_booking_confirmed_student(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test booking confirmation notification for student."""
        notification = notification_svc.notify_booking_confirmed(
            db=db_session,
            user_id=student_user.id,
            booking_id=123,
            subject_name="Mathematics",
            other_party_name="John Smith",
            session_date="2024-01-15",
            session_time="10:00 AM",
            is_tutor=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "booking_confirmed"
        assert "Mathematics" in notification.message
        assert "John Smith" in notification.message
        assert notification.link == "/bookings/123"

    def test_notify_booking_confirmed_tutor(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        tutor_user: User,
    ):
        """Test booking confirmation notification for tutor."""
        notification = notification_svc.notify_booking_confirmed(
            db=db_session,
            user_id=tutor_user.id,
            booking_id=123,
            subject_name="Physics",
            other_party_name="Jane Doe",
            session_date="2024-01-15",
            session_time="2:00 PM",
            is_tutor=True,
        )
        db_session.commit()

        assert notification is not None
        assert "/tutor" in notification.link

    def test_notify_booking_cancelled(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test booking cancellation notification."""
        notification = notification_svc.notify_booking_cancelled(
            db=db_session,
            user_id=student_user.id,
            booking_id=456,
            subject_name="Chemistry",
            session_date="2024-01-20",
            cancelled_by="tutor",
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "booking_cancelled"
        assert "Chemistry" in notification.message
        assert "tutor" in notification.message

    def test_notify_new_message(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test new message notification."""
        notification = notification_svc.notify_new_message(
            db=db_session,
            user_id=student_user.id,
            sender_name="Alice",
            conversation_id=789,
            preview="Hello, can we reschedule?",
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "new_message"
        assert "Alice" in notification.message
        assert notification.link == "/messages/789"

    def test_notify_new_message_long_preview_truncated(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test that long message preview is truncated."""
        long_message = "A" * 100

        notification = notification_svc.notify_new_message(
            db=db_session,
            user_id=student_user.id,
            sender_name="Bob",
            conversation_id=101,
            preview=long_message,
        )
        db_session.commit()

        assert notification is not None
        assert "..." in notification.message
        assert len(notification.message) < len(long_message) + 50

    def test_notify_package_expiring(
        self,
        db_session: Session,
        notification_svc: NotificationService,
        student_user: User,
    ):
        """Test package expiring notification."""
        notification = notification_svc.notify_package_expiring(
            db=db_session,
            user_id=student_user.id,
            package_id=50,
            subject_name="English",
            remaining_sessions=3,
            expires_in_days=7,
        )
        db_session.commit()

        assert notification is not None
        assert notification.type == "package_expiring"
        assert "English" in notification.message
        assert "3 sessions" in notification.message
        assert "7 days" in notification.message


# =============================================================================
# Test Analytics Tracking
# =============================================================================


class TestAnalyticsTracking:
    """Tests for notification analytics tracking."""

    def test_analytics_created_with_notification(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that analytics entry is created with notification."""
        notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Test",
            message="Test message",
            send_email=False,
        )
        db_session.commit()

        analytics = (
            db_session.query(NotificationAnalytics)
            .filter(NotificationAnalytics.user_id == student_user.id)
            .first()
        )

        assert analytics is not None
        assert analytics.template_key == "booking_confirmed"
        assert analytics.delivery_channel == "in_app"

    def test_analytics_tracks_actionable(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that analytics tracks whether notification was actionable."""
        notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_REQUEST,
            title="Booking Request",
            message="New request",
            action_url="/respond",
            send_email=False,
        )
        db_session.commit()

        analytics = (
            db_session.query(NotificationAnalytics)
            .filter(NotificationAnalytics.user_id == student_user.id)
            .first()
        )

        assert analytics is not None
        assert analytics.was_actionable is True


# =============================================================================
# Test Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_notification_with_empty_title(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating notification with empty title."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="",
            message="Message content",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.title == ""

    def test_notification_with_empty_message(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating notification with empty message."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="Title",
            message="",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.message == ""

    def test_notification_with_very_long_message(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test creating notification with very long message."""
        long_message = "A" * 5000

        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="Long Message",
            message=long_message,
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert len(notification.message) == 5000

    def test_notification_type_category_mapping(
        self, notification_svc: NotificationService
    ):
        """Test that all notification types have category mappings."""
        for notification_type in NotificationType:
            category = notification_svc.TYPE_CATEGORIES.get(notification_type)
            assert category is not None, f"Missing category mapping for {notification_type}"

    def test_unknown_notification_type_gets_system_category(
        self, db_session: Session, notification_svc: NotificationService, student_user: User
    ):
        """Test that unknown notification type defaults to system category."""
        notification = notification_svc.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type="unknown_type",
            title="Unknown",
            message="Unknown notification",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.category == NotificationCategory.SYSTEM.value


# =============================================================================
# Test Singleton Instance
# =============================================================================


class TestSingletonInstance:
    """Tests for the singleton notification_service instance."""

    def test_singleton_instance_exists(self):
        """Test that singleton instance is available."""
        assert notification_service is not None
        assert isinstance(notification_service, NotificationService)

    def test_singleton_creates_notification(
        self, db_session: Session, student_user: User
    ):
        """Test that singleton can create notifications."""
        notification = notification_service.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="Singleton Test",
            message="Testing singleton",
            send_email=False,
        )
        db_session.commit()

        assert notification is not None
        assert notification.title == "Singleton Test"
