"""Tests for Conversation and Message model soft delete columns."""

from sqlalchemy import inspect
from core.datetime_utils import utc_now

from models.messages import Conversation, Message, MessageAttachment


def test_conversation_has_deleted_at():
    """Conversation model should have deleted_at for soft delete."""
    mapper = inspect(Conversation)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns


def test_conversation_has_deleted_by():
    """Conversation model should have deleted_by for soft delete."""
    mapper = inspect(Conversation)
    columns = {c.key for c in mapper.columns}
    assert "deleted_by" in columns


def test_message_has_deleted_at():
    """Message model should have deleted_at for soft delete."""
    mapper = inspect(Message)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns


def test_message_has_deleted_by():
    """Message model should have deleted_by for soft delete."""
    mapper = inspect(Message)
    columns = {c.key for c in mapper.columns}
    assert "deleted_by" in columns


def test_message_attachment_has_file_category():
    """MessageAttachment should have file_category column."""
    mapper = inspect(MessageAttachment)
    columns = {c.key for c in mapper.columns}
    assert "file_category" in columns


def test_message_attachment_has_deleted_at():
    """MessageAttachment should have deleted_at for soft delete."""
    mapper = inspect(MessageAttachment)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns


def test_conversation_soft_delete_workflow(db_session):
    """Test that a conversation can be soft-deleted."""
    from datetime import datetime

    from models.auth import User

    student = User(
        email="conv-student@example.com",
        hashed_password="hashed",
        role="student",
        first_name="Conv",
        last_name="Student",
    )
    tutor = User(
        email="conv-tutor@example.com",
        hashed_password="hashed",
        role="tutor",
        first_name="Conv",
        last_name="Tutor",
    )
    db_session.add_all([student, tutor])
    db_session.commit()

    conv = Conversation(
        student_id=student.id,
        tutor_id=tutor.id,
    )
    db_session.add(conv)
    db_session.commit()

    assert conv.deleted_at is None

    conv.deleted_at = utc_now()
    conv.deleted_by = student.id
    db_session.commit()
    db_session.refresh(conv)

    assert conv.deleted_at is not None
    assert conv.deleted_by == student.id
