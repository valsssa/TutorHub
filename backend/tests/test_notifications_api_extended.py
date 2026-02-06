"""
Extended tests for Notifications API endpoints.

These tests extend the base test_notifications_api.py with additional coverage for:
- Pagination
- Filtering by type/category
- Bulk mark-as-read
- Notification preferences endpoints
- Dismiss functionality
- Edge cases
"""

from datetime import time as dt_time

import pytest
from fastapi import status

from models import Notification, NotificationPreferences


@pytest.fixture
def many_notifications(db_session, student_user):
    """Create many notifications for pagination testing."""
    notifications = []
    categories = ["booking", "message", "payment", "review", "system"]

    for i in range(75):
        notification = Notification(
            user_id=student_user.id,
            type=categories[i % len(categories)],
            category=categories[i % len(categories)],
            title=f"Notification {i + 1}",
            message=f"Message content {i + 1}",
            is_read=(i % 3 == 0),  # Every 3rd notification is read
            priority=((i % 5) + 1),  # Priority 1-5
        )
        db_session.add(notification)
        notifications.append(notification)

    db_session.commit()
    for n in notifications:
        db_session.refresh(n)

    return notifications


@pytest.fixture
def notifications_by_category(db_session, student_user):
    """Create notifications with specific categories for filtering tests."""
    categories = {
        "booking": [],
        "message": [],
        "payment": [],
    }

    for category, notif_list in categories.items():
        for i in range(3):
            notification = Notification(
                user_id=student_user.id,
                type=category,
                category=category,
                title=f"{category.capitalize()} Notification {i + 1}",
                message=f"{category} message {i + 1}",
                is_read=False,
            )
            db_session.add(notification)
            notif_list.append(notification)

    db_session.commit()
    for notifs in categories.values():
        for n in notifs:
            db_session.refresh(n)

    return categories


