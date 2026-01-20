"""Tests for messaging system."""

from fastapi import status


class TestMessaging:
    """Test message creation and retrieval."""

    def test_send_message_success(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test sending a message between users."""
        response = client.post(
            "/api/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Hello, I need help with calculus",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["sender_id"] == student_user.id
        assert data["recipient_id"] == tutor_user.id
        assert data["message"] == "Hello, I need help with calculus"
        assert data["is_read"] is False

    def test_list_user_messages(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test listing messages for a user."""
        # Send multiple messages
        client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 2"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Get messages as tutor
        response = client.get("/api/messages", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_200_OK

        messages = response.json()
        assert len(messages) >= 2

        # Verify message structure
        msg = messages[0]
        assert "id" in msg
        assert "sender_id" in msg
        assert "recipient_id" in msg
        assert "message" in msg
        assert "is_read" in msg
        assert "created_at" in msg

    def test_mark_message_as_read(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test marking a message as read."""
        # Send message
        send_response = client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": "Please read this"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Mark as read
        response = client.patch(
            f"/api/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's marked as read
        get_response = client.get("/api/messages", headers={"Authorization": f"Bearer {tutor_token}"})
        messages = get_response.json()
        marked_msg = next(m for m in messages if m["id"] == message_id)
        assert marked_msg["is_read"] is True

    def test_cannot_mark_others_message_as_read(
        self,
        client,
        student_user,
        tutor_user,
        admin_user,
        student_token,
        tutor_token,
        admin_token,
    ):
        """Test that users cannot mark messages they didn't receive as read."""
        # Student sends to tutor
        send_response = client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": "For tutor only"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Admin (not recipient) tries to mark as read
        response = client.patch(
            f"/api/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_message_with_booking_context(self, client, student_token, tutor_user, test_booking):
        """Test sending a message related to a booking."""
        response = client.post(
            "/api/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Question about our upcoming session",
                "booking_id": test_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["booking_id"] == test_booking.id

    def test_send_message_requires_auth(self, client, tutor_user):
        """Test that sending messages requires authentication."""
        response = client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": "Unauthorized message"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_send_empty_message_fails(self, client, student_token, tutor_user):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/messages",
            json={"recipient_id": tutor_user.id, "message": ""},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_message_to_nonexistent_user(self, client, student_token):
        """Test sending message to non-existent user."""
        response = client.post(
            "/api/messages",
            json={"recipient_id": 99999, "message": "To nobody"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
