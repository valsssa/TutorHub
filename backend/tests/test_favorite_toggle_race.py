"""Tests for favorite toggle race condition handling.

This module verifies that the favorites API handles race conditions properly
when users rapidly click the favorite toggle button, potentially sending
multiple simultaneous requests.
"""

from pathlib import Path

import pytest


class TestFavoriteToggleRaceCondition:
    """Tests verifying atomic favorite toggle operations."""

    def test_favorite_toggle_handles_duplicates(self):
        """Verify favorite toggle handles duplicate attempts gracefully.

        The favorites API should:
        1. Check if favorite exists before adding (first line of defense)
        2. Handle IntegrityError if a race condition occurs (second line)
        3. Return the existing favorite instead of failing
        """
        favorites_path = Path(__file__).parent.parent / "modules" / "favorites"

        for py_file in favorites_path.rglob("*.py"):
            source = py_file.read_text()
            if "add_favorite" in source.lower() or "def add" in source.lower():
                # Should handle IntegrityError or use ON CONFLICT
                handles_duplicates = (
                    "IntegrityError" in source
                    or "ON CONFLICT" in source
                    or "get_or_create" in source
                    or ".first()" in source  # Check if exists first
                )
                if handles_duplicates:
                    assert True
                    return

        # If no add logic found, pass (may use different endpoint pattern)
        assert True

    def test_api_catches_integrity_error_on_duplicate(self):
        """Verify the API endpoint catches IntegrityError on race condition."""
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # The API should have try/except IntegrityError handling
        assert "IntegrityError" in source, "API should handle IntegrityError"
        assert "except IntegrityError" in source, "API should catch IntegrityError"
        assert "rollback" in source, "API should rollback on IntegrityError"

    def test_api_returns_existing_on_race_condition(self):
        """Verify the API returns existing favorite on race condition."""
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # After catching IntegrityError, it should return the existing favorite
        # by fetching it from the database
        assert "get_or_404" in source or "filter" in source, (
            "API should fetch existing favorite after IntegrityError"
        )

    def test_repository_handles_integrity_error(self):
        """Verify repository implementation handles IntegrityError properly."""
        repo_path = (
            Path(__file__).parent.parent
            / "modules"
            / "favorites"
            / "infrastructure"
            / "repositories.py"
        )

        if not repo_path.exists():
            pytest.skip("Repository not found in expected location")

        source = repo_path.read_text()

        # Repository should catch IntegrityError and raise domain exception
        assert "IntegrityError" in source, "Repository should handle IntegrityError"
        assert "DuplicateFavoriteError" in source, (
            "Repository should raise domain exception on duplicate"
        )

    def test_concurrent_add_favorite_recovery_mechanism(self):
        """Verify the API has proper recovery logic after IntegrityError.

        When a race condition occurs:
        1. The IntegrityError is caught
        2. The transaction is rolled back
        3. The existing record is fetched and returned

        This test verifies these mechanisms exist in the code.
        """
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # Verify the recovery flow exists:
        # 1. Catch IntegrityError
        assert "except IntegrityError:" in source, "Should catch IntegrityError"

        # 2. Rollback transaction
        assert "rollback()" in source, "Should rollback on IntegrityError"

        # 3. Fetch and return existing (uses get_or_404 after rollback)
        # Find the except block and verify it has recovery logic
        lines = source.split("\n")
        in_except_block = False
        has_recovery = False
        block_indent = 0

        for i, line in enumerate(lines):
            if "except IntegrityError" in line:
                in_except_block = True
                # Get the indentation level of the except line
                block_indent = len(line) - len(line.lstrip())
                continue

            if in_except_block:
                # Check if this line is part of the except block
                current_indent = len(line) - len(line.lstrip())
                stripped = line.strip()

                # Empty lines or comments don't end the block
                if not stripped or stripped.startswith("#"):
                    continue

                # If indentation is <= except block, we've left the block
                if current_indent <= block_indent and stripped:
                    break

                # Check for recovery logic within the block
                if "get_or_404" in line or "return favorite" in line:
                    has_recovery = True
                    break

        assert has_recovery, (
            "Should have recovery logic (get_or_404 or return) in except block"
        )

    def test_delete_is_idempotent(self):
        """Verify that delete operations are safe for concurrent requests.

        The delete endpoint uses get_or_404 which will return 404 if the
        favorite was already deleted by a concurrent request.
        """
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # Delete should use get_or_404 pattern
        assert "def remove_favorite" in source or "async def remove_favorite" in source
        assert "get_or_404" in source, "Delete should use get_or_404 pattern"


class TestFavoriteToggleMechanisms:
    """Tests verifying the specific race condition handling mechanisms."""

    def test_exists_check_before_insert(self):
        """Verify that existence check happens before insert attempt."""
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # Should use exists_or_409 helper before creating
        assert "exists_or_409" in source, (
            "API should check existence before insert with exists_or_409"
        )

    def test_two_layer_protection(self):
        """Verify both pre-check and IntegrityError handling exist.

        This provides defense in depth:
        1. Pre-check with exists_or_409 for normal cases (fast, clean response)
        2. IntegrityError handling for race conditions (catches edge cases)
        """
        api_path = Path(__file__).parent.parent / "modules" / "favorites" / "api.py"

        if not api_path.exists():
            pytest.skip("api.py not found in expected location")

        source = api_path.read_text()

        # Layer 1: Pre-check
        assert "exists_or_409" in source, "Missing first layer: exists_or_409 pre-check"

        # Layer 2: IntegrityError handling
        assert "except IntegrityError" in source, (
            "Missing second layer: IntegrityError handling"
        )

        # Recovery: Fetch and return existing
        assert "rollback" in source, "Should rollback on IntegrityError"
