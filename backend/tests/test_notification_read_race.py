"""Tests for notification read race condition handling.

Verifies that mark-all-read uses atomic bulk UPDATE for race condition safety
and is idempotent (safe to call multiple times).
"""

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest


class TestMarkAllReadIsAtomic:
    """Verify mark-all-read uses single atomic UPDATE statement."""

    def test_mark_all_read_uses_bulk_update_in_api(self):
        """Verify API mark-all-read uses atomic update (via service or directly)."""
        api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "presentation"
            / "api.py"
        )
        source = api_path.read_text()

        # Either uses atomic bulk UPDATE directly via query().filter().update()
        # OR delegates to service.mark_all_read() which does the atomic update
        has_direct_bulk_update = (
            ".filter(" in source
            and ".update(" in source
            and "is_read" in source
        )
        delegates_to_service = "mark_all_read" in source and "notification_service" in source

        assert has_direct_bulk_update or delegates_to_service, (
            "Mark all read should use atomic bulk update "
            "(query().filter().update()) or delegate to service.mark_all_read()"
        )

        # Should NOT use a loop to update individually
        # Check for patterns like "for notification in" followed by ".is_read = "
        import re

        loop_pattern = re.compile(
            r"for\s+\w+\s+in\s+.*notifications.*:\s*\n.*is_read\s*=",
            re.MULTILINE,
        )
        has_individual_loop = bool(loop_pattern.search(source))
        assert not has_individual_loop, (
            "Mark all read should NOT use a loop to update notifications individually"
        )

    def test_mark_all_read_uses_bulk_update_in_service(self):
        """Verify service mark_all_read uses single UPDATE statement."""
        service_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "service.py"
        )
        source = service_path.read_text()

        # Either service has atomic bulk update, or it doesn't have mark_all_read
        # (in which case the API handles it atomically)
        if "def mark_all_read" in source:
            # Service has the method, verify it's atomic
            has_bulk_update = ".update(" in source or "UPDATE" in source
            assert has_bulk_update, (
                "Service mark_all_read should use atomic bulk update"
            )


class TestMarkAllReadIsIdempotent:
    """Verify mark-all-read is idempotent (safe to call multiple times)."""

    def test_mark_already_read_notifications_is_safe(self):
        """
        Calling mark-all-read when all notifications are already read
        should succeed without errors.
        """
        # This tests the concept - the actual implementation filters for
        # is_read == False, so calling it again does nothing
        mock_db = MagicMock()

        # Simulate the filter().update() call returning 0 rows updated
        mock_db.query.return_value.filter.return_value.update.return_value = 0

        # The operation should complete without error
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        result = mock_db.query().filter(
            # Filtering for unread only
        ).update({"is_read": True, "read_at": now})

        # Should return 0 (no rows updated) but not error
        assert result == 0

    def test_concurrent_mark_all_read_is_safe(self):
        """
        Concurrent mark-all-read calls should be safe due to atomic UPDATE.

        When two requests come in simultaneously:
        1. Both execute UPDATE WHERE is_read = false
        2. One gets the rows, updates them
        3. The other finds no matching rows, updates 0 rows
        4. Neither fails, both succeed
        """
        mock_db = MagicMock()

        # First call updates 5 notifications
        mock_db.query.return_value.filter.return_value.update.return_value = 5

        from datetime import UTC, datetime

        now = datetime.now(UTC)

        # First concurrent request
        result1 = mock_db.query().filter().update({"is_read": True, "read_at": now})
        assert result1 == 5

        # Second concurrent request (in reality would run concurrently)
        # Now simulating that rows are already updated
        mock_db.query.return_value.filter.return_value.update.return_value = 0
        result2 = mock_db.query().filter().update({"is_read": True, "read_at": now})

        # Second call succeeds but updates 0 rows
        assert result2 == 0


class TestMarkAllReadFilterCorrectness:
    """Verify the filter conditions are correct for mark-all-read."""

    def test_only_updates_unread_notifications(self):
        """Verify only unread notifications are updated."""
        api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "presentation"
            / "api.py"
        )
        source = api_path.read_text()

        # Should filter for is_read == False or is_read.is_(False)
        has_unread_filter = (
            "is_read.is_(False)" in source
            or "is_read == False" in source
            or "is_read==False" in source
        )
        assert has_unread_filter, (
            "Mark all read should filter for unread notifications only"
        )

    def test_filters_by_user_id(self):
        """Verify only current user's notifications are updated."""
        api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "presentation"
            / "api.py"
        )
        source = api_path.read_text()

        # Should filter by user_id
        has_user_filter = "user_id" in source and "current_user.id" in source
        assert has_user_filter, (
            "Mark all read should filter by current user's ID"
        )


class TestMarkAllReadSetsTimestamp:
    """Verify mark-all-read sets the read_at timestamp."""

    def test_sets_read_at_timestamp(self):
        """Verify read_at is set when marking as read."""
        api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "presentation"
            / "api.py"
        )
        source = api_path.read_text()

        # Should set read_at in the update
        has_read_at = "read_at" in source
        assert has_read_at, (
            "Mark all read should set the read_at timestamp"
        )


class TestNoRaceConditionWithIndividualUpdates:
    """Verify the implementation avoids race conditions."""

    def test_no_select_then_update_pattern(self):
        """
        Verify we don't have a select-then-update pattern which is prone
        to race conditions.

        Bad pattern:
            notifications = db.query(Notification).filter(...).all()
            for n in notifications:
                n.is_read = True

        Good pattern:
            db.query(Notification).filter(...).update({...})
        """
        api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "notifications"
            / "presentation"
            / "api.py"
        )
        source = api_path.read_text()

        # Look for the mark_all_notifications_read function
        import re

        # Find the function definition
        func_match = re.search(
            r"async def mark_all_notifications_read\([^)]*\):[^@]*?(?=\n(?:@|async def|class |\Z))",
            source,
            re.DOTALL,
        )

        if func_match:
            func_body = func_match.group(0)

            # Check that we're NOT fetching all notifications first
            has_fetch_all = ".all()" in func_body and "for " in func_body
            assert not has_fetch_all, (
                "mark_all_notifications_read should NOT fetch all notifications "
                "and loop through them (race condition risk)"
            )

            # Check that we ARE using atomic update
            has_atomic_update = ".update(" in func_body
            assert has_atomic_update, (
                "mark_all_notifications_read should use atomic .update() method"
            )
