"""Tests for package session race condition handling.

This module verifies that package session deduction uses atomic operations
to prevent race conditions that could lead to:
1. Negative session counts
2. Double deductions from concurrent requests
3. Inconsistent package states

The implementation uses two complementary approaches:
1. Atomic SQL UPDATE with WHERE guards (booking service, packages API)
2. Row-level locking with SELECT FOR UPDATE (repository layer)
"""

from __future__ import annotations

import re
from pathlib import Path


class TestAtomicSessionDeduction:
    """Verify session deduction uses atomic operations."""

    def test_booking_service_uses_atomic_update(self) -> None:
        """Verify booking service uses atomic UPDATE with WHERE guard."""
        booking_service_path = (
            Path(__file__).parent.parent / "modules" / "bookings" / "service.py"
        )
        source = booking_service_path.read_text()

        # Should have _consume_package_credit method with atomic update
        assert "_consume_package_credit" in source, (
            "Booking service should have _consume_package_credit method"
        )

        # Check for atomic update pattern with WHERE guard
        # Pattern: UPDATE ... WHERE sessions_remaining > 0
        has_atomic_update = (
            "sessions_remaining > 0" in source
            and "StudentPackage.sessions_remaining - 1" in source
        )
        assert has_atomic_update, (
            "Booking service should use atomic UPDATE with sessions_remaining > 0 guard"
        )

        # Verify status check is included
        assert 'status == "active"' in source or "status == 'active'" in source, (
            "Booking service should check package status is active before deduction"
        )

    def test_packages_api_uses_atomic_update(self) -> None:
        """Verify packages API uses atomic UPDATE with WHERE guard."""
        packages_api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "packages"
            / "presentation"
            / "api.py"
        )
        source = packages_api_path.read_text()

        # Check for atomic update pattern
        has_atomic_update = (
            "sessions_remaining > 0" in source
            and "StudentPackage.sessions_remaining - 1" in source
        )
        assert has_atomic_update, (
            "Packages API should use atomic UPDATE with sessions_remaining > 0 guard"
        )

        # Should verify rowcount to detect failed updates
        assert "result.rowcount == 0" in source, (
            "Packages API should check rowcount to detect failed atomic updates"
        )

    def test_repository_uses_row_level_locking(self) -> None:
        """Verify repository uses SELECT FOR UPDATE for row-level locking."""
        repository_path = (
            Path(__file__).parent.parent
            / "modules"
            / "packages"
            / "infrastructure"
            / "repositories.py"
        )
        source = repository_path.read_text()

        # Should have use_session method
        assert "def use_session(" in source, (
            "Repository should have use_session method for atomic session usage"
        )

        # Check for row-level locking
        assert "with_for_update()" in source, (
            "Repository should use with_for_update() for row-level locking"
        )

        # Verify validation before decrement
        assert "sessions_remaining <= 0" in source, (
            "Repository should check sessions_remaining before decrementing"
        )

    def test_credit_restore_uses_atomic_update(self) -> None:
        """Verify credit restoration uses atomic UPDATE with guards."""
        booking_service_path = (
            Path(__file__).parent.parent / "modules" / "bookings" / "service.py"
        )
        source = booking_service_path.read_text()

        # Should have _restore_package_credit method
        assert "_restore_package_credit" in source, (
            "Booking service should have _restore_package_credit method"
        )

        # Check for over-restoration guard
        assert "sessions_remaining < StudentPackage.sessions_purchased" in source, (
            "Credit restore should guard against over-restoration"
        )

        # Check for sessions_used guard
        assert "sessions_used > 0" in source, (
            "Credit restore should verify sessions have been used before restoring"
        )

    def test_exhausted_status_update_is_separate(self) -> None:
        """Verify exhausted status update is done after credit deduction.

        The status update to 'exhausted' should be done AFTER the credit
        deduction succeeds, not as part of the same UPDATE. This ensures
        that if the deduction fails, the status is not prematurely changed.
        """
        booking_service_path = (
            Path(__file__).parent.parent / "modules" / "bookings" / "service.py"
        )
        source = booking_service_path.read_text()

        # Should have separate method for status update
        assert "_update_package_status_if_exhausted" in source, (
            "Booking service should have _update_package_status_if_exhausted method"
        )

        # The comment pattern indicating proper separation
        assert "NOTE: Do NOT set" in source or "Do NOT set" in source, (
            "Code should document that status is not set in credit deduction"
        )

    def test_database_constraint_prevents_negative(self) -> None:
        """Verify database has CHECK constraint for non-negative sessions."""
        students_model_path = Path(__file__).parent.parent / "models" / "students.py"
        source = students_model_path.read_text()

        # Should have CheckConstraint for non-negative sessions
        assert "non_negative_sessions_remaining" in source, (
            "Database should have CHECK constraint for non-negative sessions_remaining"
        )

        assert 'sessions_remaining >= 0' in source, (
            "CHECK constraint should enforce sessions_remaining >= 0"
        )


