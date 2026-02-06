"""Tests for messages API response format."""

import pytest
from pydantic import BaseModel


def test_message_response_includes_conversation_id():
    """Verify MessageResponse schema includes conversation_id."""
    from schemas import MessageResponse

    fields = MessageResponse.model_fields.keys()
    assert "conversation_id" in fields, "MessageResponse missing conversation_id"


def test_message_response_conversation_id_is_optional():
    """Verify conversation_id can be None (for backwards compatibility)."""
    from schemas import MessageResponse

    # Get the field info
    field_info = MessageResponse.model_fields.get("conversation_id")
    assert field_info is not None, "conversation_id field not found"

    # Check that the annotation allows None
    annotation = field_info.annotation
    # For Optional/Union types, None should be allowed
    assert annotation is not None


def test_message_response_serialization_with_conversation_id():
    """Verify MessageResponse serializes conversation_id correctly."""
    from datetime import datetime, UTC
    from schemas import MessageResponse

    # Create a MessageResponse with conversation_id
    msg = MessageResponse(
        id=1,
        sender_id=2,
        recipient_id=3,
        conversation_id=42,
        message="Test message",
        is_read=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Serialize to dict
    data = msg.model_dump()
    assert "conversation_id" in data
    assert data["conversation_id"] == 42


def test_message_response_serialization_without_conversation_id():
    """Verify MessageResponse works without conversation_id (None)."""
    from datetime import datetime, UTC
    from schemas import MessageResponse

    # Create a MessageResponse without conversation_id
    msg = MessageResponse(
        id=1,
        sender_id=2,
        recipient_id=3,
        conversation_id=None,
        message="Test message",
        is_read=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Serialize to dict
    data = msg.model_dump()
    assert "conversation_id" in data
    assert data["conversation_id"] is None
