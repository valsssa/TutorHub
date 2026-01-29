"""
Tests for booking state machine.
Tests state transitions, dispute handling, and edge cases.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from modules.bookings.domain.state_machine import BookingStateMachine, TransitionResult
from modules.bookings.domain.status import (
    CancelledByRole,
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_booking():
    """Create a mock booking object."""
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
    booking.version = 1  # Optimistic locking version
    booking.updated_at = None
    return booking


# ============================================================================
# Session State Transition Tests
# ============================================================================


class TestSessionStateTransitions:
    """Test session_state transition validation."""

    def test_requested_to_scheduled(self):
        """REQUESTED → SCHEDULED is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.SCHEDULED
        )

    def test_requested_to_cancelled(self):
        """REQUESTED → CANCELLED is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.CANCELLED
        )

    def test_requested_to_expired(self):
        """REQUESTED → EXPIRED is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.EXPIRED
        )

    def test_scheduled_to_active(self):
        """SCHEDULED → ACTIVE is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.SCHEDULED, SessionState.ACTIVE
        )

    def test_scheduled_to_cancelled(self):
        """SCHEDULED → CANCELLED is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.SCHEDULED, SessionState.CANCELLED
        )

    def test_active_to_ended(self):
        """ACTIVE → ENDED is valid."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.ACTIVE, SessionState.ENDED
        )

    def test_invalid_backwards_transition(self):
        """Cannot transition backwards."""
        assert not BookingStateMachine.can_transition_session_state(
            SessionState.SCHEDULED, SessionState.REQUESTED
        )
        assert not BookingStateMachine.can_transition_session_state(
            SessionState.ENDED, SessionState.ACTIVE
        )

    def test_invalid_skip_transition(self):
        """Cannot skip intermediate states."""
        assert not BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.ACTIVE
        )
        assert not BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.ENDED
        )


# ============================================================================
# Accept Booking Tests
# ============================================================================


class TestAcceptBooking:
    """Test accepting booking requests."""

    def test_accept_requested_booking(self, mock_booking):
        """Accept booking in REQUESTED state."""
        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value
        assert mock_booking.payment_state == PaymentState.AUTHORIZED.value
        assert mock_booking.confirmed_at is not None

    def test_accept_scheduled_booking_is_idempotent(self, mock_booking):
        """Accepting already scheduled booking is idempotent (returns success)."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_cannot_accept_cancelled_booking(self, mock_booking):
        """Cannot accept cancelled booking."""
        mock_booking.session_state = SessionState.CANCELLED.value

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is False


# ============================================================================
# Decline Booking Tests
# ============================================================================


class TestDeclineBooking:
    """Test declining booking requests."""

    def test_decline_requested_booking(self, mock_booking):
        """Decline booking in REQUESTED state."""
        result = BookingStateMachine.decline_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.CANCELLED.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value
        assert mock_booking.cancelled_by_role == CancelledByRole.TUTOR.value

    def test_cannot_decline_active_booking(self, mock_booking):
        """Cannot decline active booking."""
        mock_booking.session_state = SessionState.ACTIVE.value

        result = BookingStateMachine.decline_booking(mock_booking)

        assert result.success is False


# ============================================================================
# Cancel Booking Tests
# ============================================================================


class TestCancelBooking:
    """Test cancelling bookings."""

    def test_cancel_requested_with_refund(self, mock_booking):
        """Cancel REQUESTED booking with refund."""
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.session_state == SessionState.CANCELLED.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert mock_booking.cancelled_by_role == CancelledByRole.STUDENT.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value

    def test_cancel_scheduled_with_refund(self, mock_booking):
        """Cancel SCHEDULED booking with refund."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.TUTOR,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_cancel_scheduled_without_refund(self, mock_booking):
        """Cancel SCHEDULED booking without refund (late student cancel)."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=False,
        )

        assert result.success is True
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_cannot_cancel_active_booking(self, mock_booking):
        """Cannot cancel ACTIVE booking."""
        mock_booking.session_state = SessionState.ACTIVE.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True,
        )

        assert result.success is False


# ============================================================================
# Expire Booking Tests
# ============================================================================


