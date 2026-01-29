"""
Centralized booking state machine.

Manages all state transitions for session_state, payment_state, and dispute_state.
Enforces business rules and validates transitions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from modules.bookings.domain.status import (
    CANCELLABLE_SESSION_STATES,
    TERMINAL_SESSION_STATES,
    CancelledByRole,
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)

if TYPE_CHECKING:
    from models import Booking


@dataclass
class TransitionResult:
    """Result of a state transition attempt."""

    success: bool
    error_message: str | None = None


class BookingStateMachine:
    """
    Centralized state machine for booking state management.

    Handles all state transitions with validation and business rule enforcement.
    """

    # Valid session_state transitions
    SESSION_STATE_TRANSITIONS: dict[SessionState, set[SessionState]] = {
        SessionState.REQUESTED: {
            SessionState.SCHEDULED,  # Tutor accepts
            SessionState.CANCELLED,  # Declined or cancelled
            SessionState.EXPIRED,  # 24h timeout
        },
        SessionState.SCHEDULED: {
            SessionState.ACTIVE,  # Auto at start_time
            SessionState.CANCELLED,  # Manual cancellation
        },
        SessionState.ACTIVE: {
            SessionState.ENDED,  # Auto at end_time + grace
        },
        # Terminal states - no transitions allowed
        SessionState.ENDED: set(),
        SessionState.EXPIRED: set(),
        SessionState.CANCELLED: set(),
    }

    # Valid payment_state transitions
    PAYMENT_STATE_TRANSITIONS: dict[PaymentState, set[PaymentState]] = {
        PaymentState.PENDING: {
            PaymentState.AUTHORIZED,
            PaymentState.VOIDED,  # Cancelled before auth
        },
        PaymentState.AUTHORIZED: {
            PaymentState.CAPTURED,
            PaymentState.VOIDED,
            PaymentState.REFUNDED,
        },
        PaymentState.CAPTURED: {
            PaymentState.REFUNDED,
            PaymentState.PARTIALLY_REFUNDED,
        },
        # Terminal payment states
        PaymentState.VOIDED: set(),
        PaymentState.REFUNDED: set(),
        PaymentState.PARTIALLY_REFUNDED: {
            PaymentState.REFUNDED,  # Can complete the refund
        },
    }

    # Valid dispute_state transitions
    DISPUTE_STATE_TRANSITIONS: dict[DisputeState, set[DisputeState]] = {
        DisputeState.NONE: {
            DisputeState.OPEN,
        },
        DisputeState.OPEN: {
            DisputeState.RESOLVED_UPHELD,
            DisputeState.RESOLVED_REFUNDED,
        },
        # Terminal dispute states
        DisputeState.RESOLVED_UPHELD: set(),
        DisputeState.RESOLVED_REFUNDED: set(),
    }

    @classmethod
    def can_transition_session_state(
        cls,
        current: SessionState | str,
        target: SessionState | str,
    ) -> bool:
        """Check if session_state transition is valid."""
        if isinstance(current, str):
            current = SessionState(current)
        if isinstance(target, str):
            target = SessionState(target)

        allowed = cls.SESSION_STATE_TRANSITIONS.get(current, set())
        return target in allowed

    @classmethod
    def can_transition_payment_state(
        cls,
        current: PaymentState | str,
        target: PaymentState | str,
    ) -> bool:
        """Check if payment_state transition is valid."""
        if isinstance(current, str):
            current = PaymentState(current)
        if isinstance(target, str):
            target = PaymentState(target)

        allowed = cls.PAYMENT_STATE_TRANSITIONS.get(current, set())
        return target in allowed

    @classmethod
    def can_transition_dispute_state(
        cls,
        current: DisputeState | str,
        target: DisputeState | str,
    ) -> bool:
        """Check if dispute_state transition is valid."""
        if isinstance(current, str):
            current = DisputeState(current)
        if isinstance(target, str):
            target = DisputeState(target)

        allowed = cls.DISPUTE_STATE_TRANSITIONS.get(current, set())
        return target in allowed

    @classmethod
    def is_terminal_session_state(cls, state: SessionState | str) -> bool:
        """Check if session_state is terminal (no further transitions)."""
        if isinstance(state, str):
            state = SessionState(state)
        return state in TERMINAL_SESSION_STATES

    @classmethod
    def is_cancellable(cls, state: SessionState | str) -> bool:
        """Check if booking can be cancelled from current state."""
        if isinstance(state, str):
            state = SessionState(state)
        return state in CANCELLABLE_SESSION_STATES

    @classmethod
    def accept_booking(cls, booking: "Booking") -> TransitionResult:
        """
        Tutor accepts a booking request.

        Transitions:
        - session_state: REQUESTED → SCHEDULED
        - payment_state: PENDING → AUTHORIZED
        """
        if not cls.can_transition_session_state(booking.session_state, SessionState.SCHEDULED):
            return TransitionResult(
                success=False,
                error_message=f"Cannot accept booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.SCHEDULED.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        booking.confirmed_at = datetime.utcnow()

        return TransitionResult(success=True)

    @classmethod
    def decline_booking(cls, booking: "Booking") -> TransitionResult:
        """
        Tutor declines a booking request.

        Transitions:
        - session_state: REQUESTED → CANCELLED
        - session_outcome: NOT_HELD
        - payment_state: PENDING → VOIDED
        """
        if not cls.can_transition_session_state(booking.session_state, SessionState.CANCELLED):
            return TransitionResult(
                success=False,
                error_message=f"Cannot decline booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.CANCELLED.value
        booking.session_outcome = SessionOutcome.NOT_HELD.value
        booking.payment_state = PaymentState.VOIDED.value
        booking.cancelled_by_role = CancelledByRole.TUTOR.value
        booking.cancelled_at = datetime.utcnow()

        return TransitionResult(success=True)

    @classmethod
    def cancel_booking(
        cls,
        booking: "Booking",
        cancelled_by: CancelledByRole,
        refund: bool = True,
    ) -> TransitionResult:
        """
        Cancel a booking.

        Args:
            booking: The booking to cancel
            cancelled_by: Who is cancelling (STUDENT, TUTOR, ADMIN, SYSTEM)
            refund: Whether to issue a refund

        Transitions:
        - session_state: REQUESTED/SCHEDULED → CANCELLED
        - session_outcome: NOT_HELD
        - payment_state: Depends on refund policy
        """
        if not cls.is_cancellable(booking.session_state):
            return TransitionResult(
                success=False,
                error_message=f"Cannot cancel booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.CANCELLED.value
        booking.session_outcome = SessionOutcome.NOT_HELD.value
        booking.cancelled_by_role = cancelled_by.value
        booking.cancelled_at = datetime.utcnow()

        # Determine payment state based on current state and refund decision
        current_payment = PaymentState(booking.payment_state)
        if refund:
            if current_payment == PaymentState.AUTHORIZED:
                booking.payment_state = PaymentState.REFUNDED.value
            elif current_payment == PaymentState.PENDING:
                booking.payment_state = PaymentState.VOIDED.value
            elif current_payment == PaymentState.CAPTURED:
                booking.payment_state = PaymentState.REFUNDED.value
        else:
            # No refund - void if pending/authorized, capture if already authorized
            if current_payment == PaymentState.PENDING:
                booking.payment_state = PaymentState.VOIDED.value
            elif current_payment == PaymentState.AUTHORIZED:
                booking.payment_state = PaymentState.CAPTURED.value

        return TransitionResult(success=True)

    @classmethod
    def expire_booking(cls, booking: "Booking") -> TransitionResult:
        """
        Expire a booking request (24h timeout).

        Transitions:
        - session_state: REQUESTED → EXPIRED
        - session_outcome: NOT_HELD
        - payment_state: PENDING → VOIDED
        """
        if booking.session_state != SessionState.REQUESTED.value:
            return TransitionResult(
                success=False,
                error_message=f"Cannot expire booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.EXPIRED.value
        booking.session_outcome = SessionOutcome.NOT_HELD.value
        booking.payment_state = PaymentState.VOIDED.value
        booking.cancelled_by_role = CancelledByRole.SYSTEM.value

        return TransitionResult(success=True)

    @classmethod
    def start_session(cls, booking: "Booking") -> TransitionResult:
        """
        Start a scheduled session (auto at start_time).

        Transitions:
        - session_state: SCHEDULED → ACTIVE
        """
        if booking.session_state != SessionState.SCHEDULED.value:
            return TransitionResult(
                success=False,
                error_message=f"Cannot start session with state {booking.session_state}",
            )

        booking.session_state = SessionState.ACTIVE.value
        return TransitionResult(success=True)

    @classmethod
    def end_session(
        cls,
        booking: "Booking",
        outcome: SessionOutcome = SessionOutcome.COMPLETED,
    ) -> TransitionResult:
        """
        End an active session (auto at end_time + grace).

        Args:
            booking: The booking to end
            outcome: How the session ended (COMPLETED, NO_SHOW_STUDENT, NO_SHOW_TUTOR)

        Transitions:
        - session_state: ACTIVE → ENDED
        - session_outcome: Set to provided outcome
        - payment_state: Based on outcome
        """
        if booking.session_state != SessionState.ACTIVE.value:
            return TransitionResult(
                success=False,
                error_message=f"Cannot end session with state {booking.session_state}",
            )

        booking.session_state = SessionState.ENDED.value
        booking.session_outcome = outcome.value

        # Set payment state based on outcome
        if outcome == SessionOutcome.COMPLETED:
            booking.payment_state = PaymentState.CAPTURED.value
        elif outcome == SessionOutcome.NO_SHOW_STUDENT:
            # Tutor earns payment when student is no-show
            booking.payment_state = PaymentState.CAPTURED.value
        elif outcome == SessionOutcome.NO_SHOW_TUTOR:
            # Student gets refund when tutor is no-show
            booking.payment_state = PaymentState.REFUNDED.value

        return TransitionResult(success=True)

    @classmethod
    def mark_no_show(
        cls,
        booking: "Booking",
        who_was_absent: str,  # "STUDENT" or "TUTOR"
    ) -> TransitionResult:
        """
        Mark a no-show for a session.

        This can be called on ACTIVE or SCHEDULED sessions.
        """
        current_state = SessionState(booking.session_state)

        # Can mark no-show on SCHEDULED (after start time) or ACTIVE sessions
        if current_state not in {SessionState.SCHEDULED, SessionState.ACTIVE}:
            return TransitionResult(
                success=False,
                error_message=f"Cannot mark no-show for booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.ENDED.value

        if who_was_absent == "STUDENT":
            booking.session_outcome = SessionOutcome.NO_SHOW_STUDENT.value
            booking.payment_state = PaymentState.CAPTURED.value
        else:  # TUTOR
            booking.session_outcome = SessionOutcome.NO_SHOW_TUTOR.value
            booking.payment_state = PaymentState.REFUNDED.value

        return TransitionResult(success=True)

    @classmethod
    def open_dispute(
        cls,
        booking: "Booking",
        reason: str,
        disputed_by_user_id: int,
    ) -> TransitionResult:
        """
        Open a dispute on a booking.

        Can only open disputes on terminal session states.
        """
        if not cls.is_terminal_session_state(booking.session_state):
            return TransitionResult(
                success=False,
                error_message="Can only dispute completed or cancelled bookings",
            )

        if not cls.can_transition_dispute_state(booking.dispute_state, DisputeState.OPEN):
            return TransitionResult(
                success=False,
                error_message=f"Cannot open dispute with current state {booking.dispute_state}",
            )

        booking.dispute_state = DisputeState.OPEN.value
        booking.dispute_reason = reason
        booking.disputed_at = datetime.utcnow()
        booking.disputed_by = disputed_by_user_id

        return TransitionResult(success=True)

    @classmethod
    def resolve_dispute(
        cls,
        booking: "Booking",
        resolution: DisputeState,  # RESOLVED_UPHELD or RESOLVED_REFUNDED
        resolved_by_user_id: int,
        notes: str | None = None,
        refund_amount_cents: int | None = None,
    ) -> TransitionResult:
        """
        Resolve a dispute (admin action).

        Args:
            booking: The booking with dispute
            resolution: RESOLVED_UPHELD or RESOLVED_REFUNDED
            resolved_by_user_id: Admin user ID
            notes: Resolution notes
            refund_amount_cents: Amount to refund (for partial refunds)
        """
        if booking.dispute_state != DisputeState.OPEN.value:
            return TransitionResult(
                success=False,
                error_message="No open dispute to resolve",
            )

        if resolution not in {DisputeState.RESOLVED_UPHELD, DisputeState.RESOLVED_REFUNDED}:
            return TransitionResult(
                success=False,
                error_message="Invalid resolution state",
            )

        booking.dispute_state = resolution.value
        booking.resolved_at = datetime.utcnow()
        booking.resolved_by = resolved_by_user_id
        booking.resolution_notes = notes

        # Update payment state if refunding
        if resolution == DisputeState.RESOLVED_REFUNDED:
            current_payment = PaymentState(booking.payment_state)
            if current_payment == PaymentState.CAPTURED:
                if refund_amount_cents and refund_amount_cents < (booking.rate_cents or 0):
                    booking.payment_state = PaymentState.PARTIALLY_REFUNDED.value
                else:
                    booking.payment_state = PaymentState.REFUNDED.value

        return TransitionResult(success=True)
