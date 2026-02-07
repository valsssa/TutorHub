"""Tests for Notification model soft delete columns."""

from sqlalchemy import inspect
from core.datetime_utils import utc_now

from models.notifications import Notification


def test_notification_has_deleted_at_column():
    """Notification model should have deleted_at column for soft delete."""
    mapper = inspect(Notification)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns


def test_notification_has_deleted_by_column():
    """Notification model should have deleted_by column for soft delete."""
    mapper = inspect(Notification)
    columns = {c.key for c in mapper.columns}
    assert "deleted_by" in columns


def test_notification_deleted_at_is_nullable():
    """deleted_at should be nullable (NULL means not deleted)."""
    mapper = inspect(Notification)
    col = mapper.columns["deleted_at"]
    assert col.nullable is True


def test_notification_deleted_by_is_nullable():
    """deleted_by should be nullable."""
    mapper = inspect(Notification)
    col = mapper.columns["deleted_by"]
    assert col.nullable is True


def test_notification_soft_delete_workflow(db_session):
    """Test that a notification can be soft-deleted by setting deleted_at."""
    from datetime import datetime

    from models.auth import User

    user = User(
        email="notif-test@example.com",
        hashed_password="hashed",
        role="student",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()

    notif = Notification(
        user_id=user.id,
        type="test",
        title="Test Notification",
        message="Test message",
    )
    db_session.add(notif)
    db_session.commit()

    assert notif.deleted_at is None

    notif.deleted_at = utc_now()
    notif.deleted_by = user.id
    db_session.commit()
    db_session.refresh(notif)

    assert notif.deleted_at is not None
    assert notif.deleted_by == user.id