class TestExpireBooking:
    """Test expiring booking requests."""

    def test_expire_requested_booking(self, mock_booking):
        """Expire REQUESTED booking after 24h timeout."""
        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.EXPIRED.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value
        assert mock_booking.cancelled_by_role == CancelledByRole.SYSTEM.value

    def test_cannot_expire_scheduled_booking(self, mock_booking):
        """Cannot expire SCHEDULED booking."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is False


# ============================================================================
# Session Start/End Tests
# ============================================================================


class TestSessionLifecycle:
    """Test session start and end transitions."""

    def test_start_scheduled_session(self, mock_booking):
        """Start SCHEDULED session at start_time."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.ACTIVE.value

    def test_cannot_start_requested_session(self, mock_booking):
        """Cannot start REQUESTED session."""
        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is False

    def test_end_active_session_completed(self, mock_booking):
        """End ACTIVE session with COMPLETED outcome."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)

        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value
        assert mock_booking.session_outcome == SessionOutcome.COMPLETED.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_cannot_end_scheduled_session(self, mock_booking):
        """Cannot end SCHEDULED session directly."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)

        assert result.success is False


# ============================================================================
# No-Show Tests
# ============================================================================


class TestNoShow:
    """Test no-show marking."""

    def test_mark_student_no_show(self, mock_booking):
        """Mark student as no-show."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT")

        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_mark_tutor_no_show(self, mock_booking):
        """Mark tutor as no-show."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.mark_no_show(mock_booking, "TUTOR")

        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_TUTOR.value
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_mark_no_show_on_scheduled(self, mock_booking):
        """Can mark no-show on SCHEDULED session (past start time)."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT")

        assert result.success is True

    def test_conflicting_no_show_reports_escalate_to_dispute(self, mock_booking):
        """Conflicting no-show reports auto-escalate to dispute."""
        # First: tutor reports student as no-show
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value
        mock_booking.dispute_state = DisputeState.NONE.value

        result1 = BookingStateMachine.mark_no_show(mock_booking, "STUDENT", reporter_role="TUTOR")
        assert result1.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value

        # Second: student reports tutor as no-show (conflicting report)
        result2 = BookingStateMachine.mark_no_show(mock_booking, "TUTOR", reporter_role="STUDENT")

        assert result2.success is True
        assert result2.escalated_to_dispute is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value
        assert "Conflicting no-show reports" in mock_booking.dispute_reason
        assert mock_booking.disputed_at is not None

    def test_same_reporter_no_show_is_idempotent(self, mock_booking):
        """Same reporter reporting no-show again is idempotent."""
        # First: tutor reports student as no-show
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result1 = BookingStateMachine.mark_no_show(mock_booking, "STUDENT", reporter_role="TUTOR")
        assert result1.success is True
        assert not result1.already_in_target_state

        # Same reporter reports again (idempotent)
        result2 = BookingStateMachine.mark_no_show(mock_booking, "STUDENT", reporter_role="TUTOR")
        assert result2.success is True
        assert result2.already_in_target_state is True
        assert result2.escalated_to_dispute is False

    def test_no_show_with_reporter_role_explicit(self, mock_booking):
        """No-show with explicit reporter_role parameter."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.mark_no_show(
            mock_booking, "STUDENT", reporter_role="TUTOR"
        )

        assert result.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value

    def test_no_show_backwards_compatibility_without_reporter(self, mock_booking):
        """No-show without reporter_role infers it from who_was_absent."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        # Without reporter_role, it infers TUTOR from STUDENT absence
        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT")

        assert result.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value


# ============================================================================
# Dispute Tests
# ============================================================================


class TestDisputes:
    """Test dispute handling."""

    def test_open_dispute_on_ended_booking(self, mock_booking):
        """Open dispute on ENDED booking."""
        mock_booking.session_state = SessionState.ENDED.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Tutor didn't teach properly",
            disputed_by_user_id=123,
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value
        assert mock_booking.dispute_reason == "Tutor didn't teach properly"
        assert mock_booking.disputed_by == 123
        assert mock_booking.disputed_at is not None

    def test_open_dispute_on_cancelled_booking(self, mock_booking):
        """Open dispute on CANCELLED booking."""
        mock_booking.session_state = SessionState.CANCELLED.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Unfair cancellation",
            disputed_by_user_id=456,
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.OPEN.value

    def test_cannot_open_dispute_on_active_booking(self, mock_booking):
        """Cannot open dispute on ACTIVE booking."""
        mock_booking.session_state = SessionState.ACTIVE.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Test",
            disputed_by_user_id=123,
        )

        assert result.success is False
        assert "terminal" in result.error_message.lower() or "completed" in result.error_message.lower()

    def test_cannot_open_dispute_on_refunded_booking(self, mock_booking):
        """Cannot open dispute when payment already refunded."""
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.payment_state = PaymentState.REFUNDED.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Unfair cancellation",
            disputed_by_user_id=123,
        )

        assert result.success is False
        assert "refunded" in result.error_message.lower()

    def test_cannot_open_dispute_on_voided_booking(self, mock_booking):
        """Cannot open dispute when payment already voided."""
        mock_booking.session_state = SessionState.EXPIRED.value
        mock_booking.payment_state = PaymentState.VOIDED.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Should have been accepted",
            disputed_by_user_id=123,
        )

        assert result.success is False
        assert "voided" in result.error_message.lower()

    def test_open_dispute_is_idempotent(self, mock_booking):
        """Opening dispute when one is already open is idempotent."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Another dispute",
            disputed_by_user_id=123,
        )

        assert result.success is True
        assert result.already_in_target_state is True

    def test_resolve_dispute_upheld(self, mock_booking):
        """Resolve dispute as UPHELD (original decision stands)."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
            notes="Original decision was correct",
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_UPHELD.value
        assert mock_booking.resolved_by == 999
        assert mock_booking.resolution_notes == "Original decision was correct"
        assert mock_booking.resolved_at is not None
        # Payment state unchanged for UPHELD
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_resolve_dispute_refunded(self, mock_booking):
        """Resolve dispute as REFUNDED (refund granted)."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Student's complaint valid",
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_REFUNDED.value
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_resolve_dispute_partial_refund(self, mock_booking):
        """Resolve dispute with partial refund."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Partial refund approved",
            refund_amount_cents=2500,  # Half refund
        )

        assert result.success is True
        assert mock_booking.payment_state == PaymentState.PARTIALLY_REFUNDED.value

    def test_cannot_resolve_without_open_dispute(self, mock_booking):
        """Cannot resolve if no dispute is open."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.NONE.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
        )

        assert result.success is False
        assert "No open dispute" in result.error_message


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_string_state_values(self, mock_booking):
        """State machine accepts string values."""
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "SCHEDULED")
        assert BookingStateMachine.can_transition_payment_state("PENDING", "AUTHORIZED")
        assert BookingStateMachine.can_transition_dispute_state("NONE", "OPEN")

    def test_enum_state_values(self, mock_booking):
        """State machine accepts enum values."""
        assert BookingStateMachine.can_transition_session_state(
            SessionState.REQUESTED, SessionState.SCHEDULED
        )
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.PENDING, PaymentState.AUTHORIZED
        )

    def test_terminal_state_checks(self, mock_booking):
        """Terminal state helper method works correctly."""
        assert BookingStateMachine.is_terminal_session_state(SessionState.ENDED)
        assert BookingStateMachine.is_terminal_session_state(SessionState.CANCELLED)
        assert BookingStateMachine.is_terminal_session_state(SessionState.EXPIRED)
        assert not BookingStateMachine.is_terminal_session_state(SessionState.REQUESTED)
        assert not BookingStateMachine.is_terminal_session_state(SessionState.SCHEDULED)
        assert not BookingStateMachine.is_terminal_session_state(SessionState.ACTIVE)

    def test_cancellable_state_checks(self, mock_booking):
        """Cancellable state helper method works correctly."""
        assert BookingStateMachine.is_cancellable(SessionState.REQUESTED)
        assert BookingStateMachine.is_cancellable(SessionState.SCHEDULED)
        assert not BookingStateMachine.is_cancellable(SessionState.ACTIVE)
        assert not BookingStateMachine.is_cancellable(SessionState.ENDED)
        assert not BookingStateMachine.is_cancellable(SessionState.CANCELLED)


