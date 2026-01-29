"""
Booking domain layer.

Contains domain entities, value objects, and business rules for the booking system.
"""

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

__all__ = [
    "SessionState",
    "SessionOutcome",
    "PaymentState",
    "DisputeState",
    "CancelledByRole",
    "BookingStateMachine",
    "OptimisticLockError",
    "StateTransitionError",
    "TransitionResult",
]