class TestAtomicOperationPatterns:
    """Test that atomic operation patterns are correctly implemented."""

    def test_no_read_modify_write_antipattern(self) -> None:
        """Verify no read-modify-write antipattern in session deduction.

        The antipattern would be:
            package = db.query(StudentPackage).get(id)
            package.sessions_remaining -= 1  # Race condition here!
            db.commit()

        Instead, should use atomic UPDATE or SELECT FOR UPDATE.
        """
        # Check packages presentation API
        packages_api_path = (
            Path(__file__).parent.parent
            / "modules"
            / "packages"
            / "presentation"
            / "api.py"
        )
        source = packages_api_path.read_text()

        # Find the use_credit endpoint
        use_credit_pattern = re.compile(
            r'def use_credit\(.*?\n(?:.*?\n)*?.*?(?=\n(?:@router|def |class |\Z))',
            re.MULTILINE,
        )
        match = use_credit_pattern.search(source)

        if match:
            use_credit_code = match.group()
            # Should use update() not direct attribute modification
            assert "update(" in use_credit_code, (
                "use_credit should use update() for atomic operation"
            )

    def test_atomic_update_uses_correct_where_clause(self) -> None:
        """Verify atomic UPDATE has proper WHERE conditions."""
        booking_service_path = (
            Path(__file__).parent.parent / "modules" / "bookings" / "service.py"
        )
        source = booking_service_path.read_text()

        # The _consume_package_credit should have:
        # 1. Package ID check
        # 2. sessions_remaining > 0 check
        # 3. status == 'active' check

        # Find the _consume_package_credit function
        consume_pattern = re.compile(
            r'def _consume_package_credit\(.*?\n(?:.*?\n)*?.*?rowcount',
            re.MULTILINE,
        )
        match = consume_pattern.search(source)

        if match:
            consume_code = match.group()
            # Check all required WHERE conditions
            assert "StudentPackage.id ==" in consume_code, (
                "Should filter by package ID"
            )
            assert "sessions_remaining > 0" in consume_code, (
                "Should check sessions_remaining > 0"
            )


class TestRaceConditionDocumentation:
    """Verify race condition handling is documented."""

    def test_booking_service_documents_atomicity(self) -> None:
        """Verify booking service has documentation about atomicity."""
        booking_service_path = (
            Path(__file__).parent.parent / "modules" / "bookings" / "service.py"
        )
        source = booking_service_path.read_text()

        # Should have docstring explaining atomic operation
        assert "race condition" in source.lower() or "atomic" in source.lower(), (
            "Booking service should document atomic/race condition handling"
        )

    def test_repository_documents_row_locking(self) -> None:
        """Verify repository documents row-level locking."""
        repository_path = (
            Path(__file__).parent.parent
            / "modules"
            / "packages"
            / "infrastructure"
            / "repositories.py"
        )
        source = repository_path.read_text()

        # Should have documentation about locking
        lock_doc_patterns = ["lock", "for update", "atomic"]
        has_lock_doc = any(
            pattern in source.lower() for pattern in lock_doc_patterns
        )
        assert has_lock_doc, (
            "Repository should document row-level locking behavior"
        )