# ============================================================================
# Payment State Transition Tests
# ============================================================================


class TestPaymentStateTransitions:
    """Test payment_state transition validation."""

    def test_pending_to_authorized(self):
        """PENDING → AUTHORIZED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.PENDING, PaymentState.AUTHORIZED
        )

    def test_pending_to_voided(self):
        """PENDING → VOIDED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.PENDING, PaymentState.VOIDED
        )

    def test_authorized_to_captured(self):
        """AUTHORIZED → CAPTURED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.AUTHORIZED, PaymentState.CAPTURED
        )

    def test_authorized_to_refunded(self):
        """AUTHORIZED → REFUNDED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.AUTHORIZED, PaymentState.REFUNDED
        )

    def test_captured_to_refunded(self):
        """CAPTURED → REFUNDED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.CAPTURED, PaymentState.REFUNDED
        )

    def test_captured_to_partially_refunded(self):
        """CAPTURED → PARTIALLY_REFUNDED is valid."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.CAPTURED, PaymentState.PARTIALLY_REFUNDED
        )

    def test_partially_refunded_to_refunded(self):
        """PARTIALLY_REFUNDED → REFUNDED is valid (complete refund)."""
        assert BookingStateMachine.can_transition_payment_state(
            PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED
        )

    def test_cannot_transition_from_voided(self):
        """VOIDED is terminal - no transitions allowed."""
        assert not BookingStateMachine.can_transition_payment_state(
            PaymentState.VOIDED, PaymentState.AUTHORIZED
        )
        assert not BookingStateMachine.can_transition_payment_state(
            PaymentState.VOIDED, PaymentState.REFUNDED
        )

    def test_cannot_transition_from_refunded(self):
        """REFUNDED is terminal - no transitions allowed."""
        assert not BookingStateMachine.can_transition_payment_state(
            PaymentState.REFUNDED, PaymentState.CAPTURED
        )

    def test_invalid_backwards_payment_transition(self):
        """Cannot transition backwards in payment states."""
        assert not BookingStateMachine.can_transition_payment_state(
            PaymentState.CAPTURED, PaymentState.AUTHORIZED
        )
        assert not BookingStateMachine.can_transition_payment_state(
            PaymentState.AUTHORIZED, PaymentState.PENDING
        )


