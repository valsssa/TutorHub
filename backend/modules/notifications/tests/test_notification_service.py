"""Tests for the notification service."""

from unittest.mock import MagicMock, patch

import pytest

from modules.notifications.service import (
    NotificationCategory,
    NotificationService,
    NotificationType,
    notification_service,
)


class TestNotificationType:
    """Tests for NotificationType enum."""

    def test_all_types_defined(self):
        """Test all expected notification types are defined."""
        expected_types = [
            "booking_confirmed",
            "booking_cancelled",
            "booking_reminder",
            "booking_request",
            "booking_completed",
            "payment_received",
            "payment_failed",
            "payout_completed",
            "refund_processed",
            "new_message",
            "new_review",
            "review_prompt",
            "account_update",
            "system_announcement",
            "achievement_unlocked",
            "learning_nudge",
            "package_expiring",
            "package_expired",
        ]

        for type_name in expected_types:
            assert hasattr(NotificationType, type_name.upper())

    def test_types_are_strings(self):
        """Test notification types are string enums."""
        for type_value in NotificationType:
            assert isinstance(type_value.value, str)


class TestNotificationCategory:
    """Tests for NotificationCategory enum."""

    def test_all_categories_defined(self):
        """Test all expected categories are defined."""
        expected_categories = [
            "booking",
            "payment",
            "message",
            "review",
            "system",
            "achievement",
            "learning",
        ]

        for category in expected_categories:
            assert hasattr(NotificationCategory, category.upper())


class TestNotificationService:
    """Tests for NotificationService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create notification service instance."""
        return NotificationService()


class TestGetOrCreatePreferences:
    """Tests for _get_or_create_preferences method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    def test_returns_existing_preferences(self, service, mock_db):
        """Test returns existing preferences."""
        existing_prefs = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_prefs
        )

        result = service._get_or_create_preferences(mock_db, user_id=1)

        assert result == existing_prefs
        mock_db.add.assert_not_called()

    def test_creates_new_preferences(self, service, mock_db):
        """Test creates new preferences when none exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service._get_or_create_preferences(mock_db, user_id=1)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


