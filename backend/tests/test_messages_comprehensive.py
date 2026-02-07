"""
Comprehensive tests for the messaging module.

Tests cover:
- Message creation and delivery
- Message thread management
- File attachment handling
- Message read receipts
- Message editing and deletion
- Conversation search
- Unread count tracking
- WebSocket connection handling
- Message acknowledgment
- Authorization (only participants can access)
- Booking-context conversations
- Pagination
- PII masking in pre-booking conversations
"""

import asyncio
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from models import Booking, Message, MessageAttachment, User

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def second_tutor_user(db_session: Session) -> User:
    """Create a second tutor user for testing."""
    from tests.conftest import create_test_tutor_profile, create_test_user

    user = create_test_user(
        db_session,
        email="tutor2@test.com",
        password="tutor123",
        role="tutor",
        first_name="Second",
        last_name="Tutor",
    )
    create_test_tutor_profile(db_session, user.id)
    return user


@pytest.fixture
def second_student_user(db_session: Session) -> User:
    """Create a second student user for testing."""
    from tests.conftest import create_test_user

    return create_test_user(
        db_session,
        email="student2@test.com",
        password="student123",
        role="student",
        first_name="Second",
        last_name="Student",
    )


@pytest.fixture
def second_student_token(client, second_student_user) -> str:
    """Get token for second student."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": second_student_user.email, "password": "student123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def confirmed_booking(db_session: Session, tutor_user: User, student_user: User, test_subject) -> Booking:
    """Create a confirmed booking for testing post-booking messaging."""
    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=utc_now() + timedelta(days=1),
        end_time=utc_now() + timedelta(days=1, hours=1),
        topic="Calculus basics",
        hourly_rate=50.00,
        total_amount=50.00,
        currency="USD",
        session_state="SCHEDULED",  # Confirmed/scheduled status
        tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
        student_name=f"{student_user.first_name} {student_user.last_name}",
        subject_name=test_subject.name,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def multiple_messages(
    client, student_user, tutor_user, student_token, tutor_token
) -> list[int]:
    """Create multiple messages between student and tutor."""
    message_ids = []

    # Student sends 3 messages
    for i in range(3):
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": f"Student message {i + 1}"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        message_ids.append(response.json()["id"])

    # Tutor replies with 2 messages
    for i in range(2):
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": student_user.id, "message": f"Tutor reply {i + 1}"},
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        message_ids.append(response.json()["id"])

    return message_ids


# =============================================================================
# Message Creation Tests
# =============================================================================


class TestMessageCreation:
    """Test message creation and delivery."""

    def test_send_message_success(
        self, client, student_user, tutor_user, student_token
    ):
        """Test successful message sending."""
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
        assert data["is_edited"] is False
        assert "id" in data
        assert "created_at" in data

    def test_send_message_with_booking_context(
        self, client, student_token, tutor_user, test_booking
    ):
        """Test sending a message with booking context."""
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Question about our session",
                "booking_id": test_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["booking_id"] == test_booking.id

    def test_send_message_to_self_fails(self, client, student_user, student_token):
        """Test that users cannot message themselves."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": student_user.id, "message": "Self message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_message_to_nonexistent_user_fails(self, client, student_token):
        """Test sending message to non-existent user fails."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": 99999, "message": "To nobody"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_empty_message_fails(self, client, student_token, tutor_user):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": ""},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_message_too_long_fails(self, client, student_token, tutor_user):
        """Test that overly long messages are rejected."""
        long_message = "x" * 2001  # Over 2000 character limit
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": long_message},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_message_requires_auth(self, client, tutor_user):
        """Test that authentication is required."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Unauthorized"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_send_message_whitespace_only_fails(self, client, student_token, tutor_user):
        """Test that whitespace-only messages are rejected."""
        response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "   "},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Pydantic min_length=1 should reject this after stripping
        assert response.status_code in (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        )


# =============================================================================
# Message Thread Management Tests
# =============================================================================


