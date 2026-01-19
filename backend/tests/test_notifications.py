"""Tests for notification endpoints."""

from fastapi import status


class TestNotifications:
    """Test notification management."""

    def test_list_notifications_empty(self, client, student_token):
        """Test listing notifications when there are none."""
        response = client.get(
            "/api/notifications", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_user_notifications(
        self, client, student_token, student_user, db_session
    ):
        """Test user can list their own notifications."""
        from models import Notification

        # Create notifications for the user
        notif1 = Notification(
            user_id=student_user.id,
            type="booking_confirmed",
            title="Booking Confirmed",
            message="Your booking has been confirmed",
            is_read=False,
        )
        notif2 = Notification(
            user_id=student_user.id,
            type="message_received",
            title="New Message",
            message="You have a new message",
            is_read=True,
        )
        db_session.add_all([notif1, notif2])
        db_session.commit()

        response = client.get(
            "/api/notifications", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # Verify most recent first
        assert data[0]["id"] == notif2.id  # Most recent
        assert data[1]["id"] == notif1.id

    def test_notifications_only_returns_own(
        self, client, student_token, tutor_user, db_session
    ):
        """Test users only see their own notifications."""
        from models import Notification

        # Create notification for another user
        other_notif = Notification(
            user_id=tutor_user.id,
            type="test",
            title="Other User Notification",
            message="Should not see this",
            is_read=False,
        )
        db_session.add(other_notif)
        db_session.commit()

        response = client.get(
            "/api/notifications", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Should not see other user's notifications

    def test_list_notifications_unauthorized(self, client):
        """Test listing notifications without auth fails."""
        response = client.get("/api/notifications")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mark_notification_read(
        self, client, student_token, student_user, db_session
    ):
        """Test marking notification as read."""
        from models import Notification

        notif = Notification(
            user_id=student_user.id,
            type="test",
            title="Test Notification",
            message="Test message",
            is_read=False,
        )
        db_session.add(notif)
        db_session.commit()
        db_session.refresh(notif)

        response = client.patch(
            f"/api/notifications/{notif.id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "marked as read" in response.json()["message"].lower()

        # Verify it's marked as read
        db_session.refresh(notif)
        assert notif.is_read is True

    def test_mark_other_user_notification_read_fails(
        self, client, student_token, tutor_user, db_session
    ):
        """Test cannot mark another user's notification as read."""
        from models import Notification

        notif = Notification(
            user_id=tutor_user.id,
            type="test",
            title="Other User Notification",
            message="Test message",
            is_read=False,
        )
        db_session.add(notif)
        db_session.commit()

        response = client.patch(
            f"/api/notifications/{notif.id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_nonexistent_notification_read(self, client, student_token):
        """Test marking nonexistent notification fails."""
        response = client.patch(
            "/api/notifications/99999/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_all_notifications_read(
        self, client, student_token, student_user, db_session
    ):
        """Test marking all notifications as read."""
        from models import Notification

        # Create multiple unread notifications
        notifs = [
            Notification(
                user_id=student_user.id,
                type="test",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False,
            )
            for i in range(3)
        ]
        db_session.add_all(notifs)
        db_session.commit()

        response = client.patch(
            "/api/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "all notifications" in response.json()["message"].lower()

        # Verify all are marked as read
        for notif in notifs:
            db_session.refresh(notif)
            assert notif.is_read is True

    def test_mark_all_read_only_affects_own_notifications(
        self, client, student_token, student_user, tutor_user, db_session
    ):
        """Test marking all read only affects user's own notifications."""
        from models import Notification

        # Create notifications for both users
        student_notif = Notification(
            user_id=student_user.id,
            type="test",
            title="Student Notification",
            message="Test",
            is_read=False,
        )
        tutor_notif = Notification(
            user_id=tutor_user.id,
            type="test",
            title="Tutor Notification",
            message="Test",
            is_read=False,
        )
        db_session.add_all([student_notif, tutor_notif])
        db_session.commit()

        # Student marks all as read
        response = client.patch(
            "/api/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify only student's notification is marked
        db_session.refresh(student_notif)
        db_session.refresh(tutor_notif)
        assert student_notif.is_read is True
        assert tutor_notif.is_read is False

    def test_notifications_pagination_limit(
        self, client, student_token, student_user, db_session
    ):
        """Test notifications are limited to 50 recent items."""
        from models import Notification

        # Create 60 notifications
        notifs = [
            Notification(
                user_id=student_user.id,
                type="test",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False,
            )
            for i in range(60)
        ]
        db_session.add_all(notifs)
        db_session.commit()

        response = client.get(
            "/api/notifications", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 50  # Limited to 50