class TestShouldNotify:
    """Tests for _should_notify method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    @pytest.fixture
    def default_prefs(self):
        """Create default preferences."""
        prefs = MagicMock()
        prefs.session_reminders_enabled = True
        prefs.booking_requests_enabled = True
        prefs.learning_nudges_enabled = True
        prefs.review_prompts_enabled = True
        prefs.achievements_enabled = True
        prefs.marketing_enabled = True
        prefs.email_enabled = True
        prefs.quiet_hours_start = None
        prefs.quiet_hours_end = None
        return prefs

    def test_session_reminder_disabled(self, service, default_prefs):
        """Test session reminder blocked when disabled."""
        default_prefs.session_reminders_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.BOOKING_REMINDER
        )

        assert should_create is False
        assert should_email is False

    def test_booking_request_disabled(self, service, default_prefs):
        """Test booking request blocked when disabled."""
        default_prefs.booking_requests_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.BOOKING_REQUEST
        )

        assert should_create is False

    def test_learning_nudge_disabled(self, service, default_prefs):
        """Test learning nudge blocked when disabled."""
        default_prefs.learning_nudges_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.LEARNING_NUDGE
        )

        assert should_create is False

    def test_review_prompt_disabled(self, service, default_prefs):
        """Test review prompt blocked when disabled."""
        default_prefs.review_prompts_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.REVIEW_PROMPT
        )

        assert should_create is False

    def test_achievement_disabled(self, service, default_prefs):
        """Test achievement blocked when disabled."""
        default_prefs.achievements_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.ACHIEVEMENT_UNLOCKED
        )

        assert should_create is False

    def test_email_disabled(self, service, default_prefs):
        """Test email not sent when disabled."""
        default_prefs.email_enabled = False

        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.BOOKING_CONFIRMED
        )

        assert should_create is True
        assert should_email is False

    def test_allows_notification_when_enabled(self, service, default_prefs):
        """Test notification allowed when all enabled."""
        should_create, should_email = service._should_notify(
            default_prefs, NotificationType.BOOKING_CONFIRMED
        )

        assert should_create is True
        assert should_email is True

    def test_accepts_string_type(self, service, default_prefs):
        """Test accepts string notification type."""
        should_create, should_email = service._should_notify(
            default_prefs, "booking_confirmed"
        )

        assert should_create is True


class TestCreateNotification:
    """Tests for create_notification method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    @pytest.fixture
    def mock_prefs(self):
        """Create mock preferences."""
        prefs = MagicMock()
        prefs.session_reminders_enabled = True
        prefs.booking_requests_enabled = True
        prefs.learning_nudges_enabled = True
        prefs.review_prompts_enabled = True
        prefs.achievements_enabled = True
        prefs.email_enabled = True
        prefs.quiet_hours_start = None
        prefs.quiet_hours_end = None
        return prefs

    def test_creates_notification(self, service, mock_db, mock_prefs):
        """Test notification is created."""
        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            with patch.object(service, "_send_email_notification"):
                with patch.object(service, "_track_analytics"):
                    service.create_notification(
                        db=mock_db,
                        user_id=1,
                        notification_type=NotificationType.BOOKING_CONFIRMED,
                        title="Test Title",
                        message="Test Message",
                        send_email=False,
                    )

                    mock_db.add.assert_called_once()
                    mock_db.flush.assert_called_once()

    def test_returns_none_when_blocked(self, service, mock_db, mock_prefs):
        """Test returns None when notification blocked."""
        mock_prefs.session_reminders_enabled = False

        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            result = service.create_notification(
                db=mock_db,
                user_id=1,
                notification_type=NotificationType.BOOKING_REMINDER,
                title="Reminder",
                message="Session starting",
            )

            assert result is None
            mock_db.add.assert_not_called()

    def test_sets_priority(self, service, mock_db, mock_prefs):
        """Test notification priority is set."""
        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            with patch.object(service, "_send_email_notification"):
                with patch.object(service, "_track_analytics"):
                    service.create_notification(
                        db=mock_db,
                        user_id=1,
                        notification_type=NotificationType.BOOKING_CONFIRMED,
                        title="Test",
                        message="Test",
                        priority=1,
                        send_email=False,
                    )

                    call_args = mock_db.add.call_args[0][0]
                    assert call_args.priority == 1


class TestGetUnreadCount:
    """Tests for get_unread_count method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    def test_returns_count(self, service, mock_db):
        """Test returns unread count."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = service.get_unread_count(mock_db, user_id=1)

        assert result == 5


class TestMarkAsRead:
    """Tests for mark_as_read method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    def test_marks_notification_read(self, service, mock_db):
        """Test marks notification as read."""
        mock_notification = MagicMock()
        mock_notification.is_read = False
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_notification
        )

        result = service.mark_as_read(mock_db, notification_id=1, user_id=1)

        assert result is True
        assert mock_notification.is_read is True
        assert mock_notification.read_at is not None

    def test_returns_false_if_not_found(self, service, mock_db):
        """Test returns False if notification not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.mark_as_read(mock_db, notification_id=999, user_id=1)

        assert result is False


class TestDismissNotification:
    """Tests for dismiss_notification method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    def test_dismisses_notification(self, service, mock_db):
        """Test dismisses notification."""
        mock_notification = MagicMock()
        mock_notification.dismissed_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_notification
        )

        result = service.dismiss_notification(mock_db, notification_id=1, user_id=1)

        assert result is True
        assert mock_notification.dismissed_at is not None

    def test_returns_false_if_not_found(self, service, mock_db):
        """Test returns False if notification not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.dismiss_notification(mock_db, notification_id=999, user_id=1)

        assert result is False