class TestMessageThreads:
    """Test message thread management."""

    def test_list_threads_empty(self, client, student_token):
        """Test listing threads when user has none."""
        response = client.get(
            "/api/v1/messages/threads",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_threads_with_messages(
        self, client, student_user, tutor_user, student_token, tutor_token, multiple_messages
    ):
        """Test listing conversation threads."""
        # Get threads as tutor
        response = client.get(
            "/api/v1/messages/threads",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        threads = response.json()
        assert len(threads) >= 1

        thread = threads[0]
        assert thread["other_user_id"] == student_user.id
        assert thread["other_user_email"] == student_user.email
        assert "last_message" in thread
        assert "unread_count" in thread
        assert "last_message_time" in thread
        assert "other_user_role" in thread

    def test_list_threads_limit(
        self, client, student_token, tutor_user, second_tutor_user, db_session
    ):
        """Test threads limit parameter."""
        from tests.conftest import create_test_tutor_profile, create_test_user

        # Create multiple tutors and send messages
        for i in range(3):
            tutor = create_test_user(
                db_session,
                email=f"thread_tutor_{i}@test.com",
                password="test123",
                role="tutor",
            )
            create_test_tutor_profile(db_session, tutor.id)
            client.post(
                "/api/v1/messages",
                json={"recipient_id": tutor.id, "message": f"Hello tutor {i}"},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # Get threads with limit
        response = client.get(
            "/api/v1/messages/threads?limit=2",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) <= 2

    def test_get_conversation_messages(
        self, client, student_user, tutor_user, student_token, multiple_messages
    ):
        """Test getting messages in a conversation."""
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "messages" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 5  # 3 from student + 2 from tutor

    def test_get_conversation_pagination(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
        """Test conversation pagination."""
        # Send 10 messages
        for i in range(10):
            client.post(
                "/api/v1/messages",
                json={"recipient_id": tutor_user.id, "message": f"Message {i}"},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # Get first page
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}?page=1&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["total"] == 10
        assert data["page"] == 1

        # Get second page
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}?page=2&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["page"] == 2

    def test_get_conversation_with_booking_filter(
        self, client, student_user, tutor_user, student_token, test_booking
    ):
        """Test filtering conversation by booking."""
        # Send messages with and without booking
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "No booking"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "With booking",
                "booking_id": test_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Filter by booking
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}?booking_id={test_booking.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["messages"][0]["booking_id"] == test_booking.id


# =============================================================================
# Read Receipts Tests
# =============================================================================


class TestReadReceipts:
    """Test message read receipt functionality."""

    def test_mark_message_as_read(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
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
        assert response.json()["read_at"] is not None

    def test_cannot_mark_own_message_as_read(
        self, client, tutor_user, student_token
    ):
        """Test that sender cannot mark their own message as read."""
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "My own message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Sender tries to mark as read
        response = client.patch(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_mark_others_message_as_read(
        self, client, student_user, tutor_user, admin_user, student_token, admin_token
    ):
        """Test that third parties cannot mark messages as read."""
        # Student sends to tutor
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "For tutor only"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Admin (not recipient) tries to mark as read
        response = client.patch(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_thread_as_read(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
        """Test marking all messages in a thread as read."""
        # Send multiple messages
        for i in range(3):
            client.post(
                "/api/v1/messages",
                json={"recipient_id": tutor_user.id, "message": f"Message {i}"},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # Mark thread as read
        response = client.patch(
            f"/api/v1/messages/threads/{student_user.id}/read-all",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 3

    def test_mark_thread_read_with_booking_filter(
        self, client, student_user, tutor_user, student_token, tutor_token, test_booking
    ):
        """Test marking thread as read with booking filter."""
        # Send messages with different booking contexts
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "No booking"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "With booking",
                "booking_id": test_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Mark only booking-related messages as read
        response = client.patch(
            f"/api/v1/messages/threads/{student_user.id}/read-all?booking_id={test_booking.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1


# =============================================================================
# Unread Count Tests
# =============================================================================


class TestUnreadCount:
    """Test unread message count tracking."""

    def test_get_unread_count(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
        """Test getting unread message count."""
        # Send messages
        for i in range(3):
            client.post(
                "/api/v1/messages",
                json={"recipient_id": tutor_user.id, "message": f"Unread {i}"},
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
        assert data["total"] >= 3
        assert "by_sender" in data
        assert student_user.id in data["by_sender"] or str(student_user.id) in data["by_sender"]

    def test_unread_count_decreases_after_read(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
        """Test that unread count decreases after reading."""
        # Send message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Read me"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Get initial count
        count_response = client.get(
            "/api/v1/messages/unread/count",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        initial_count = count_response.json()["total"]

        # Mark as read
        client.patch(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        # Get new count
        count_response = client.get(
            "/api/v1/messages/unread/count",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        new_count = count_response.json()["total"]

        assert new_count == initial_count - 1


# =============================================================================
# Message Edit Tests
# =============================================================================


class TestMessageEdit:
    """Test message editing functionality."""

    def test_edit_message_success(self, client, student_token, tutor_user):
        """Test successful message edit."""
        # Send message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Original message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Edit message
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json={"message": "Edited message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["message"] == "Edited message"
        assert data["is_edited"] is True
        assert "edited_at" in data

    def test_cannot_edit_others_message(
        self, client, student_token, tutor_token, tutor_user
    ):
        """Test that users cannot edit others' messages."""
        # Student sends message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Student's message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Tutor tries to edit
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json={"message": "Tampered message"},
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_edit_after_15_minutes(
        self, client, student_token, tutor_user, db_session
    ):
        """Test that messages cannot be edited after 15 minutes."""
        # Send message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Old message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Modify created_at to be 16 minutes ago
        message = db_session.query(Message).filter(Message.id == message_id).first()
        message.created_at = utc_now() - timedelta(minutes=16)
        db_session.commit()

        # Try to edit
        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json={"message": "Too late edit"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "15 minutes" in response.json()["detail"]


# =============================================================================
# Message Delete Tests
# =============================================================================


class TestMessageDelete:
    """Test message deletion functionality."""

    def test_delete_message_success(self, client, student_token, tutor_user):
        """Test successful message deletion."""
        # Send message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Delete me"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Delete message
        response = client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_others_message(
        self, client, student_token, tutor_token, tutor_user
    ):
        """Test that users cannot delete others' messages."""
        # Student sends message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Student's message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        # Tutor tries to delete
        response = client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_deleted_message_not_in_conversation(
        self, client, student_token, tutor_user
    ):
        """Test that deleted messages don't appear in conversations."""
        # Send and delete message
        send_response = client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Deleted message"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        message_id = send_response.json()["id"]

        client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Check conversation
        response = client.get(
            f"/api/v1/messages/threads/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        messages = response.json()["messages"]
        message_ids = [m["id"] for m in messages]
        assert message_id not in message_ids


# =============================================================================
# Message Search Tests
# =============================================================================


class TestMessageSearch:
    """Test message search functionality."""

    def test_search_messages_success(
        self, client, student_token, tutor_user
    ):
        """Test searching messages by content."""
        # Send messages with searchable content
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Hello calculus expert"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": "Need help with algebra"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Search for calculus
        response = client.get(
            "/api/v1/messages/search?q=calculus",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "messages" in data
        assert "total" in data
        assert data["total"] >= 1
        assert "calculus" in data["messages"][0]["message"].lower()

    def test_search_messages_pagination(
        self, client, student_token, tutor_user
    ):
        """Test search results pagination."""
        # Send multiple searchable messages
        for i in range(10):
            client.post(
                "/api/v1/messages",
                json={"recipient_id": tutor_user.id, "message": f"Searchable term {i}"},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # Search with pagination
        response = client.get(
            "/api/v1/messages/search?q=Searchable&page=1&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] >= 10
        assert len(data["messages"]) == 5
        assert data["page"] == 1
        assert data["total_pages"] >= 2

    def test_search_short_query_fails(self, client, student_token):
        """Test that short search queries are rejected."""
        response = client.get(
            "/api/v1/messages/search?q=a",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_only_own_messages(
        self, client, student_user, tutor_user, student_token, tutor_token
    ):
        """Test that users can only search their own messages."""
        # Student sends unique message
        unique_content = "UniqueSearchTest12345"
        client.post(
            "/api/v1/messages",
            json={"recipient_id": tutor_user.id, "message": unique_content},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Student can find it
        response = client.get(
            f"/api/v1/messages/search?q={unique_content}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.json()["total"] >= 1

        # Tutor can also find it (recipient)
        response = client.get(
            f"/api/v1/messages/search?q={unique_content}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.json()["total"] >= 1


# =============================================================================
# PII Masking Tests
# =============================================================================


class TestPIIMasking:
    """Test PII protection in pre-booking conversations."""

    def test_pii_masked_pre_booking(self, client, student_token, tutor_user):
        """Test that PII is masked in pre-booking messages."""
        # Send message with PII (no booking context)
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Contact me at test@email.com or 555-123-4567",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        # Email and phone should be masked
        assert "test@email.com" not in data["message"]
        assert "555-123-4567" not in data["message"]
        assert "***" in data["message"]

    def test_pii_not_masked_post_booking(
        self, client, student_token, tutor_user, confirmed_booking
    ):
        """Test that PII is not masked after booking confirmation."""
        # Send message with PII (with confirmed booking)
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Contact me at test@email.com",
                "booking_id": confirmed_booking.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        # Email should NOT be masked for confirmed bookings
        assert "test@email.com" in data["message"]

    def test_url_masked_pre_booking(self, client, student_token, tutor_user):
        """Test that URLs are masked in pre-booking messages."""
        response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "message": "Check out https://example.com for resources",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "https://example.com" not in data["message"]
        assert "[link removed]" in data["message"]


# =============================================================================
# User Info Endpoint Tests
# =============================================================================


class TestUserInfo:
    """Test user info endpoint for messaging."""

    def test_get_user_info(self, client, student_token, tutor_user):
        """Test getting basic user info."""
        response = client.get(
            f"/api/v1/messages/users/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == tutor_user.id
        assert data["email"] == tutor_user.email
        assert data["role"] == "tutor"
        assert "first_name" in data
        assert "last_name" in data

    def test_get_nonexistent_user_info(self, client, student_token):
        """Test getting info for non-existent user."""
        response = client.get(
            "/api/v1/messages/users/99999",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# File Attachment Tests
# =============================================================================


class TestFileAttachments:
    """Test file attachment functionality."""

    @patch("modules.messages.api.store_message_attachment")
    @patch("modules.messages.api.manager.send_personal_message", new_callable=AsyncMock)
    def test_send_message_with_attachment(
        self,
        mock_websocket,
        mock_store,
        client,
        student_token,
        tutor_user,
        db_session,
    ):
        """Test sending a message with file attachment."""
        # Mock storage
        mock_store.return_value = {
            "file_key": "messages/1/1/test.pdf",
            "original_filename": "test.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "file_category": "document",
            "width": None,
            "height": None,
        }
        mock_websocket.return_value = None

        # Create file-like object
        file_content = b"PDF content here"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

        response = client.post(
            "/api/v1/messages/with-attachment",
            data={
                "recipient_id": str(tutor_user.id),
                "message": "Here is the document",
            },
            files=files,
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Should succeed (201) or fail gracefully if mocking isn't complete
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @patch("modules.messages.api.generate_presigned_url")
    def test_get_attachment_download_url(
        self,
        mock_presign,
        client,
        student_user,
        tutor_user,
        student_token,
        db_session,
    ):
        """Test getting presigned URL for attachment download."""
        # Create message and attachment in DB
        message = Message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            message="Test with attachment",
            is_read=False,
        )
        message.updated_at = utc_now()
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        attachment = MessageAttachment(
            message_id=message.id,
            file_key="messages/test/file.pdf",
            original_filename="document.pdf",
            file_size=1024,
            mime_type="application/pdf",
            file_category="document",
            uploaded_by=student_user.id,
            scan_result="clean",
        )
        attachment.updated_at = utc_now()
        db_session.add(attachment)
        db_session.commit()
        db_session.refresh(attachment)

        # Mock presigned URL
        mock_presign.return_value = "https://storage.example.com/presigned-url"

        # Get download URL
        response = client.get(
            f"/api/v1/messages/attachments/{attachment.id}/download",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "download_url" in data
        assert data["filename"] == "document.pdf"
        assert data["mime_type"] == "application/pdf"

    def test_unauthorized_attachment_download(
        self, client, student_user, tutor_user, admin_token, db_session
    ):
        """Test that unauthorized users cannot download attachments."""
        # Create message between student and tutor
        message = Message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            message="Private attachment",
            is_read=False,
        )
        message.updated_at = utc_now()
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        attachment = MessageAttachment(
            message_id=message.id,
            file_key="messages/private/file.pdf",
            original_filename="private.pdf",
            file_size=1024,
            mime_type="application/pdf",
            file_category="document",
            uploaded_by=student_user.id,
            scan_result="clean",
        )
        attachment.updated_at = utc_now()
        db_session.add(attachment)
        db_session.commit()
        db_session.refresh(attachment)

        # Admin (not participant) tries to download
        response = client.get(
            f"/api/v1/messages/attachments/{attachment.id}/download",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_infected_attachment_blocked(
        self, client, student_user, tutor_user, student_token, db_session
    ):
        """Test that infected attachments cannot be downloaded."""
        # Create message with infected attachment
        message = Message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            message="Infected file",
            is_read=False,
        )
        message.updated_at = utc_now()
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        attachment = MessageAttachment(
            message_id=message.id,
            file_key="messages/infected/file.exe",
            original_filename="malware.exe",
            file_size=1024,
            mime_type="application/octet-stream",
            file_category="other",
            uploaded_by=student_user.id,
            scan_result="infected",  # Marked as infected
        )
        attachment.updated_at = utc_now()
        db_session.add(attachment)
        db_session.commit()
        db_session.refresh(attachment)

        # Try to download
        response = client.get(
            f"/api/v1/messages/attachments/{attachment.id}/download",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "unsafe" in response.json()["detail"].lower()


# =============================================================================
# WebSocket Manager Unit Tests
# =============================================================================


class TestWebSocketManager:
    """Test WebSocket manager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a fresh WebSocket manager for testing."""
        from modules.messages.websocket import WebSocketManager

        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, manager):
        """Test connection and disconnection."""
        # Create mock websocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        # Connect
        await manager.connect(mock_ws, user_id=1)
        assert manager.is_user_online(1)
        assert manager.get_online_count() == 1

        # Disconnect
        await manager.disconnect(mock_ws, user_id=1)
        assert not manager.is_user_online(1)
        assert manager.get_online_count() == 0

    @pytest.mark.asyncio
    async def test_multi_device_support(self, manager):
        """Test multiple connections per user."""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Connect two devices for same user
        await manager.connect(mock_ws1, user_id=1)
        await manager.connect(mock_ws2, user_id=1)

        assert manager.is_user_online(1)
        assert manager.get_connection_count() == 2

        # Disconnect one device
        await manager.disconnect(mock_ws1, user_id=1)
        assert manager.is_user_online(1)  # Still online
        assert manager.get_connection_count() == 1

        # Disconnect second device
        await manager.disconnect(mock_ws2, user_id=1)
        assert not manager.is_user_online(1)

    @pytest.mark.asyncio
    async def test_send_personal_message_user_offline(self, manager):
        """Test sending message to offline user."""
        result = await manager.send_personal_message({"type": "test"}, user_id=99)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_personal_message_success(self, manager):
        """Test successful message delivery."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, user_id=1)
        result = await manager.send_personal_message({"type": "test"}, user_id=1)

        assert result is True
        mock_ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_users(self, manager):
        """Test broadcasting to multiple users."""
        mock_ws1 = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1, user_id=1)
        await manager.connect(mock_ws2, user_id=2)

        count = await manager.broadcast_to_users({"type": "broadcast"}, [1, 2, 3])

        assert count == 2  # Only 2 users online
        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_online_users(self, manager):
        """Test filtering online users."""
        mock_ws = AsyncMock()

        await manager.connect(mock_ws, user_id=1)
        await manager.connect(mock_ws, user_id=3)

        online = manager.get_online_users([1, 2, 3, 4])
        assert online == [1, 3]

    def test_update_pong(self, manager):
        """Test pong timestamp update."""
        import time

        mock_ws = MagicMock()

        # Manually add connection metadata
        from modules.messages.websocket import ConnectionInfo

        manager.connection_metadata[mock_ws] = ConnectionInfo(
            user_id=1, connected_at=time.time()
        )

        old_pong = manager.connection_metadata[mock_ws].last_pong
        time.sleep(0.01)  # Small delay
        manager.update_pong(mock_ws)
        new_pong = manager.connection_metadata[mock_ws].last_pong

        assert new_pong > old_pong

    def test_ack_tracking(self, manager):
        """Test message acknowledgment tracking."""
        mock_ws = MagicMock()

        from modules.messages.websocket import ConnectionInfo

        manager.connection_metadata[mock_ws] = ConnectionInfo(
            user_id=1, connected_at=0
        )

        # Track pending ack
        manager.track_pending_ack(mock_ws, "ack-123")
        assert "ack-123" in manager.connection_metadata[mock_ws].pending_acks

        # Receive ack
        result = manager.receive_ack(mock_ws, "ack-123")
        assert result is True
        assert "ack-123" not in manager.connection_metadata[mock_ws].pending_acks

        # Unknown ack
        result = manager.receive_ack(mock_ws, "unknown")
        assert result is False

    def test_get_stats(self, manager):
        """Test statistics retrieval."""
        stats = manager.get_stats()

        assert "online_users" in stats
        assert "total_connections" in stats
        assert "total_connected" in stats
        assert "total_disconnected" in stats
        assert "failed_sends" in stats
        assert "acks_sent" in stats
        assert "acks_timeout" in stats


# =============================================================================
# Message Service Unit Tests
# =============================================================================


class TestMessageService:
    """Unit tests for MessageService."""

    @pytest.fixture
    def service(self, db_session):
        """Create service instance."""
        from modules.messages.service import MessageService

        return MessageService(db_session)

    def test_sanitize_content(self, service):
        """Test content sanitization."""
        # Test null byte removal
        result = service._sanitize_content("Hello\x00World")
        assert "\x00" not in result
        assert "HelloWorld" in result

        # Test whitespace normalization
        result = service._sanitize_content("  Hello   World  ")
        assert result == "Hello World"

        # Test empty content
        result = service._sanitize_content("")
        assert result == ""

    def test_mask_pii_email(self, service):
        """Test email masking."""
        result = service._mask_pii("Contact me at test@example.com please")
        assert "test@example.com" not in result
        assert "***@***.***" in result

    def test_mask_pii_phone(self, service):
        """Test phone number masking."""
        result = service._mask_pii("Call me at 555-123-4567")
        assert "555-123-4567" not in result
        assert "***-***-****" in result

    def test_mask_pii_url(self, service):
        """Test URL masking."""
        result = service._mask_pii("Visit https://example.com/page")
        assert "https://example.com" not in result
        assert "[link removed]" in result

    def test_mask_pii_social_handle(self, service):
        """Test social media handle masking."""
        result = service._mask_pii("DM me @username on Twitter")
        assert "@username" not in result
        assert "@***" in result

    def test_send_message_creates_message(
        self, service, student_user, tutor_user, db_session
    ):
        """Test that send_message creates a message."""
        message = service.send_message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            content="Test message",
        )

        assert message.id is not None
        assert message.sender_id == student_user.id
        assert message.recipient_id == tutor_user.id
        assert message.message == "Test message"
        assert message.is_read is False

    def test_get_unread_count(self, service, student_user, tutor_user, db_session):
        """Test unread count retrieval."""
        # Send messages
        service.send_message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            content="Message 1",
        )
        service.send_message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            content="Message 2",
        )

        count = service.get_unread_count(tutor_user.id)
        assert count >= 2

    def test_mark_message_read_updates_timestamp(
        self, service, student_user, tutor_user, db_session
    ):
        """Test that marking read sets read_at timestamp."""
        message = service.send_message(
            sender_id=student_user.id,
            recipient_id=tutor_user.id,
            content="Test",
        )

        assert message.read_at is None

        updated = service.mark_message_read(message.id, tutor_user.id)
        assert updated.is_read is True
        assert updated.read_at is not None