# ============================================================================
# Dispute State Transition Tests
# ============================================================================


class TestDisputeStateTransitions:
    """Test dispute_state transition validation."""

    def test_none_to_open(self):
        """NONE → OPEN is valid."""
        assert BookingStateMachine.can_transition_dispute_state(
            DisputeState.NONE, DisputeState.OPEN
        )

    def test_open_to_resolved_upheld(self):
        """OPEN → RESOLVED_UPHELD is valid."""
        assert BookingStateMachine.can_transition_dispute_state(
            DisputeState.OPEN, DisputeState.RESOLVED_UPHELD
        )

    def test_open_to_resolved_refunded(self):
        """OPEN → RESOLVED_REFUNDED is valid."""
        assert BookingStateMachine.can_transition_dispute_state(
            DisputeState.OPEN, DisputeState.RESOLVED_REFUNDED
        )

    def test_cannot_reopen_resolved_dispute(self):
        """Cannot reopen resolved disputes."""
        assert not BookingStateMachine.can_transition_dispute_state(
            DisputeState.RESOLVED_UPHELD, DisputeState.OPEN
        )
        assert not BookingStateMachine.can_transition_dispute_state(
            DisputeState.RESOLVED_REFUNDED, DisputeState.OPEN
        )

    def test_cannot_change_resolved_disputes(self):
        """Cannot change between resolved states."""
        assert not BookingStateMachine.can_transition_dispute_state(
            DisputeState.RESOLVED_UPHELD, DisputeState.RESOLVED_REFUNDED
        )
        assert not BookingStateMachine.can_transition_dispute_state(
            DisputeState.RESOLVED_REFUNDED, DisputeState.RESOLVED_UPHELD
        )


# ============================================================================
# Cancel Booking Additional Tests
# ============================================================================


