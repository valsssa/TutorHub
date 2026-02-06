"""Tests for message soft delete functionality."""
from sqlalchemy import inspect

from models.messages import Conversation, Message, MessageAttachment


def test_conversation_has_deleted_at():
    """Test that Conversation model has deleted_at column for soft delete."""
    mapper = inspect(Conversation)
    assert "deleted_at" in [c.key for c in mapper.columns]


def test_conversation_has_deleted_by():
    """Test that Conversation model has deleted_by column for soft delete tracking."""
    mapper = inspect(Conversation)
    assert "deleted_by" in [c.key for c in mapper.columns]


def test_message_attachment_has_file_category():
    """Test that MessageAttachment model has file_category column."""
    mapper = inspect(MessageAttachment)
    assert "file_category" in [c.key for c in mapper.columns]


def test_message_has_deleted_at():
    """Test that Message model has deleted_at column for soft delete."""
    mapper = inspect(Message)
    assert "deleted_at" in [c.key for c in mapper.columns]


def test_message_has_deleted_by():
    """Test that Message model has deleted_by column for soft delete tracking."""
    mapper = inspect(Message)
    assert "deleted_by" in [c.key for c in mapper.columns]


def test_message_attachment_has_deleted_at():
    """Test that MessageAttachment model has deleted_at column for soft delete."""
    mapper = inspect(MessageAttachment)
    assert "deleted_at" in [c.key for c in mapper.columns]