class TestUpdatePreferences:
    """Tests for update_preferences method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    @pytest.fixture
    def mock_prefs(self):
        """Create mock preferences."""
        prefs = MagicMock()
        prefs.email_enabled = True
        return prefs

    def test_updates_valid_fields(self, service, mock_db, mock_prefs):
        """Test updates valid preference fields."""
        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            service.update_preferences(
                mock_db,
                user_id=1,
                email_enabled=False,
                push_enabled=True,
            )

            assert mock_prefs.email_enabled is False
            assert mock_prefs.push_enabled is True

    def test_ignores_invalid_fields(self, service, mock_db, mock_prefs):
        """Test ignores invalid preference fields."""
        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            service.update_preferences(
                mock_db,
                user_id=1,
                invalid_field="value",
            )

            assert not hasattr(mock_prefs, "invalid_field")

    def test_ignores_none_values(self, service, mock_db, mock_prefs):
        """Test ignores None values."""
        mock_prefs.email_enabled = True

        with patch.object(service, "_get_or_create_preferences", return_value=mock_prefs):
            service.update_preferences(
                mock_db,
                user_id=1,
                email_enabled=None,
            )

            assert mock_prefs.email_enabled is True


class TestConvenienceMethods:
    """Tests for convenience notification methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NotificationService()

    def test_notify_booking_confirmed(self, service, mock_db):
        """Test booking confirmed notification."""
        with patch.object(service, "create_notification") as mock_create:
            service.notify_booking_confirmed(
                db=mock_db,
                user_id=1,
                booking_id=100,
                subject_name="Math",
                other_party_name="John Doe",
                session_date="Jan 15",
                session_time="10:00 AM",
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["notification_type"] == NotificationType.BOOKING_CONFIRMED
            assert "Math" in call_kwargs["message"]
            assert "John Doe" in call_kwargs["message"]

    def test_notify_booking_cancelled(self, service, mock_db):
        """Test booking cancelled notification."""
        with patch.object(service, "create_notification") as mock_create:
            service.notify_booking_cancelled(
                db=mock_db,
                user_id=1,
                booking_id=100,
                subject_name="Math",
                session_date="Jan 15",
                cancelled_by="tutor",
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["notification_type"] == NotificationType.BOOKING_CANCELLED

    def test_notify_new_message(self, service, mock_db):
        """Test new message notification."""
        with patch.object(service, "create_notification") as mock_create:
            service.notify_new_message(
                db=mock_db,
                user_id=1,
                sender_name="Jane Smith",
                conversation_id=50,
                preview="Hello, I have a question...",
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["notification_type"] == NotificationType.NEW_MESSAGE
            assert "Jane Smith" in call_kwargs["message"]

    def test_notify_package_expiring(self, service, mock_db):
        """Test package expiring notification."""
        with patch.object(service, "create_notification") as mock_create:
            service.notify_package_expiring(
                db=mock_db,
                user_id=1,
                package_id=10,
                subject_name="Physics",
                remaining_sessions=3,
                expires_in_days=7,
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["notification_type"] == NotificationType.PACKAGE_EXPIRING
            assert "Physics" in call_kwargs["message"]
            assert "3" in call_kwargs["message"]
            assert "7" in call_kwargs["message"]


class TestTypeCategoryMapping:
    """Tests for type to category mapping."""

    def test_all_types_have_categories(self):
        """Test all notification types have category mappings."""
        service = NotificationService()

        for ntype in NotificationType:
            assert ntype in service.TYPE_CATEGORIES, f"Missing category for {ntype}"

    def test_booking_types_in_booking_category(self):
        """Test booking types are in booking category."""
        service = NotificationService()

        booking_types = [
            NotificationType.BOOKING_CONFIRMED,
            NotificationType.BOOKING_CANCELLED,
            NotificationType.BOOKING_REMINDER,
            NotificationType.BOOKING_REQUEST,
            NotificationType.BOOKING_COMPLETED,
        ]

        for btype in booking_types:
            assert service.TYPE_CATEGORIES[btype] == NotificationCategory.BOOKING

    def test_payment_types_in_payment_category(self):
        """Test payment types are in payment category."""
        service = NotificationService()

        payment_types = [
            NotificationType.PAYMENT_RECEIVED,
            NotificationType.PAYMENT_FAILED,
            NotificationType.PAYOUT_COMPLETED,
            NotificationType.REFUND_PROCESSED,
        ]

        for ptype in payment_types:
            assert service.TYPE_CATEGORIES[ptype] == NotificationCategory.PAYMENT


class TestSingletonInstance:
    """Tests for singleton notification_service instance."""

    def test_singleton_exists(self):
        """Test singleton instance exists."""
        assert notification_service is not None
        assert isinstance(notification_service, NotificationService)
