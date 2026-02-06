"""Tests for notifications API endpoints."""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from fastapi import status


@pytest.fixture
def test_notification(db_session, student_user):
    """Create a test notification."""
    from models import Notification

    notification = Notification(
        user_id=student_user.id,
        type="booking",
        title="New Booking",
        message="You have a new booking request",
        link="/bookings/1",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


@pytest.fixture
def multiple_notifications(db_session, student_user):
    """Create multiple test notifications."""
    from models import Notification

    notifications = []
    for i in range(5):
        notification = Notification(
            user_id=student_user.id,
            type="booking",
            title=f"Notification {i+1}",
            message=f"Message {i+1}",
            is_read=i % 2 == 0,  # Alternate read/unread
        )
        db_session.add(notification)
        notifications.append(notification)

    db_session.commit()
    for n in notifications:
        db_session.refresh(n)

    return notifications


class TestListNotifications:
    """Test GET /api/notifications endpoint."""

    def test_list_notifications_success(self, client, student_token, test_notification):
        """Test listing notifications successfully."""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_notifications_contains_fields(self, client, student_token, test_notification):
        """Test notification response contains required fields."""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()
        notification = data[0]

        assert "id" in notification
        assert "type" in notification
        assert "title" in notification
        assert "message" in notification
        assert "is_read" in notification
        assert "created_at" in notification

    def test_list_notifications_ordered_by_date(self, client, student_token, multiple_notifications):
        """Test notifications are ordered by date (newest first)."""
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        # Verify descending order by created_at
        dates = [n["created_at"] for n in data]
        assert dates == sorted(dates, reverse=True)

    def test_list_notifications_limited_to_50(self, client, student_token, db_session, student_user):
        """Test notifications list is limited to 50."""
        from models import Notification

        # Create 60 notifications
        for i in range(60):
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
        assert len(data) <= 50

    def test_list_notifications_only_own(self, client, student_token, admin_user, db_session):
        """Test user only sees own notifications."""
        from models import Notification

        # Create notification for admin user
        admin_notification = Notification(
            user_id=admin_user.id,
            type="admin",
            title="Admin Notification",
            message="For admin only",
            is_read=False,
        )
        db_session.add(admin_notification)
        db_session.commit()

        # Student should not see admin's notification
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()
        notification_ids = [n["id"] for n in data]
        assert admin_notification.id not in notification_ids

    def test_list_notifications_unauthenticated(self, client):
        """Test unauthenticated user cannot list notifications."""
        response = client.get("/api/v1/notifications")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMarkNotificationRead:
    """Test PATCH /api/notifications/{id}/read endpoint."""

    def test_mark_notification_read_success(self, client, student_token, test_notification):
        """Test marking notification as read."""
        response = client.patch(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "marked as read" in response.json()["message"].lower()

    def test_mark_notification_read_updates_db(self, client, student_token, test_notification, db_session):
        """Test that marking read actually updates database."""
        assert test_notification.is_read is False

        client.patch(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        db_session.refresh(test_notification)
        assert test_notification.is_read is True

    def test_mark_nonexistent_notification_returns_404(self, client, student_token):
        """Test marking nonexistent notification returns 404."""
        response = client.patch(
            "/api/v1/notifications/99999/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_mark_other_user_notification(self, client, admin_token, test_notification):
        """Test cannot mark another user's notification as read."""
        response = client.patch(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_already_read_notification(self, client, student_token, test_notification, db_session):
        """Test marking already read notification succeeds."""
        # Mark as read first
        test_notification.is_read = True
        db_session.commit()

        # Mark again
        response = client.patch(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK


class TestMarkAllNotificationsRead:
    """Test PATCH /api/notifications/mark-all-read endpoint."""

    def test_mark_all_read_success(self, client, student_token, multiple_notifications):
        """Test marking all notifications as read."""
        response = client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "all" in response.json()["message"].lower()

    def test_mark_all_read_updates_db(self, client, student_token, multiple_notifications, db_session):
        """Test that mark all read updates database."""
        # Verify some are unread
        unread_count = sum(1 for n in multiple_notifications if not n.is_read)
        assert unread_count > 0

        client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Refresh and check all are read
        for notification in multiple_notifications:
            db_session.refresh(notification)
            assert notification.is_read is True

    def test_mark_all_read_only_affects_own(self, client, student_token, admin_user, db_session):
        """Test mark all read only affects own notifications."""
        from models import Notification

        # Create unread notification for admin
        admin_notification = Notification(
            user_id=admin_user.id,
            type="admin",
            title="Admin Notification",
            message="For admin",
            is_read=False,
        )
        db_session.add(admin_notification)
        db_session.commit()

        # Student marks all read
        client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Admin's notification should still be unread
        db_session.refresh(admin_notification)
        assert admin_notification.is_read is False

    def test_mark_all_read_with_no_notifications(self, client, admin_token):
        """Test mark all read with no notifications succeeds."""
        response = client.patch(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK


class TestDeleteNotification:
    """Test DELETE /api/notifications/{id} endpoint."""

    def test_delete_notification_success(self, client, student_token, test_notification):
        """Test deleting notification successfully."""
        response = client.delete(
            f"/api/v1/notifications/{test_notification.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.json()["message"].lower()

    def test_delete_notification_removes_from_db(self, client, student_token, test_notification, db_session):
        """Test deletion actually removes from database."""
        from models import Notification

        notification_id = test_notification.id

        client.delete(
            f"/api/v1/notifications/{notification_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Verify deleted
        deleted = db_session.query(Notification).filter(Notification.id == notification_id).first()
        assert deleted is None

    def test_delete_nonexistent_notification_returns_404(self, client, student_token):
        """Test deleting nonexistent notification returns 404."""
        response = client.delete(
            "/api/v1/notifications/99999",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_other_user_notification(self, client, admin_token, test_notification):
        """Test cannot delete another user's notification."""
        response = client.delete(
            f"/api/v1/notifications/{test_notification.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_unauthenticated(self, client, test_notification):
        """Test unauthenticated user cannot delete."""
        response = client.delete(f"/api/v1/notifications/{test_notification.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestNotificationsIntegration:
    """Integration tests for notifications workflow."""

    def test_full_notification_workflow(self, client, student_token, db_session, student_user):
        """Test complete notification workflow."""
        from models import Notification

        # 1. Create notification directly in DB (simulating system creating it)
        notification = Notification(
            user_id=student_user.id,
            type="test",
            title="Test Notification",
            message="This is a test",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        notification_id = notification.id

        # 2. List - should see notification
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ids = [n["id"] for n in response.json()]
        assert notification_id in ids

        # 3. Mark as read
        response = client.patch(
            f"/api/v1/notifications/{notification_id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. Verify is_read in list
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        notification_data = next((n for n in response.json() if n["id"] == notification_id), None)
        assert notification_data is not None
        assert notification_data["is_read"] is True

        # 5. Delete
        response = client.delete(
            f"/api/v1/notifications/{notification_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. Verify deleted from list
        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ids = [n["id"] for n in response.json()]
        assert notification_id not in ids

    def test_notification_types(self, client, student_token, db_session, student_user):
        """Test different notification types are handled correctly."""
        from models import Notification

        types = ["booking", "message", "payment", "review", "system"]

        for notification_type in types:
            notification = Notification(
                user_id=student_user.id,
                type=notification_type,
                title=f"{notification_type.capitalize()} Notification",
                message=f"This is a {notification_type} notification",
                is_read=False,
            )
            db_session.add(notification)

        db_session.commit()

        response = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        data = response.json()

        # Verify all types are present
        response_types = {n["type"] for n in data}
        for t in types:
            assert t in response_types
