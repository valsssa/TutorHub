"""Tests for messaging system."""

from fastapi import status


class TestMessaging:
    """Test message creation and retrieval."""

    def test_send_message_success(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test sending a message between users."""
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Hello, I need help with calculus",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["sender_id"] == student_user.id
        assert data["recipient_id"] == tutor_user.id
        assert data["message"] == "Hello, I need help with calculus"
        assert data["is_read"] is False

    def test_list_conversation_threads(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test listing conversation threads for a user."""
        # Send multiple messages
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 2"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Get threads as tutor
        response = client.get("/api/v1/messages/threads", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_200_OK

        threads = response.json()
        assert len(threads) >= 1

        # Verify thread structure
        thread = threads[0]
        assert "other_user_id" in thread
        assert "other_user_email" in thread
        assert "last_message" in thread
        assert "unread_count" in thread

    def test_get_conversation_messages(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test getting messages in a conversation."""
        # Send messages
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Hello tutor"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={"recipient_id": student_user.id, "message": "Hello student"},
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        # Get conversation
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "messages" in data
        assert "total" in data
        assert len(data["messages"]) >= 2

    def test_mark_message_as_read(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test marking a message as read."""
        # Send message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Please read this"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Mark as read by recipient
        response = client.patch(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "read_at" in response.json()

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
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "For tutor only"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Admin (not recipient) tries to mark as read - returns 404 as message not found for this user
        response = client.patch(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_send_message_with_booking_context(self, client, student_token, tutor_user, test_booking):
        """Test sending a message related to a booking."""
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Question about our upcoming session",
                "booking_id": test_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["booking_id"] == test_booking.id

    def test_send_message_requires_auth(self, client, tutor_user):
        """Test that sending messages requires authentication."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Unauthorized message"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_send_empty_message_fails(self, client, student_token, tutor_user):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": ""},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_message_to_nonexistent_user(self, client, student_token):
        """Test sending message to non-existent user."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": 99999, "message": "To nobody"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # API returns 400 for validation errors (user not found is a validation error)
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

    def test_get_unread_count(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test getting unread message count."""
        # Send a message
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Unread message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Get unread count as recipient
        response = client.get(
            "/api/v1/messages/unread/count",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "total" in data
        assert data["total"] >= 1

    def test_mark_thread_as_read(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test marking all messages in a thread as read."""
        # Send messages
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 1"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Message 2"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Mark thread as read
        response = client.patch(
            f"/api/v1/messages/threads/{student_user.id}/read-all",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.json()

    def test_search_messages(self, client, student_user, tutor_user, student_token, tutor_token):
        """Test searching messages by content."""
        # Send a message with searchable content
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Hello calculus expert"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Search for message
        response = client.get(
            "/api/v1/messages/search?q=calculus",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "messages" in data
        assert "total" in data
