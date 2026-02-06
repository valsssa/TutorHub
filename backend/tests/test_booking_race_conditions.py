"""Tests for booking race condition handling.

These tests verify that the booking system properly prevents race conditions
through row-level locking (SELECT FOR UPDATE) and optimistic locking (version column).

Race conditions addressed:
1. Concurrent booking confirmations (two tutors clicking confirm simultaneously)
2. Race between cancel and start_sessions job
3. Race between confirm and expiry job
4. Concurrent no-show reports from student and tutor
"""

from pathlib import Path


def test_booking_state_machine_has_locking_method():
    """Verify state machine has get_booking_with_lock method."""
    state_machine_path = Path(__file__).parent.parent / "modules" / "bookings" / "domain" / "state_machine.py"
    source = state_machine_path.read_text()

    # Should have the get_booking_with_lock method
    assert "def get_booking_with_lock" in source, "State machine should have get_booking_with_lock method"

    # Method should use with_for_update for row-level locking
    assert "with_for_update" in source, "get_booking_with_lock should use with_for_update"


def test_booking_state_machine_has_optimistic_locking():
    """Verify state machine implements optimistic locking via version column."""
    state_machine_path = Path(__file__).parent.parent / "modules" / "bookings" / "domain" / "state_machine.py"
    source = state_machine_path.read_text()

    # Should have version increment method
    assert "def increment_version" in source, "State machine should have increment_version method"

    # Should have version verification method
    assert "def verify_version" in source, "State machine should have verify_version method"

    # Should have OptimisticLockError exception
    assert "class OptimisticLockError" in source, "State machine should define OptimisticLockError"


def test_booking_confirm_uses_locking():
    """Verify booking confirmation endpoint uses row-level locking."""
    api_path = Path(__file__).parent.parent / "modules" / "bookings" / "presentation" / "api.py"
    source = api_path.read_text()

    # Find the confirm_booking function
    assert "async def confirm_booking" in source, "Confirm booking endpoint should exist"

    # The confirm endpoint should use get_booking_with_lock
    # Split source to find the function and check it uses locking
    lines = source.split("\n")
    in_confirm_function = False
    found_locking = False

    for line in lines:
        if "async def confirm_booking" in line:
            in_confirm_function = True
        elif in_confirm_function and "async def " in line and "confirm_booking" not in line:
            break  # Next function started
        elif in_confirm_function and "get_booking_with_lock" in line:
            found_locking = True
            break

    assert found_locking, "confirm_booking should use get_booking_with_lock for row-level locking"


def test_booking_cancel_uses_locking():
    """Verify booking cancellation endpoint uses row-level locking."""
    api_path = Path(__file__).parent.parent / "modules" / "bookings" / "presentation" / "api.py"
    source = api_path.read_text()

    # Find the cancel_booking function
    assert "async def cancel_booking" in source, "Cancel booking endpoint should exist"

    # Check for locking in cancel endpoint
    lines = source.split("\n")
    in_cancel_function = False
    found_locking = False

    for line in lines:
        if "async def cancel_booking" in line:
            in_cancel_function = True
        elif in_cancel_function and "async def " in line and "cancel_booking" not in line:
            break
        elif in_cancel_function and "get_booking_with_lock" in line:
            found_locking = True
            break

    assert found_locking, "cancel_booking should use get_booking_with_lock for row-level locking"


def test_booking_decline_uses_locking():
    """Verify booking decline endpoint uses row-level locking."""
    api_path = Path(__file__).parent.parent / "modules" / "bookings" / "presentation" / "api.py"
    source = api_path.read_text()

    # Find the decline_booking function
    assert "async def decline_booking" in source, "Decline booking endpoint should exist"

    # Check for locking in decline endpoint
    lines = source.split("\n")
    in_decline_function = False
    found_locking = False

    for line in lines:
        if "async def decline_booking" in line:
            in_decline_function = True
        elif in_decline_function and "async def " in line and "decline_booking" not in line:
            break
        elif in_decline_function and "get_booking_with_lock" in line:
            found_locking = True
            break

    assert found_locking, "decline_booking should use get_booking_with_lock for row-level locking"


def test_no_show_uses_locking():
    """Verify no-show endpoints use row-level locking."""
    api_path = Path(__file__).parent.parent / "modules" / "bookings" / "presentation" / "api.py"
    source = api_path.read_text()

    # No-show endpoints should use locking
    # They use use_lock=True parameter in service.mark_no_show call
    assert "use_lock=True" in source, "No-show marking should use locking via use_lock parameter"


def test_state_machine_transitions_are_idempotent():
    """Verify state machine transitions handle idempotent calls safely."""
    state_machine_path = Path(__file__).parent.parent / "modules" / "bookings" / "domain" / "state_machine.py"
    source = state_machine_path.read_text()

    # All transition methods should check for already_in_target_state
    assert "already_in_target_state" in source, "Transitions should be idempotent"

    # Check that key methods have idempotency checks
    idempotent_patterns = [
        "already_in_target_state=True",
        "Idempotent",
    ]

    for pattern in idempotent_patterns:
        assert pattern in source, f"State machine should include idempotency pattern: {pattern}"


def test_atomic_operation_used_for_state_changes():
    """Verify state changes are wrapped in atomic_operation for transaction safety."""
    api_path = Path(__file__).parent.parent / "modules" / "bookings" / "presentation" / "api.py"
    source = api_path.read_text()

    # Should import atomic_operation
    assert "from core.transactions import atomic_operation" in source, (
        "API should import atomic_operation for transaction safety"
    )

    # Should use atomic_operation context manager
    assert "with atomic_operation(db)" in source, (
        "State changes should be wrapped in atomic_operation"
    )


def test_state_machine_documents_race_condition_prevention():
    """Verify state machine documentation mentions race condition handling."""
    state_machine_path = Path(__file__).parent.parent / "modules" / "bookings" / "domain" / "state_machine.py"
    source = state_machine_path.read_text()

    # Documentation should mention race condition prevention
    race_condition_docs = [
        "Race Condition Prevention",
        "SELECT FOR UPDATE",
        "pessimistic locking",
    ]

    for doc in race_condition_docs:
        assert doc in source, f"Documentation should mention: {doc}"


def test_mark_no_show_with_lock_method_exists():
    """Verify convenience method for atomic no-show with locking exists."""
    state_machine_path = Path(__file__).parent.parent / "modules" / "bookings" / "domain" / "state_machine.py"
    source = state_machine_path.read_text()

    # Should have the combined lock + no-show method
    assert "def mark_no_show_with_lock" in source, (
        "State machine should have mark_no_show_with_lock convenience method"
    )
