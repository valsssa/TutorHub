"""
Booking status enums and type definitions.

Four independent fields on one booking:
- session_state: Where is the booking lifecycle?
- session_outcome: How did it end?
- payment_state: What's the money status?
- dispute_state: Is there a dispute?
"""

from enum import Enum


class SessionState(str, Enum):
    """
    Booking lifecycle states (forward-only progression).

    State transitions:
        REQUESTED → SCHEDULED (tutor accepts)
        REQUESTED → CANCELLED (declined/cancelled)
        REQUESTED → EXPIRED (24h timeout)
        SCHEDULED → ACTIVE (auto at start_time)
        SCHEDULED → CANCELLED (manual)
        ACTIVE → ENDED (auto at end_time + grace)
    """

    REQUESTED = "REQUESTED"  # Waiting for tutor response
    SCHEDULED = "SCHEDULED"  # Confirmed, session upcoming
    ACTIVE = "ACTIVE"  # Session happening now
    ENDED = "ENDED"  # Session lifecycle complete (terminal)
    EXPIRED = "EXPIRED"  # Request timed out - 24h (terminal)
    CANCELLED = "CANCELLED"  # Explicitly cancelled (terminal)


class SessionOutcome(str, Enum):
    """
    How the session ended (only set for terminal states).

    Used when session_state is ENDED, CANCELLED, or EXPIRED.
    """

    COMPLETED = "COMPLETED"  # Session happened successfully
    NOT_HELD = "NOT_HELD"  # Session didn't happen (cancelled/expired)
    NO_SHOW_STUDENT = "NO_SHOW_STUDENT"  # Student didn't attend
    NO_SHOW_TUTOR = "NO_SHOW_TUTOR"  # Tutor didn't attend


class PaymentState(str, Enum):
    """
    Payment lifecycle states.

    All payment state changes are manual (no auto-transitions).
    """

    PENDING = "PENDING"  # Awaiting authorization
    AUTHORIZED = "AUTHORIZED"  # Funds held, ready to capture
    CAPTURED = "CAPTURED"  # Tutor earned payment
    VOIDED = "VOIDED"  # Authorization released (no capture)
    REFUNDED = "REFUNDED"  # Full refund issued
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"  # Partial refund issued


class DisputeState(str, Enum):
    """
    Dispute lifecycle states.

    All dispute state changes are manual (admin actions).
    """

    NONE = "NONE"  # No dispute filed
    OPEN = "OPEN"  # Under admin review
    RESOLVED_UPHELD = "RESOLVED_UPHELD"  # Original decision confirmed
    RESOLVED_REFUNDED = "RESOLVED_REFUNDED"  # Refund granted via dispute


class CancelledByRole(str, Enum):
    """Who cancelled the booking (only set when session_state=CANCELLED)."""

    STUDENT = "STUDENT"
    TUTOR = "TUTOR"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"  # Auto-expired


# Terminal session states (no further transitions allowed)
TERMINAL_SESSION_STATES = {SessionState.ENDED, SessionState.EXPIRED, SessionState.CANCELLED}

# States that allow cancellation
CANCELLABLE_SESSION_STATES = {SessionState.REQUESTED, SessionState.SCHEDULED}

# States that indicate an upcoming/active session
ACTIVE_SESSION_STATES = {SessionState.REQUESTED, SessionState.SCHEDULED, SessionState.ACTIVE}