class TestNotificationsPagination:
    """Test pagination for notifications list."""

    def test_pagination_default_limit(self, client, student_token, many_notifications):
        """Test that default limit is applied."""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Default limit is 50
        assert len(data["items"]) <= 50
        assert data["total"] == 75

    def test_pagination_custom_limit(self, client, student_token, many_notifications):
        """Test custom limit parameter."""
        response = client.get(
            "/api/v1/notifications?limit=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert len(data["items"]) == 10
        assert data["total"] == 75

    def test_pagination_skip_offset(self, client, student_token, many_notifications):
        """Test skip parameter for pagination."""
        # Get first page
        response1 = client.get(
            "/api/v1/notifications?limit=10&skip=0",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        page1_ids = [n["id"] for n in response1.json()["items"]]

        # Get second page
        response2 = client.get(
            "/api/v1/notifications?limit=10&skip=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        page2_ids = [n["id"] for n in response2.json()["items"]]

        # Pages should not overlap
        assert not set(page1_ids).intersection(set(page2_ids))

    def test_pagination_returns_total_count(self, client, student_token, many_notifications):
        """Test that total count is always returned."""
        response = client.get(
            "/api/v1/notifications?limit=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert "total" in data
        assert data["total"] == 75
        assert len(data["items"]) == 5

    def test_pagination_skip_beyond_total(self, client, student_token, many_notifications):
        """Test skipping beyond total returns empty list."""
        response = client.get(
            "/api/v1/notifications?skip=100",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 75

    def test_pagination_limit_max_100(self, client, student_token, many_notifications):
        """Test that limit is capped at 100."""
        response = client.get(
            "/api/v1/notifications?limit=200",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should either cap at 100 or return validation error
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert len(data["items"]) <= 100
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestNotificationsFiltering:
    """Test filtering notifications."""

    def test_filter_by_category(self, client, student_token, notifications_by_category):
        """Test filtering notifications by category."""
        response = client.get(
            "/api/v1/notifications?category=booking",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert all(n["category"] == "booking" for n in data["items"])
        assert data["total"] == 3

    def test_filter_unread_only(self, client, student_token, many_notifications, db_session):
        """Test filtering to show only unread notifications."""
        # Count actual unread
        unread_count = sum(1 for n in many_notifications if not n.is_read)

        response = client.get(
            "/api/v1/notifications?unread_only=true",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert all(n["is_read"] is False for n in data["items"])
        assert data["total"] == unread_count

    def test_filter_combined(self, client, student_token, many_notifications):
        """Test combining multiple filters."""
        response = client.get(
            "/api/v1/notifications?category=booking&unread_only=true&limit=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert len(data["items"]) <= 5
        for item in data["items"]:
            assert item["category"] == "booking"
            assert item["is_read"] is False


class TestUnreadCount:
    """Test unread notification count endpoint."""

    def test_get_unread_count(self, client, student_token, many_notifications):
        """Test getting unread notification count."""
        # Calculate expected unread count
        expected_unread = sum(1 for n in many_notifications if not n.is_read)

        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "count" in data
        assert data["count"] == expected_unread

    def test_unread_count_updates_after_mark_read(self, client, student_token, many_notifications):
        """Test that unread count updates after marking as read."""
        # Get initial count
        response1 = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        initial_count = response1.json()["count"]

        # Mark all as read
        client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Get new count
        response2 = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        new_count = response2.json()["count"]

        assert new_count == 0
        assert new_count < initial_count

    def test_unread_count_zero_when_no_notifications(self, client, admin_token):
        """Test unread count is 0 when user has no notifications."""
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0


class TestDismissNotification:
    """Test dismiss notification functionality."""

    def test_dismiss_notification_success(self, client, student_token, db_session, student_user):
        """Test dismissing a notification."""
        # Create a notification
        notification = Notification(
            user_id=student_user.id,
            type="test",
            title="Dismissable",
            message="This can be dismissed",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        response = client.patch(
            f"/api/v1/notifications/{notification.id}/dismiss",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "dismissed" in response.json()["message"].lower()

    def test_dismissed_notification_not_in_list(self, client, student_token, db_session, student_user):
        """Test that dismissed notifications don't appear in list."""
        # Create and dismiss notification
        notification = Notification(
            user_id=student_user.id,
            type="test",
            title="To be dismissed",
            message="Will disappear",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()
        notification_id = notification.id

        # Dismiss it
        client.patch(
            f"/api/v1/notifications/{notification_id}/dismiss",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Check it's not in list
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ids = [n["id"] for n in response.json()["items"]]
        assert notification_id not in ids

    def test_dismiss_nonexistent_notification(self, client, student_token):
        """Test dismissing nonexistent notification returns 404."""
        response = client.patch(
            "/api/v1/notifications/99999/dismiss",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_dismiss_other_user_notification(
        self, client, admin_token, db_session, student_user
    ):
        """Test cannot dismiss another user's notification."""
        notification = Notification(
            user_id=student_user.id,
            type="test",
            title="Student's notification",
            message="Belongs to student",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        response = client.patch(
            f"/api/v1/notifications/{notification.id}/dismiss",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestNotificationPreferences:
    """Test notification preferences endpoints."""

    def test_get_preferences_creates_default(self, client, student_token, student_user, db_session):
        """Test getting preferences creates default if none exist."""
        # Ensure no preferences exist
        db_session.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == student_user.id
        ).delete()
        db_session.commit()

        response = client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Should have default values
        assert data["email_enabled"] is True
        assert data["push_enabled"] is True
        assert data["session_reminders_enabled"] is True

    def test_get_preferences_returns_all_fields(self, client, student_token):
        """Test that preferences response contains all expected fields."""
        response = client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        expected_fields = [
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
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_update_preferences_success(self, client, student_token):
        """Test updating notification preferences."""
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "email_enabled": False,
                "marketing_enabled": True,
                "max_daily_notifications": 20,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["email_enabled"] is False
        assert data["marketing_enabled"] is True
        assert data["max_daily_notifications"] == 20

    def test_update_preferences_persists(self, client, student_token):
        """Test that preference updates persist."""
        # Update
        client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"push_enabled": False},
        )

        # Read back
        response = client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.json()["push_enabled"] is False

    def test_update_quiet_hours(self, client, student_token):
        """Test updating quiet hours."""
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["quiet_hours_start"] == "22:00"
        assert data["quiet_hours_end"] == "08:00"

    def test_update_invalid_time_format(self, client, student_token):
        """Test that invalid time format is rejected."""
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"quiet_hours_start": "invalid-time"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "time" in response.json()["detail"].lower()

    def test_update_preferred_notification_time(self, client, student_token):
        """Test updating preferred notification time."""
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"preferred_notification_time": "09:30"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["preferred_notification_time"] == "09:30"

    def test_update_notification_limits(self, client, student_token):
        """Test updating notification limits."""
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "max_daily_notifications": 50,
                "max_weekly_nudges": 10,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["max_daily_notifications"] == 50
        assert data["max_weekly_nudges"] == 10

    def test_update_notification_limits_validation(self, client, student_token):
        """Test notification limits validation."""
        # Test max_daily_notifications exceeds maximum
        response = client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"max_daily_notifications": 200},  # Exceeds max of 100
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_preferences_unauthenticated(self, client):
        """Test unauthenticated access to preferences is rejected."""
        response = client.get("/api/v1/notifications/preferences")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.put(
            "/api/v1/notifications/preferences",
            json={"email_enabled": False},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_partial_preferences_update(self, client, student_token):
        """Test that partial update only changes specified fields."""
        # Get initial preferences
        initial = client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
        ).json()

        # Update only one field
        client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"sms_enabled": True},
        )

        # Verify other fields unchanged
        updated = client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
        ).json()

        assert updated["sms_enabled"] is True
        assert updated["email_enabled"] == initial["email_enabled"]
        assert updated["push_enabled"] == initial["push_enabled"]


class TestNotificationsResponse:
    """Test notification list response structure."""

    def test_response_includes_unread_count(self, client, student_token, many_notifications):
        """Test that list response includes unread count."""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)

    def test_notification_fields_complete(self, client, student_token, db_session, student_user):
        """Test that notification response includes all expected fields."""
        # Create notification with all optional fields
        notification = Notification(
            user_id=student_user.id,
            type="test",
            title="Complete Notification",
            message="Full message",
            link="/test/link",
            category="test",
            priority=2,
            action_url="/action",
            action_label="Take Action",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        # Find our notification
        notif = next((n for n in data["items"] if n["title"] == "Complete Notification"), None)
        assert notif is not None

        assert notif["type"] == "test"
        assert notif["title"] == "Complete Notification"
        assert notif["message"] == "Full message"
        assert notif["link"] == "/test/link"
        assert notif["category"] == "test"
        assert notif["priority"] == 2
        assert notif["action_url"] == "/action"
        assert notif["action_label"] == "Take Action"


class TestNotificationsIntegrationExtended:
    """Extended integration tests for notifications."""

    def test_preferences_affect_notification_display(self, client, student_token, student_user, db_session):
        """Test full workflow with preferences and notifications."""
        # 1. Set preferences
        client.put(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "email_enabled": True,
                "session_reminders_enabled": True,
            },
        )

        # 2. Create notifications
        for i in range(5):
            notification = Notification(
                user_id=student_user.id,
                type="booking",
                title=f"Booking {i}",
                message=f"Booking notification {i}",
                is_read=False,
            )
            db_session.add(notification)
        db_session.commit()

        # 3. Verify unread count
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.json()["count"] == 5

        # 4. Mark all as read
        client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # 5. Verify count is now 0
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.json()["count"] == 0

    def test_notification_ordering_newest_first(self, client, student_token, db_session, student_user):
        """Test that notifications are ordered newest first."""
        import time

        # Create notifications with slight delay to ensure different timestamps
        for i in range(3):
            notification = Notification(
                user_id=student_user.id,
                type="test",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False,
            )
            db_session.add(notification)
            db_session.commit()

        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        # Verify descending order by created_at
        dates = [n["created_at"] for n in data["items"]]
        assert dates == sorted(dates, reverse=True)