class TestCancelBookingAdvanced:
    """Additional cancel booking tests for edge cases."""

    def test_cancel_with_captured_payment_refund(self, mock_booking):
        """Cancel with CAPTURED payment and refund."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.payment_state = PaymentState.CAPTURED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.ADMIN,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_cancel_by_admin(self, mock_booking):
        """Admin can cancel bookings."""
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.ADMIN,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.cancelled_by_role == CancelledByRole.ADMIN.value

    def test_cancel_by_system(self, mock_booking):
        """System can cancel bookings."""
        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.SYSTEM,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.cancelled_by_role == CancelledByRole.SYSTEM.value


# ============================================================================
# End Session Additional Tests
# ============================================================================


class TestEndSessionAdvanced:
    """Additional end session tests for different outcomes."""

    def test_end_session_no_show_student(self, mock_booking):
        """End session with student no-show outcome."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.end_session(
            mock_booking, SessionOutcome.NO_SHOW_STUDENT
        )

        assert result.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_end_session_no_show_tutor(self, mock_booking):
        """End session with tutor no-show outcome."""
        mock_booking.session_state = SessionState.ACTIVE.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value

        result = BookingStateMachine.end_session(
            mock_booking, SessionOutcome.NO_SHOW_TUTOR
        )

        assert result.success is True
        assert mock_booking.session_outcome == SessionOutcome.NO_SHOW_TUTOR.value
        assert mock_booking.payment_state == PaymentState.REFUNDED.value


# ============================================================================
# Resolve Dispute Additional Tests
# ============================================================================


class TestResolveDisputeAdvanced:
    """Additional dispute resolution tests."""

    def test_resolve_with_invalid_resolution_state(self, mock_booking):
        """Cannot resolve with non-resolution dispute states."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.NONE,  # Invalid resolution
            resolved_by_user_id=999,
        )

        assert result.success is False
        assert "Invalid resolution" in result.error_message

    def test_resolve_with_open_state(self, mock_booking):
        """Cannot resolve with OPEN as resolution."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.OPEN,  # Invalid resolution
            resolved_by_user_id=999,
        )

        assert result.success is False

    def test_resolve_already_resolved_dispute_is_idempotent(self, mock_booking):
        """Resolving already resolved dispute is idempotent."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.RESOLVED_UPHELD.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
        )

        assert result.success is True
        assert result.already_in_target_state is True

    def test_resolve_dispute_refunded_skips_refund_if_already_refunded(self, mock_booking):
        """Resolving dispute with refund when payment already refunded just updates dispute state."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.REFUNDED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Refund already issued",
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_REFUNDED.value
        # Payment state should remain REFUNDED (not change)
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_resolve_dispute_refunded_skips_refund_if_voided(self, mock_booking):
        """Resolving dispute with refund when payment voided just updates dispute state."""
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.VOIDED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Payment was already voided",
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_REFUNDED.value
        # Payment state should remain VOIDED (not attempt refund)
        assert mock_booking.payment_state == PaymentState.VOIDED.value

    def test_resolve_dispute_refunded_voids_authorized_payment(self, mock_booking):
        """Resolving dispute with refund when payment authorized should void."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Release authorization to student",
        )

        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_REFUNDED.value
        # Payment should be voided (authorization released) not captured then refunded
        assert mock_booking.payment_state == PaymentState.VOIDED.value


# ============================================================================
# State Machine Consistency Tests
# ============================================================================


class TestStateMachineConsistency:
    """Test overall state machine consistency and behavior."""

    def test_full_successful_booking_lifecycle(self, mock_booking):
        """Test complete successful booking flow."""
        # Step 1: Accept booking
        result = BookingStateMachine.accept_booking(mock_booking)
        assert result.success is True
        assert mock_booking.session_state == SessionState.SCHEDULED.value
        assert mock_booking.payment_state == PaymentState.AUTHORIZED.value

        # Step 2: Start session
        result = BookingStateMachine.start_session(mock_booking)
        assert result.success is True
        assert mock_booking.session_state == SessionState.ACTIVE.value

        # Step 3: End session
        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)
        assert result.success is True
        assert mock_booking.session_state == SessionState.ENDED.value
        assert mock_booking.session_outcome == SessionOutcome.COMPLETED.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_declined_booking_lifecycle(self, mock_booking):
        """Test declined booking flow."""
        result = BookingStateMachine.decline_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.CANCELLED.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value
        assert mock_booking.cancelled_by_role == CancelledByRole.TUTOR.value

    def test_expired_booking_lifecycle(self, mock_booking):
        """Test expired booking flow."""
        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert mock_booking.session_state == SessionState.EXPIRED.value
        assert mock_booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert mock_booking.payment_state == PaymentState.VOIDED.value
        assert mock_booking.cancelled_by_role == CancelledByRole.SYSTEM.value

    def test_disputed_booking_resolved_upheld(self, mock_booking):
        """Test disputed booking resolved in tutor's favor."""
        # Complete the booking first
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.COMPLETED.value
        mock_booking.payment_state = PaymentState.CAPTURED.value

        # Open dispute
        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Service not as described",
            disputed_by_user_id=123,
        )
        assert result.success is True

        # Resolve dispute - upheld
        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
            notes="Tutor provided service as advertised",
        )
        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_UPHELD.value
        assert mock_booking.payment_state == PaymentState.CAPTURED.value  # Unchanged

    def test_disputed_booking_resolved_refunded(self, mock_booking):
        """Test disputed booking resolved in student's favor."""
        # Complete the booking first
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.COMPLETED.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        # Open dispute
        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Tutor was unprepared",
            disputed_by_user_id=123,
        )
        assert result.success is True

        # Resolve dispute - refunded
        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Student complaint validated",
        )
        assert result.success is True
        assert mock_booking.dispute_state == DisputeState.RESOLVED_REFUNDED.value
        assert mock_booking.payment_state == PaymentState.REFUNDED.value


