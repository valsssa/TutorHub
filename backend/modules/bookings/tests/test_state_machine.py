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

    def test_cannot_accept_scheduled_booking(self, mock_booking):
        """Cannot accept already scheduled booking."""
        mock_booking.session_state = SessionState.SCHEDULED.value

        result = BookingStateMachine.accept_booking(mock_booking)

        assert result.success is False
        assert "Cannot accept" in result.error_message

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

    def test_cannot_open_duplicate_dispute(self, mock_booking):
        """Cannot open dispute when one is already open."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.OPEN.value

        result = BookingStateMachine.open_dispute(
            mock_booking,
            reason="Another dispute",
            disputed_by_user_id=123,
        )

        assert result.success is False

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

    def test_resolve_already_resolved_dispute(self, mock_booking):
        """Cannot re-resolve an already resolved dispute."""
        mock_booking.session_state = SessionState.ENDED.value
        mock_booking.dispute_state = DisputeState.RESOLVED_UPHELD.value

        result = BookingStateMachine.resolve_dispute(
            mock_booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=999,
        )

        assert result.success is False
        assert "No open dispute" in result.error_message


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
