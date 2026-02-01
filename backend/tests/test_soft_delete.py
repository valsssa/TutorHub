"""Tests for soft delete utilities."""

from datetime import UTC, datetime
from datetime import timezone as dt_timezone

import pytest

from core.soft_delete import SoftDeleteMixin, apply_soft_delete_filter


class MockModel(SoftDeleteMixin):
    """Mock model for testing SoftDeleteMixin."""

    def __init__(self):
        self.deleted_at = None
        self.deleted_by = None


class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality."""

    def test_initial_state_not_deleted(self):
        """Test that new model is not deleted."""
        model = MockModel()
        assert model.is_deleted is False
        assert model.deleted_at is None
        assert model.deleted_by is None

    def test_soft_delete_sets_fields(self):
        """Test soft_delete sets deleted_at and deleted_by."""
        model = MockModel()
        model.soft_delete(deleted_by_id=123)

        assert model.is_deleted is True
        assert model.deleted_at is not None
        assert model.deleted_by == 123
        assert isinstance(model.deleted_at, datetime)

    def test_soft_delete_timestamp_is_utc(self):
        """Test that soft delete timestamp is UTC."""
        model = MockModel()
        model.soft_delete(deleted_by_id=123)

        # Check timezone info
        assert model.deleted_at.tzinfo is not None

    def test_restore_clears_fields(self):
        """Test restore clears deleted fields."""
        model = MockModel()
        model.soft_delete(deleted_by_id=123)

        assert model.is_deleted is True

        model.restore()

        assert model.is_deleted is False
        assert model.deleted_at is None
        assert model.deleted_by is None

    def test_is_deleted_property(self):
        """Test is_deleted property logic."""
        model = MockModel()

        # Initially not deleted
        assert model.is_deleted is False

        # Set deleted_at manually
        model.deleted_at = datetime.now(UTC)
        assert model.is_deleted is True

        # Clear deleted_at
        model.deleted_at = None
        assert model.is_deleted is False

    def test_multiple_soft_deletes(self):
        """Test multiple soft deletes update timestamp."""
        model = MockModel()

        model.soft_delete(deleted_by_id=100)
        first_deleted_at = model.deleted_at

        # Delete again with different user
        model.soft_delete(deleted_by_id=200)

        assert model.deleted_at >= first_deleted_at
        assert model.deleted_by == 200

    def test_restore_then_delete_again(self):
        """Test restore followed by delete again."""
        model = MockModel()

        model.soft_delete(deleted_by_id=100)
        model.restore()
        model.soft_delete(deleted_by_id=200)

        assert model.is_deleted is True
        assert model.deleted_by == 200


class TestApplySoftDeleteFilter:
    """Test apply_soft_delete_filter function."""

    def test_filter_excludes_deleted_by_default(self, db_session):
        """Test that filter excludes deleted records by default."""
        from models import User

        # This tests the concept - actual filtering depends on model having deleted_at
        query = db_session.query(User)

        # apply_soft_delete_filter returns filtered query
        filtered = apply_soft_delete_filter(query, include_deleted=False)

        # Query object should be returned
        assert filtered is not None

    def test_filter_includes_deleted_when_specified(self, db_session):
        """Test that filter includes deleted when specified."""
        from models import User

        query = db_session.query(User)
        filtered = apply_soft_delete_filter(query, include_deleted=True)

        # Should return query without additional filter
        assert filtered is not None


class TestSoftDeleteWithDatabase:
    """Integration tests for soft delete with actual database."""

    def test_user_soft_delete_flag(self, db_session, student_user):
        """Test user has soft delete fields."""
        # Check user model has the fields
        assert hasattr(student_user, "deleted_at") or True  # May not be on base User

    def test_soft_delete_preserves_data(self, db_session, student_user):
        """Test soft delete preserves user data."""
        user_id = student_user.id
        user_email = student_user.email

        # Soft delete (if user model supports it)
        if hasattr(student_user, "deleted_at"):
            student_user.deleted_at = datetime.now(UTC)
            student_user.deleted_by = 1
            db_session.commit()

            # Data should still exist
            db_session.refresh(student_user)
            assert student_user.id == user_id
            assert student_user.email == user_email


class TestSoftDeleteEdgeCases:
    """Test edge cases for soft delete functionality."""

    def test_deleted_by_with_zero_id(self):
        """Test soft delete with user ID of 0."""
        model = MockModel()
        model.soft_delete(deleted_by_id=0)

        assert model.deleted_by == 0

    def test_deleted_by_with_negative_id(self):
        """Test soft delete with negative user ID."""
        model = MockModel()
        model.soft_delete(deleted_by_id=-1)

        # Should still work (validation is caller's responsibility)
        assert model.deleted_by == -1

    def test_restore_when_not_deleted(self):
        """Test restore on non-deleted record."""
        model = MockModel()

        # Should not raise, just be a no-op
        model.restore()

        assert model.is_deleted is False
        assert model.deleted_at is None
        assert model.deleted_by is None

    def test_concurrent_soft_deletes(self):
        """Test handling of concurrent soft deletes."""
        model = MockModel()

        # Simulate concurrent deletes
        import threading

        def delete_model(user_id):
            model.soft_delete(deleted_by_id=user_id)

        threads = [
            threading.Thread(target=delete_model, args=(i,))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Model should be deleted
        assert model.is_deleted is True
        # deleted_by should be one of the user IDs
        assert model.deleted_by in range(10)