# ============================================================================
# Idempotent Transition Tests
# ============================================================================


class TestIdempotentTransitions:
    """Test idempotent state transition behavior."""

    def test_accept_booking_is_idempotent(self, mock_booking):
        """Accepting an already scheduled booking is idempotent."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        initial_version = mock_booking.version

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True
        # Version should not change for idempotent no-op
        assert mock_booking.version == initial_version

    def test_cancel_booking_is_idempotent(self, mock_booking):
        """Cancelling an already cancelled booking is idempotent."""
        mock_booking.session_state = SessionState.CANCELLED.value

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True,
        )

        assert result.success is True
        assert result.already_in_target_state is True

    def test_expire_booking_is_idempotent(self, mock_booking):
        """Expiring an already expired booking is idempotent."""
        mock_booking.session_state = SessionState.EXPIRED.value

        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_expire_booking_skips_scheduled(self, mock_booking):
        """Expire is idempotent when booking was already scheduled."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_start_session_is_idempotent(self, mock_booking):
        """Starting an already active session is idempotent."""
        mock_booking.session_state = SessionState.ACTIVE.value

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_start_session_skips_ended(self, mock_booking):
        """Start is idempotent when session has already ended."""
        mock_booking.session_state = SessionState.ENDED.value

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_end_session_is_idempotent(self, mock_booking):
        """Ending an already ended session is idempotent."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.COMPLETED.value

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)

        assert result.success is True
        assert result.already_in_target_state is True

    def test_mark_no_show_is_idempotent(self, mock_booking):
        """Marking no-show on already ended session is idempotent (same reporter)."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.session_outcome = SessionOutcome.NO_SHOW_STUDENT.value

        # Same reporter (TUTOR) reports same thing again
        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT", reporter_role="TUTOR")

        assert result.success is True
        assert result.already_in_target_state is True
        assert result.escalated_to_dispute is False


# ============================================================================
# Version Increment Tests
# ============================================================================


