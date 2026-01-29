"""
Centralized booking state machine.

Manages all state transitions for session_state, payment_state, and dispute_state.
Enforces business rules and validates transitions.

Race Condition Prevention:
- Uses SELECT FOR UPDATE for pessimistic locking during transitions
- Implements optimistic locking via version column
- Makes transitions idempotent (returns success if already in target state)
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    from sqlalchemy.orm import Session


class OptimisticLockError(Exception):
    """Raised when optimistic lock version mismatch is detected."""

    pass


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    pass


@dataclass
class TransitionResult:
    """Result of a state transition attempt."""

    success: bool
    error_message: str | None = None
    already_in_target_state: bool = False  # Indicates idempotent success
    escalated_to_dispute: bool = False  # Indicates conflicting no-show reports
    restore_package_credit: bool = False  # Indicates package credit should be restored


class BookingStateMachine:
    """
    Centralized state machine for booking state management.

    Handles all state transitions with validation and business rule enforcement.
    Uses pessimistic locking (SELECT FOR UPDATE) and optimistic locking (version)
    to prevent race conditions.

    Transaction Safety:
    -------------------
    All state transition methods in this class are designed to be transaction-safe:
    - Methods modify the booking object in memory but DO NOT call db.commit()
    - The caller is responsible for committing the transaction
    - This allows the caller to wrap multiple operations in a single atomic transaction
    - Use the atomic_operation context manager from core.transactions for safety

    Example usage:
        from core.transactions import atomic_operation

        with atomic_operation(db):
            booking = BookingStateMachine.get_booking_with_lock(db, booking_id)
            result = BookingStateMachine.accept_booking(booking)
            if result.success:
                # Additional operations can be added here
                # All changes commit together on context exit
    """

    # Time limit for opening disputes after session end (in days)
    DISPUTE_WINDOW_DAYS = 30

    @staticmethod
    def get_booking_with_lock(
        db: "Session",
        booking_id: int,
        *,
        nowait: bool = False,
    ) -> "Booking | None":
        """
        Get a booking with a row-level lock for safe state transitions.

        Uses SELECT ... FOR UPDATE to acquire an exclusive lock on the row,
        preventing concurrent modifications.

        Args:
            db: SQLAlchemy session
            booking_id: ID of the booking to lock
            nowait: If True, fail immediately if lock cannot be acquired

        Returns:
            Locked Booking object or None if not found

        Raises:
            OperationalError: If nowait=True and lock cannot be acquired
        """
        from models import Booking

        query = db.query(Booking).filter(Booking.id == booking_id)

        if nowait:
            query = query.with_for_update(nowait=True)
        else:
            query = query.with_for_update()

        return query.first()

    @staticmethod
    def increment_version(booking: "Booking") -> None:
        """
        Increment the booking version after a state change.

        This must be called after every state transition to maintain
        optimistic locking integrity.
        """
        booking.version = (booking.version or 1) + 1
        booking.updated_at = datetime.utcnow()

    @staticmethod
    def verify_version(booking: "Booking", expected_version: int) -> bool:
        """
        Verify the booking version matches expected value.

        Args:
            booking: The booking to check
            expected_version: The version we expect the booking to have

        Returns:
            True if versions match, False otherwise
        """
        return booking.version == expected_version

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

        Idempotent: Returns success if already in SCHEDULED state.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already in target state
        if booking.session_state == SessionState.SCHEDULED.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        if not cls.can_transition_session_state(booking.session_state, SessionState.SCHEDULED):
            return TransitionResult(
                success=False,
                error_message=f"Cannot accept booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.SCHEDULED.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        booking.confirmed_at = datetime.utcnow()
        cls.increment_version(booking)

        return TransitionResult(success=True)

    @classmethod
    def decline_booking(cls, booking: "Booking") -> TransitionResult:
        """
        Tutor declines a booking request.

        Transitions:
        - session_state: REQUESTED → CANCELLED
        - session_outcome: NOT_HELD
        - payment_state: PENDING → VOIDED

        Idempotent: Returns success if already CANCELLED by tutor.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already cancelled by tutor
        if (
            booking.session_state == SessionState.CANCELLED.value
            and booking.cancelled_by_role == CancelledByRole.TUTOR.value
        ):
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

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
        cls.increment_version(booking)

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

        Idempotent: Returns success if already CANCELLED.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already cancelled
        if booking.session_state == SessionState.CANCELLED.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

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

        cls.increment_version(booking)

        return TransitionResult(success=True)

    @classmethod
    def expire_booking(cls, booking: "Booking") -> TransitionResult:
        """
        Expire a booking request (24h timeout).

        Transitions:
        - session_state: REQUESTED → EXPIRED
        - session_outcome: NOT_HELD
        - payment_state: PENDING → VOIDED

        Idempotent: Returns success if already EXPIRED.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already expired
        if booking.session_state == SessionState.EXPIRED.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        # Also idempotent if already in a terminal state that "beats" expiry
        # (e.g., tutor accepted/declined before expiry job ran)
        if booking.session_state in {
            SessionState.SCHEDULED.value,
            SessionState.CANCELLED.value,
        }:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        if booking.session_state != SessionState.REQUESTED.value:
            return TransitionResult(
                success=False,
                error_message=f"Cannot expire booking with state {booking.session_state}",
            )

        booking.session_state = SessionState.EXPIRED.value
        booking.session_outcome = SessionOutcome.NOT_HELD.value
        booking.payment_state = PaymentState.VOIDED.value
        booking.cancelled_by_role = CancelledByRole.SYSTEM.value
        cls.increment_version(booking)

        return TransitionResult(success=True)

    @classmethod
    def start_session(cls, booking: "Booking") -> TransitionResult:
        """
        Start a scheduled session (auto at start_time).

        Transitions:
        - session_state: SCHEDULED → ACTIVE

        Idempotent: Returns success if already ACTIVE.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already active
        if booking.session_state == SessionState.ACTIVE.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        # Also idempotent if session already ended
        if booking.session_state == SessionState.ENDED.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        if booking.session_state != SessionState.SCHEDULED.value:
            return TransitionResult(
                success=False,
                error_message=f"Cannot start session with state {booking.session_state}",
            )

        booking.session_state = SessionState.ACTIVE.value
        cls.increment_version(booking)

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
            outcome: How the session ended:
                - COMPLETED: Both parties attended, normal completion
                - NO_SHOW_STUDENT: Student didn't attend, tutor earns payment
                - NO_SHOW_TUTOR: Tutor didn't attend, student gets refund
                - NOT_HELD: Neither party attended, void payment

        Transitions:
        - session_state: ACTIVE → ENDED
        - session_outcome: Set to provided outcome
        - payment_state: Based on outcome

        Idempotent: Returns success if already ENDED with same outcome.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already ended
        if booking.session_state == SessionState.ENDED.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

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
        elif outcome == SessionOutcome.NOT_HELD:
            # Neither party joined - void the payment authorization
            # No one should be charged for a session that didn't happen
            booking.payment_state = PaymentState.VOIDED.value

        cls.increment_version(booking)

        return TransitionResult(success=True)

    @classmethod
    def mark_no_show(
        cls,
        booking: "Booking",
        who_was_absent: str,  # "STUDENT" or "TUTOR"
        reporter_role: str | None = None,  # "TUTOR" or "STUDENT" - who is reporting
    ) -> TransitionResult:
        """
        Mark a no-show for a session with race condition protection.

        This method handles the case where both parties may report no-show
        simultaneously. If conflicting reports exist, it escalates to dispute.

        Args:
            booking: The booking to mark as no-show (should be locked with FOR UPDATE)
            who_was_absent: "STUDENT" or "TUTOR" - who didn't show up
            reporter_role: "TUTOR" or "STUDENT" - who is making the report

        Returns:
            TransitionResult with escalated_to_dispute=True if conflicting reports

        Note:
            The booking should be acquired with get_booking_with_lock() before
            calling this method to prevent race conditions.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Determine reporter role if not provided (for backwards compatibility)
        if reporter_role is None:
            reporter_role = "TUTOR" if who_was_absent == "STUDENT" else "STUDENT"

        # Check if already ended with a no-show outcome
        if booking.session_state == SessionState.ENDED.value:
            if booking.session_outcome in {
                SessionOutcome.NO_SHOW_STUDENT.value,
                SessionOutcome.NO_SHOW_TUTOR.value,
            }:
                # Determine who reported first based on outcome
                existing_reporter = (
                    "TUTOR" if booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
                    else "STUDENT"
                )

                # Same reporter - idempotent success
                if existing_reporter == reporter_role:
                    return TransitionResult(
                        success=True,
                        already_in_target_state=True,
                    )

                # Conflicting reports! Auto-escalate to dispute
                # Store both reports for admin review
                existing_claim = (
                    "student was absent" if booking.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
                    else "tutor was absent"
                )
                new_claim = "tutor was absent" if who_was_absent == "TUTOR" else "student was absent"

                booking.dispute_state = DisputeState.OPEN.value
                booking.dispute_reason = (
                    f"Conflicting no-show reports: {existing_reporter} reported {existing_claim}, "
                    f"{reporter_role} reported {new_claim}. Requires admin review."
                )
                booking.disputed_at = datetime.utcnow()
                # Don't set disputed_by as this is a system-generated dispute
                cls.increment_version(booking)

                return TransitionResult(
                    success=True,
                    escalated_to_dispute=True,
                )

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

        cls.increment_version(booking)

        return TransitionResult(success=True)

    @classmethod
    def mark_no_show_with_lock(
        cls,
        db: "Session",
        booking_id: int,
        who_was_absent: str,
        reporter_role: str,
    ) -> tuple["Booking | None", TransitionResult]:
        """
        Mark no-show with row-level locking for race condition safety.

        This is the preferred method for marking no-shows from API endpoints.
        It acquires a row lock, checks for conflicts, and handles the transition
        atomically.

        Args:
            db: SQLAlchemy session
            booking_id: ID of the booking
            who_was_absent: "STUDENT" or "TUTOR"
            reporter_role: "TUTOR" or "STUDENT"

        Returns:
            Tuple of (locked_booking, TransitionResult)
        """
        # Acquire row lock to prevent race conditions
        booking = cls.get_booking_with_lock(db, booking_id)

        if not booking:
            return None, TransitionResult(
                success=False,
                error_message="Booking not found",
            )

        result = cls.mark_no_show(booking, who_was_absent, reporter_role)
        return booking, result

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
        Cannot open disputes on bookings where payment has already been refunded or voided.
        Must be filed within DISPUTE_WINDOW_DAYS of session completion.

        Idempotent: Returns success if already has OPEN dispute.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already has open dispute
        if booking.dispute_state == DisputeState.OPEN.value:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

        if not cls.is_terminal_session_state(booking.session_state):
            return TransitionResult(
                success=False,
                error_message="Can only dispute completed or cancelled bookings",
            )

        # Check dispute time window
        # Use the most relevant timestamp for when the session ended:
        # - end_time for completed sessions
        # - cancelled_at for cancelled sessions
        # - updated_at as fallback
        session_ended_at = booking.end_time
        if booking.cancelled_at:
            session_ended_at = booking.cancelled_at
        elif session_ended_at is None:
            session_ended_at = booking.updated_at

        if session_ended_at:
            # Ensure we're comparing timezone-aware datetimes
            now = datetime.now(UTC)
            # Handle both timezone-aware and naive datetimes from the database
            if session_ended_at.tzinfo is None:
                # Treat naive datetime as UTC
                days_since_end = (now.replace(tzinfo=None) - session_ended_at).days
            else:
                days_since_end = (now - session_ended_at).days

            if days_since_end > cls.DISPUTE_WINDOW_DAYS:
                return TransitionResult(
                    success=False,
                    error_message=(
                        f"Disputes must be filed within {cls.DISPUTE_WINDOW_DAYS} days "
                        f"of session completion. This session ended {days_since_end} days ago."
                    ),
                )

        # Check payment state - cannot dispute if already refunded or voided
        current_payment = PaymentState(booking.payment_state)
        if current_payment in {PaymentState.REFUNDED, PaymentState.VOIDED}:
            return TransitionResult(
                success=False,
                error_message="Cannot open dispute: payment has already been refunded or voided",
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
        cls.increment_version(booking)

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

        Idempotent: Returns success if already resolved.

        Transaction Safety: Does NOT commit - caller must commit the transaction.
        """
        # Idempotent check: already resolved
        if booking.dispute_state in {
            DisputeState.RESOLVED_UPHELD.value,
            DisputeState.RESOLVED_REFUNDED.value,
        }:
            return TransitionResult(
                success=True,
                already_in_target_state=True,
            )

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

        # Track whether package credit should be restored
        should_restore_package_credit = False

        # Update payment state if refunding
        if resolution == DisputeState.RESOLVED_REFUNDED:
            current_payment = PaymentState(booking.payment_state)
            # Skip refund if payment already refunded or voided - just update dispute state
            if current_payment in {PaymentState.REFUNDED, PaymentState.VOIDED}:
                # Payment already returned to student, just resolve the dispute
                cls.increment_version(booking)
                return TransitionResult(
                    success=True,
                    already_in_target_state=False,
                )
            elif current_payment == PaymentState.CAPTURED:
                if refund_amount_cents and refund_amount_cents < (booking.rate_cents or 0):
                    booking.payment_state = PaymentState.PARTIALLY_REFUNDED.value
                else:
                    booking.payment_state = PaymentState.REFUNDED.value
                # Full refund on package booking should restore credit
                should_restore_package_credit = True
            elif current_payment == PaymentState.AUTHORIZED:
                # Release the authorization instead of capturing and refunding
                booking.payment_state = PaymentState.VOIDED.value
                # Voided authorization on package booking should restore credit
                should_restore_package_credit = True

        cls.increment_version(booking)

        return TransitionResult(
            success=True,
            restore_package_credit=should_restore_package_credit,
        )
