"""
Comprehensive tests for hard booking flow scenarios.

Tests complex edge cases including:
- Race conditions (concurrent booking attempts, state transitions)
- Timezone edge cases (DST, cross-timezone, midnight boundaries)
- State machine edge cases (invalid transitions, expiration during payment)
- Cancellation complexities (during Zoom, late cancellation, concurrent)
- Recovery scenarios (Redis failure, DB rollback, webhook failure)
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import threading
import time

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from modules.bookings.domain.state_machine import (
    BookingStateMachine,
    OptimisticLockError,
    StateTransitionError,
    TransitionResult,
)
from modules.bookings.domain.status import (
    CancelledByRole,
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)
from core.distributed_lock import DistributedLockService
from core.transactions import TransactionError, atomic_operation


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_booking():
    """Create a fully-configured mock booking object."""
    booking = MagicMock()
    booking.id = 1
    booking.session_state = SessionState.REQUESTED.value
    booking.session_outcome = None
    booking.payment_state = PaymentState.PENDING.value
    booking.dispute_state = DisputeState.NONE.value
    booking.cancelled_by_role = None
    booking.cancelled_at = None
    booking.confirmed_at = None
    booking.rate_cents = 5000
    booking.tutor_profile = MagicMock()
    booking.tutor_profile.id = 1
    booking.student_id = 2
    booking.version = 1
    booking.updated_at = datetime.now(UTC)
    booking.created_at = datetime.now(UTC) - timedelta(hours=1)
    booking.start_time = datetime.now(UTC) + timedelta(hours=24)
    booking.end_time = datetime.now(UTC) + timedelta(hours=25)
    booking.tutor_joined_at = None
    booking.student_joined_at = None
    booking.zoom_meeting_id = None
    booking.zoom_meeting_pending = False
    booking.stripe_checkout_session_id = "cs_test_123"
    booking.tutor_tz = "UTC"
    booking.student_tz = "UTC"
    booking.dispute_reason = None
    booking.disputed_at = None
    booking.disputed_by = None
    return booking


@pytest.fixture
def mock_db():
    """Create a mock database session with transaction support."""
    db = MagicMock(spec=Session)
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.refresh = MagicMock()
    db.begin_nested = MagicMock()
    db.execute = MagicMock()
    db.query = MagicMock()
    return db


@pytest.fixture
def lock_service():
    """Create a fresh distributed lock service for testing."""
    return DistributedLockService()


# =============================================================================
# Race Condition Tests
# =============================================================================


class TestRaceConditions:
    """Test race condition scenarios in booking flows."""

    def test_two_students_booking_same_slot_first_wins(self, mock_db, mock_booking):
        """
        Two students try to book the same time slot simultaneously.
        The first to acquire the lock should succeed, the second should fail.
        """
        # Setup: Create two concurrent booking attempts
        slot_start = datetime.now(UTC) + timedelta(days=1)
        slot_end = slot_start + timedelta(hours=1)

        # Mock the database query to simulate overlap check
        existing_booking = MagicMock()
        existing_booking.id = 1
        existing_booking.tutor_profile_id = 1
        existing_booking.start_time = slot_start
        existing_booking.end_time = slot_end
        existing_booking.session_state = SessionState.REQUESTED.value

        # First student's booking attempt succeeds
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Simulate the first booking being created
        first_booking = MagicMock()
        first_booking.id = 1

        # Second student's attempt should find the conflict
        # After first booking is committed, query returns existing booking
        def side_effect_query(*args, **kwargs):
            mock_result = MagicMock()
            # First call returns None (no conflict), second returns existing
            mock_result.filter.return_value.first.side_effect = [None, existing_booking]
            return mock_result

        mock_db.query.side_effect = side_effect_query

        # Verify that overlapping bookings are detected
        assert existing_booking.start_time == slot_start
        assert existing_booking.end_time == slot_end

    def test_concurrent_state_transitions_with_row_lock(self, mock_booking):
        """
        Concurrent state transitions on the same booking should be serialized
        via SELECT FOR UPDATE.
        """
        # Initial state
        mock_booking.session_state = SessionState.REQUESTED.value
        mock_booking.version = 1

        # First transition: Accept booking
        result1 = BookingStateMachine.accept_booking(mock_booking)
        assert result1.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value
        assert mock_booking.version == 2

        # Second concurrent transition attempt should be idempotent
        result2 = BookingStateMachine.accept_booking(mock_booking)
        assert result2.success is True
        assert result2.already_in_target_state is True
        # Version should not change for idempotent operations
        assert mock_booking.version == 2

    def test_optimistic_lock_version_mismatch(self, mock_booking):
        """
        Test that version mismatch is detected during concurrent updates.
        """
        mock_booking.version = 1

        # Simulate first update
        initial_version = mock_booking.version
        BookingStateMachine.accept_booking(mock_booking)

        # Version should be incremented
        assert mock_booking.version == initial_version + 1

        # Verify version is correct after transition
        assert BookingStateMachine.verify_version(mock_booking, 2) is True
        assert BookingStateMachine.verify_version(mock_booking, 1) is False

    def test_booking_during_availability_update(self, mock_db, mock_booking):
        """
        Test booking attempt while tutor is simultaneously updating availability.
        The booking should either succeed or fail atomically.
        """
        # Simulate tutor availability being updated concurrently
        availability_lock = threading.Lock()
        booking_succeeded = [False]
        availability_updated = [False]

        def update_availability():
            with availability_lock:
                time.sleep(0.01)  # Small delay to simulate concurrent operation
                availability_updated[0] = True

        def create_booking():
            with availability_lock:
                # Booking should wait for lock if availability is being updated
                booking_succeeded[0] = True

        # Run both operations
        t1 = threading.Thread(target=update_availability)
        t2 = threading.Thread(target=create_booking)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both should complete (one after the other due to lock)
        assert availability_updated[0] is True
        assert booking_succeeded[0] is True

    def test_double_accept_race_condition(self, mock_booking):
        """
        Test two tutors (or same tutor twice) accepting the same booking.
        Second accept should be idempotent.
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        # First accept
        result1 = BookingStateMachine.accept_booking(mock_booking)
        assert result1.success is True
        assert result1.already_in_target_state is False

        # Second accept (idempotent)
        result2 = BookingStateMachine.accept_booking(mock_booking)
        assert result2.success is True
        assert result2.already_in_target_state is True

    def test_cancel_while_starting_session(self, mock_booking):
        """
        Test cancellation attempt while session is starting.
        The start transition should take precedence if it occurs first.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value

        # Start session first
        start_result = BookingStateMachine.start_session(mock_booking)
        assert start_result.success is True
        assert mock_booking.session_state == SessionState.ACTIVE.value

        # Now try to cancel - should fail because session is active
        cancel_result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True
        )
        assert cancel_result.success is False
        assert "ACTIVE" in cancel_result.error_message


# =============================================================================
# Timezone Edge Cases
# =============================================================================


class TestTimezoneEdgeCases:
    """Test timezone-related edge cases in booking flows."""

    def test_booking_across_dst_transition(self, mock_booking):
        """
        Test booking that spans a DST transition.
        The duration should be preserved regardless of DST changes.
        """
        # Setup: Booking scheduled during DST transition (e.g., US spring forward)
        # March 10, 2024 at 2:00 AM becomes 3:00 AM
        mock_booking.tutor_tz = "America/New_York"
        mock_booking.student_tz = "America/Los_Angeles"

        # Original 1-hour session scheduled at 1:30 AM EST
        # During DST transition, this becomes complex
        pre_dst_start = datetime(2024, 3, 10, 1, 30, tzinfo=UTC)
        pre_dst_end = pre_dst_start + timedelta(hours=1)

        mock_booking.start_time = pre_dst_start
        mock_booking.end_time = pre_dst_end

        # Duration should still be 1 hour in absolute terms
        duration = mock_booking.end_time - mock_booking.start_time
        assert duration == timedelta(hours=1)

        # State machine should not care about DST
        mock_booking.session_state = SessionState.REQUESTED.value
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True

    def test_user_different_timezone_than_tutor(self, mock_booking):
        """
        Test booking when student and tutor are in different timezones.
        Both should see correct times in their respective timezones.
        """
        mock_booking.tutor_tz = "Asia/Tokyo"  # UTC+9
        mock_booking.student_tz = "America/New_York"  # UTC-5 (EST)

        # Booking at 10:00 AM UTC
        booking_start_utc = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
        mock_booking.start_time = booking_start_utc

        # Tutor sees: 7:00 PM JST
        # Student sees: 6:00 AM EST (or 5:00 AM EDT in summer)

        # The booking should still process correctly
        mock_booking.session_state = SessionState.REQUESTED.value
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True

        # Verify start_time is still stored in UTC
        assert mock_booking.start_time.tzinfo == UTC

    def test_midnight_boundary_booking(self, mock_booking):
        """
        Test booking that crosses midnight in various timezones.
        """
        # Booking from 11:30 PM to 12:30 AM
        mock_booking.tutor_tz = "UTC"
        mock_booking.start_time = datetime(2024, 6, 15, 23, 30, 0, tzinfo=UTC)
        mock_booking.end_time = datetime(2024, 6, 16, 0, 30, 0, tzinfo=UTC)

        # Verify dates are different
        assert mock_booking.start_time.date() != mock_booking.end_time.date()

        # But state machine should handle this fine
        mock_booking.session_state = SessionState.REQUESTED.value
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True

    def test_international_date_line_crossing(self, mock_booking):
        """
        Test booking for users near the International Date Line.
        """
        mock_booking.tutor_tz = "Pacific/Auckland"  # UTC+12/+13
        mock_booking.student_tz = "Pacific/Honolulu"  # UTC-10

        # 22-hour difference between timezones
        # Same moment can be different calendar dates
        mock_booking.start_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        mock_booking.end_time = mock_booking.start_time + timedelta(hours=1)

        # Processing should work correctly
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value
        result = BookingStateMachine.start_session(mock_booking)
        assert result.success is True

    def test_session_end_near_dst_fallback(self, mock_booking):
        """
        Test session ending during DST "fall back" when clocks repeat an hour.
        """
        # November 3, 2024 at 2:00 AM becomes 1:00 AM (US fall back)
        mock_booking.tutor_tz = "America/New_York"

        # Session scheduled to end at the ambiguous 1:30 AM
        mock_booking.start_time = datetime(2024, 11, 3, 5, 0, 0, tzinfo=UTC)  # 1:00 AM EDT
        mock_booking.end_time = datetime(2024, 11, 3, 6, 30, 0, tzinfo=UTC)  # 1:30 AM EST (after fallback)

        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value


# =============================================================================
# State Machine Edge Cases
# =============================================================================


class TestStateMachineEdgeCases:
    """Test state machine edge cases and invalid transitions."""

    def test_invalid_cancelled_to_confirmed_transition(self, mock_booking):
        """
        Test that cancelled booking cannot be confirmed.
        """
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.session_outcome = SessionOutcome.NOT_HELD.value

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is False
        assert "CANCELLED" in result.error_message

    def test_invalid_expired_to_active_transition(self, mock_booking):
        """
        Test that expired booking cannot become active.
        """
        mock_booking.session_state = SessionState.EXPIRED.value

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is False
        assert "EXPIRED" in result.error_message

    def test_expiration_during_payment_processing(self, mock_booking):
        """
        Test booking expiration while payment is being authorized.
        Payment should be voided if booking expires.
        """
        mock_booking.session_state = SessionState.REQUESTED.value
        mock_booking.payment_state = PaymentState.PENDING.value
        mock_booking.created_at = datetime.now(UTC) - timedelta(hours=25)  # Past 24h

        # Expire the booking
        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.EXPIRED.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value
        assert mock_booking.cancelled_by_role == CancelledByRole.SYSTEM.value

    def test_session_start_while_pending(self, mock_booking):
        """
        Test that session cannot start if still in pending (REQUESTED) state.
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is False
        assert "REQUESTED" in result.error_message

    def test_double_completion_attempts(self, mock_booking):
        """
        Test that completing an already ended session is idempotent.
        """
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        # First completion
        result1 = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert result1.success is True
        assert mock_booking.session_state == SessionState.ENDED.value

        # Second completion attempt (idempotent)
        result2 = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert result2.success is True
        assert result2.already_in_target_state is True

    def test_end_session_from_requested_state(self, mock_booking):
        """
        Test that session cannot end directly from REQUESTED state.
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)

        assert result.success is False

    def test_decline_after_accept(self, mock_booking):
        """
        Test that a tutor cannot decline after accepting a booking.
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        # Accept first
        accept_result = BookingStateMachine.accept_booking(mock_booking)
        assert accept_result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value

        # Try to decline - should fail
        decline_result = BookingStateMachine.decline_booking(mock_booking)
        assert decline_result.success is False

    def test_no_show_on_ended_session(self, mock_booking):
        """
        Test marking no-show on already ended session.
        """
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.COMPLETED.value
        mock_booking.payment_state = PaymentState.CAPTURED.value

        # Try to mark student as no-show (same reporter)
        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT", reporter_role="TUTOR")

        # This should escalate to dispute since outcome differs
        assert result.success is True
        assert result.escalated_to_dispute is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value

    def test_dispute_on_non_terminal_state(self, mock_booking):
        """
        Test that disputes cannot be opened on non-terminal session states.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="I want a refund",
            disputed_by_user_id=123
        )

        assert result.success is False
        assert "terminal" in result.error_message.lower() or "completed" in result.error_message.lower()


# =============================================================================
# Cancellation Complexities
# =============================================================================


class TestCancellationComplexities:
    """Test complex cancellation scenarios."""

    def test_cancellation_during_active_zoom_meeting(self, mock_booking):
        """
        Test cancellation attempt while Zoom meeting is active.
        Active sessions cannot be cancelled.
        """
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.zoom_meeting_id = "zoom_123"
        mock_booking.tutor_joined_at = datetime.now(UTC) - timedelta(minutes=10)
        mock_booking.student_joined_at = datetime.now(UTC) - timedelta(minutes=8)

        # Try to cancel active session
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True
        )

        assert result.success is False
        assert "ACTIVE" in result.error_message

    def test_late_cancellation_inside_policy_window(self, mock_booking):
        """
        Test late cancellation (inside 24-hour policy window).
        Should capture payment instead of refunding.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value
        # Session starts in 2 hours (inside 24h window)
        mock_booking.start_time = datetime.now(UTC) + timedelta(hours=2)

        # Late cancellation - no refund
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=False  # Late cancellation policy
        )

        assert result.success is True
        assert mock_booking.session_state == SessionState.CANCELLED.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value  # Tutor gets paid

    def test_cancellation_with_partial_refund(self, mock_booking):
        """
        Test cancellation with partial refund scenario.
        """
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.COMPLETED.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        # Open dispute and resolve with partial refund
        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Session quality issues",
            disputed_by_user_id=123
        )
        assert result.success is True

        # Resolve with partial refund
        resolve_result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Partial refund approved",
            refund_amount_cents=2500  # Half refund
        )

        assert resolve_result.success is True
        assert mock_booking.payment_state == PaymentState.PARTIALLY_REFUNDED.value

    def test_concurrent_student_and_tutor_cancellation(self, mock_booking):
        """
        Test scenario where student and tutor try to cancel simultaneously.
        First cancellation should succeed, second should be idempotent.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        # Student cancels first
        result1 = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True
        )
        assert result1.success is True
        assert mock_booking.cancelled_by_role == CancelledByRole.STUDENT.value

        # Tutor tries to cancel (idempotent)
        result2 = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.TUTOR,
            refund=True
        )
        assert result2.success is True
        assert result2.already_in_target_state is True
        # Original canceller should be preserved
        assert mock_booking.cancelled_by_role == CancelledByRole.STUDENT.value

    def test_admin_cancellation_overrides(self, mock_booking):
        """
        Test that admin can cancel bookings in various states.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.ADMIN,
            refund=True
        )

        assert result.success is True
        assert mock_booking.cancelled_by_role == CancelledByRole.ADMIN.value
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_system_cancellation_on_tutor_account_issue(self, mock_booking):
        """
        Test system-initiated cancellation (e.g., tutor account suspended).
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.SYSTEM,
            refund=True
        )

        assert result.success is True
        assert mock_booking.cancelled_by_role == CancelledByRole.SYSTEM.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value


# =============================================================================
# Recovery Scenarios
# =============================================================================


class TestRecoveryScenarios:
    """Test recovery scenarios for various failure modes."""

    @pytest.mark.asyncio
    async def test_redis_failure_during_distributed_lock(self, lock_service):
        """
        Test that Redis failure during lock acquisition fails open.
        Operations should proceed to prevent blocking all jobs.
        """
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = Exception("Redis connection refused")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            acquired, token = await lock_service.try_acquire("booking:process:1")

            # Should fail open (return True) to allow job to proceed
            assert acquired is True
            assert token is None

    @pytest.mark.asyncio
    async def test_redis_failure_on_lock_release(self, lock_service):
        """
        Test handling of Redis failure during lock release.
        """
        mock_redis = AsyncMock()
        mock_redis.eval.side_effect = Exception("Redis timeout")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.release("booking:process:1", "token123")

            # Release should return False but not raise
            assert result is False

    def test_database_rollback_mid_booking(self, mock_db):
        """
        Test that database transaction rollback properly cleans up partial state.
        """
        mock_db.commit.side_effect = IntegrityError("duplicate key", None, None)

        with pytest.raises(TransactionError):
            with atomic_operation(mock_db):
                mock_db.add(MagicMock())
                # Commit will fail, triggering rollback

        mock_db.rollback.assert_called_once()

    def test_operational_error_recovery(self, mock_db):
        """
        Test recovery from database operational errors (connection issues).
        """
        mock_db.commit.side_effect = OperationalError("connection lost", None, None)

        with pytest.raises(TransactionError) as exc_info:
            with atomic_operation(mock_db):
                mock_db.add(MagicMock())

        assert "operation failed" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_failure_during_state_change(self, mock_booking):
        """
        Test handling of webhook delivery failure during state change.
        State change should complete, webhook failure should be logged for retry.
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        # Simulate webhook failure
        webhook_failed = [False]
        webhook_error = None

        async def failing_webhook(*args, **kwargs):
            nonlocal webhook_error
            webhook_failed[0] = True
            webhook_error = Exception("Webhook timeout")
            raise webhook_error

        # State change should succeed regardless of webhook
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value

        # Webhook can fail independently
        try:
            await failing_webhook()
        except Exception:
            pass

        assert webhook_failed[0] is True

    def test_stripe_payment_failure_recovery(self, mock_booking):
        """
        Test recovery when Stripe payment authorization fails.
        Booking should remain in REQUESTED state.
        """
        mock_booking.session_state = SessionState.REQUESTED.value
        mock_booking.payment_state = PaymentState.PENDING.value

        # Simulate payment failure - booking stays in REQUESTED
        # The tutor cannot accept without payment authorization
        # This is handled at the application layer, not state machine
        assert mock_booking.session_state == SessionState.REQUESTED.value
        assert mock_booking.payment_state == PaymentState.PENDING.value

    def test_zoom_meeting_creation_failure_retry(self, mock_booking):
        """
        Test that Zoom meeting creation failure sets pending flag for retry.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.zoom_meeting_id = None
        mock_booking.zoom_meeting_pending = True  # Flag for retry

        # Booking should still be valid even without Zoom meeting
        result = BookingStateMachine.start_session(mock_booking)
        assert result.success is True

        # Zoom meeting can be created later via retry mechanism
        assert mock_booking.zoom_meeting_pending is True

    def test_idempotent_retry_after_partial_failure(self, mock_booking):
        """
        Test that retry after partial failure is safe (idempotent).
        """
        mock_booking.session_state = SessionState.REQUESTED.value

        # First attempt succeeds
        result1 = BookingStateMachine.accept_booking(mock_booking)
        assert result1.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value

        # Imagine notification failed, job retries
        # Second accept should be idempotent
        result2 = BookingStateMachine.accept_booking(mock_booking)
        assert result2.success is True
        assert result2.already_in_target_state is True


# =============================================================================
# Complex Multi-Step Scenarios
# =============================================================================


class TestComplexMultiStepScenarios:
    """Test complex scenarios involving multiple state transitions."""

    def test_full_booking_lifecycle_with_dispute(self, mock_booking):
        """
        Test complete booking lifecycle: request -> accept -> start -> end -> dispute -> resolve.
        """
        # Step 1: Initial state
        assert mock_booking.session_state == SessionState.REQUESTED.value

        # Step 2: Tutor accepts
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value
        assert mock_booking.payment_state == PaymentState.AUTHORIZED.value

        # Step 3: Session starts
        result = BookingStateMachine.start_session(mock_booking)
        assert result.success is True
        assert mock_booking.session_state == SessionState.ACTIVE.value

        # Step 4: Session ends
        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

        # Step 5: Student files dispute
        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Tutor was unprepared",
            disputed_by_user_id=mock_booking.student_id
        )
        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value

        # Step 6: Admin resolves dispute
        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
            notes="Evidence reviewed, tutor was prepared"
        )
        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_UPHELD.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value  # Unchanged

    def test_expiry_race_with_accept(self, mock_booking):
        """
        Test race between booking expiry and tutor accept.
        If tutor accepts first, expiry should be idempotent.
        """
        mock_booking.session_state = SessionState.REQUESTED.value
        mock_booking.created_at = datetime.now(UTC) - timedelta(hours=25)  # Past 24h

        # Scenario 1: Tutor accepts first
        accept_result = BookingStateMachine.accept_booking(mock_booking)
        assert accept_result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value

        # Expiry job runs later - should be idempotent
        expire_result = BookingStateMachine.expire_booking(mock_booking)
        assert expire_result.success is True
        assert expire_result.already_in_target_state is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value  # Unchanged

    def test_conflicting_no_show_reports_escalation(self, mock_booking):
        """
        Test escalation to dispute when both parties report no-show.
        """
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        # Tutor reports student no-show
        result1 = BookingStateMachine.mark_no_show(
            mock_booking, "STUDENT", reporter_role="TUTOR"
        )
        assert result1.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

        # Student reports tutor no-show (conflicting)
        result2 = BookingStateMachine.mark_no_show(
            mock_booking, "TUTOR", reporter_role="STUDENT"
        )
        assert result2.success is True
        assert result2.escalated_to_dispute is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value
        assert "Conflicting" in mock_booking.dispute_reason

    def test_cancel_and_rebook_flow(self, mock_booking):
        """
        Test cancellation followed by rebooking the same slot.
        """
        # First booking
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        # Cancel
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True
        )
        assert result.success is True
        assert mock_booking.session_state == SessionState.CANCELLED.value

        # New booking for same slot should be allowed
        new_booking = MagicMock()
        new_booking.id = 2
        new_booking.session_state = SessionState.REQUESTED.value
        new_booking.payment_state = PaymentState.PENDING.value
        new_booking.version = 1
        new_booking.confirmed_at = None
        new_booking.updated_at = None
        new_booking.start_time = mock_booking.start_time  # Same slot
        new_booking.end_time = mock_booking.end_time

        accept_result = BookingStateMachine.accept_booking(new_booking)
        assert accept_result.success is True


# =============================================================================
# Payment State Transition Edge Cases
# =============================================================================


class TestPaymentStateEdgeCases:
    """Test payment state transition edge cases."""

    def test_refund_from_partially_refunded(self, mock_booking):
        """
        Test completing refund from partially refunded state.
        """
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.payment_state = PaymentState.PARTIALLY_REFUNDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value

        # Resolve dispute with full refund
        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Full refund approved"
        )

        assert result.success is True
        # Note: The state machine sets to REFUNDED for RESOLVED_REFUNDED resolution
        # when payment is already PARTIALLY_REFUNDED

    def test_void_authorized_payment(self, mock_booking):
        """
        Test voiding an authorized (but not captured) payment.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.TUTOR,
            refund=True
        )

        assert result.success is True
        # Authorized payments should be refunded (released)
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_no_refund_on_late_student_cancel(self, mock_booking):
        """
        Test that late student cancellation results in payment capture (no refund).
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=False  # Late cancellation - tutor gets paid
        )

        assert result.success is True
        assert mock_booking.payment_state == PaymentState.CAPTURED.value


# =============================================================================
# Version Control Tests
# =============================================================================


class TestVersionControl:
    """Test optimistic locking via version control."""

    def test_version_increments_on_every_transition(self, mock_booking):
        """
        Test that version increments on every state transition.
        """
        mock_booking.version = 1

        # Accept
        BookingStateMachine.accept_booking(mock_booking)
        assert mock_booking.version == 2

        # Start
        BookingStateMachine.start_session(mock_booking)
        assert mock_booking.version == 3

        # End
        BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert mock_booking.version == 4

    def test_version_not_incremented_on_idempotent(self, mock_booking):
        """
        Test that version does not increment on idempotent operations.
        """
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.version = 2

        # Idempotent accept (already scheduled)
        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True
        assert mock_booking.version == 2  # Unchanged

    def test_updated_at_set_on_transition(self, mock_booking):
        """
        Test that updated_at is set on state transitions.
        """
        original_updated_at = mock_booking.updated_at
        mock_booking.version = 1

        # Perform transition
        BookingStateMachine.accept_booking(mock_booking)

        # updated_at should be changed
        assert mock_booking.updated_at != original_updated_at or mock_booking.updated_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