class TestVersionIncrement:
    """Test that version is incremented on state transitions."""

    def test_accept_booking_increments_version(self, mock_booking):
        """Accept booking increments version."""
        initial_version = mock_booking.version

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is True
        assert result.already_in_target_state is False
        assert mock_booking.version == initial_version + 1

    def test_decline_booking_increments_version(self, mock_booking):
        """Decline booking increments version."""
        initial_version = mock_booking.version

        result = BookingStateMachine.decline_booking(mock_booking)

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_cancel_booking_increments_version(self, mock_booking):
        """Cancel booking increments version."""
        initial_version = mock_booking.version

        result = BookingStateMachine.cancel_booking(
            mock_booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True,
        )

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_expire_booking_increments_version(self, mock_booking):
        """Expire booking increments version."""
        initial_version = mock_booking.version

        result = BookingStateMachine.expire_booking(mock_booking)

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_start_session_increments_version(self, mock_booking):
        """Start session increments version."""
        mock_booking.session_state = SessionState.SCHEDULED.value
        initial_version = mock_booking.version

        result = BookingStateMachine.start_session(mock_booking)

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_end_session_increments_version(self, mock_booking):
        """End session increments version."""
        mock_booking.session_state = SessionState.ACTIVE.value
        initial_version = mock_booking.version

        result = BookingStateMachine.end_session(mock_booking, SessionOutcome.COMPLETED)

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_mark_no_show_increments_version(self, mock_booking):
        """Mark no-show increments version."""
        mock_booking.session_state = SessionState.ACTIVE.value
        initial_version = mock_booking.version

        result = BookingStateMachine.mark_no_show(mock_booking, "STUDENT")

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_open_dispute_increments_version(self, mock_booking):
        """Open dispute increments version."""
        mock_booking.session_state = SessionState.ENDED.value
        initial_version = mock_booking.version

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Test dispute",
            disputed_by_user_id=123,
        )

        assert result.success is True
        assert mock_booking.version == initial_version + 1

    def test_resolve_dispute_increments_version(self, mock_booking):
        """Resolve dispute increments version."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        initial_version = mock_booking.version

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
        )

        assert result.success is True
        assert mock_booking.version == initial_version + 1


# ============================================================================
# Package Credit Restoration Flag Tests
# ============================================================================


class TestPackageCreditRestorationFlag:
    """Test that resolve_dispute correctly sets restore_package_credit flag."""

    def test_resolve_dispute_refunded_captured_payment_sets_flag(self, mock_booking):
        """Dispute resolution with refund on captured payment should set restore flag."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Refund granted",
        )

        assert result.success is True
        assert result.restore_package_credit is True
        assert mock_booking.payment_state == PaymentState.REFUNDED.value

    def test_resolve_dispute_refunded_authorized_payment_sets_flag(self, mock_booking):
        """Dispute resolution with voided authorization should set restore flag."""
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.AUTHORIZED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Release authorization",
        )

        assert result.success is True
        assert result.restore_package_credit is True
        assert mock_booking.payment_state == PaymentState.VOIDED.value

    def test_resolve_dispute_upheld_does_not_set_flag(self, mock_booking):
        """Dispute resolution upheld should NOT set restore flag."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=999,
            notes="Original decision correct",
        )

        assert result.success is True
        assert result.restore_package_credit is False
        assert mock_booking.payment_state == PaymentState.CAPTURED.value

    def test_resolve_dispute_already_refunded_does_not_set_flag(self, mock_booking):
        """Dispute resolution when payment already refunded should NOT set restore flag."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.REFUNDED.value  # Already refunded

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Payment already returned",
        )

        assert result.success is True
        assert result.restore_package_credit is False  # Credit should have been restored when originally refunded

    def test_resolve_dispute_already_voided_does_not_set_flag(self, mock_booking):
        """Dispute resolution when payment already voided should NOT set restore flag."""
        mock_booking.session_state = SessionState.CANCELLED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.VOIDED.value  # Already voided

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
        )

        assert result.success is True
        assert result.restore_package_credit is False  # Credit should have been restored when originally voided

    def test_partial_refund_sets_restore_flag(self, mock_booking):
        """Partial refund dispute resolution should still set restore flag."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value
        mock_booking.payment_state = PaymentState.CAPTURED.value
        mock_booking.rate_cents = 5000

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
            notes="Partial refund",
            refund_amount_cents=2500,  # Half refund
        )

        assert result.success is True
        assert result.restore_package_credit is True
        assert mock_booking.payment_state == PaymentState.PARTIALLY_REFUNDED.value

    def test_idempotent_resolve_does_not_set_flag(self, mock_booking):
        """Idempotent resolve (already resolved) should NOT set restore flag."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.RESOLVED_REFUNDED.value  # Already resolved

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
        )

        assert result.success is True
        assert result.already_in_target_state is True
        assert result.restore_package_credit is False  # Already handled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
