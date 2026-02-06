"""Tests for notification soft delete functionality."""
from sqlalchemy import inspect

from models.notifications import Notification


def test_notification_has_deleted_at_column():
    """Test that Notification model has deleted_at column for soft delete."""
    mapper = inspect(Notification)
    column_names = [c.key for c in mapper.columns]
    assert "deleted_at" in column_names


def test_notification_has_deleted_by_column():
    """Test that Notification model has deleted_by column for soft delete."""
    mapper = inspect(Notification)
    column_names = [c.key for c in mapper.columns]
    assert "deleted_by" in column_names
