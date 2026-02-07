"""
Domain entities for bookings module.

These are pure data classes representing the core booking domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from core.datetime_utils import utc_now
from modules.bookings.domain.status import (
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)


@dataclass
class BookingEntity:
    """
    Core booking domain entity.

    Represents a tutoring session booking with its four-field status system.
    """

    id: int | None
    student_id: int
    tutor_id: int
    tutor_profile_id: int

    # Session timing
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"

    # Status fields (4-field system)
    session_state: SessionState = SessionState.REQUESTED
    session_outcome: SessionOutcome | None = None
    payment_state: PaymentState = PaymentState.PENDING
    dispute_state: DisputeState = DisputeState.NONE

    # Pricing
    amount_cents: int = 0
    currency: str = "USD"
    platform_fee_cents: int = 0

    # References
    subject_id: int | None = None
    subject_name: str | None = None
    package_id: int | None = None
    pricing_option_id: int | None = None

    # Meeting
    meeting_url: str | None = None
    meeting_id: str | None = None
    meeting_provider: str | None = None

    # Payment references
    stripe_session_id: str | None = None
    payment_intent_id: str | None = None

    # Notes
    student_notes: str | None = None
    tutor_notes: str | None = None
    cancellation_reason: str | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None

    # Version for optimistic locking
    version: int = 1

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def amount_decimal(self) -> Decimal:
        """Get amount as decimal."""
        return Decimal(self.amount_cents) / 100

    @property
    def is_confirmed(self) -> bool:
        """Check if booking is confirmed (scheduled)."""
        return self.session_state == SessionState.SCHEDULED

    @property
    def is_completed(self) -> bool:
        """Check if session completed successfully."""
        return (
            self.session_state == SessionState.ENDED
            and self.session_outcome == SessionOutcome.COMPLETED
        )

    @property
    def is_cancelled(self) -> bool:
        """Check if booking is cancelled."""
        return self.session_state == SessionState.CANCELLED

    @property
    def is_paid(self) -> bool:
        """Check if payment was captured."""
        return self.payment_state == PaymentState.CAPTURED

    @property
    def can_start(self) -> bool:
        """Check if session can start (scheduled and time is right)."""
        if self.session_state != SessionState.SCHEDULED:
            return False
        now = datetime.now(self.start_time.tzinfo)
        return now >= self.start_time

    @property
    def has_dispute(self) -> bool:
        """Check if there's an active dispute."""
        return self.dispute_state == DisputeState.OPEN


@dataclass
class BookingParticipant:
    """Information about a booking participant (student or tutor)."""

    user_id: int
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None = None
    timezone: str = "UTC"

    @property
    def full_name(self) -> str:
        """Get participant's full name."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class BookingDetails:
    """
    Full booking details including participant information.

    Used for responses that need complete booking information.
    """

    booking: BookingEntity
    student: BookingParticipant
    tutor: BookingParticipant
    subject_name: str | None = None

    @property
    def display_title(self) -> str:
        """Generate display title for the booking."""
        subject = self.subject_name or "Tutoring Session"
        return f"{subject} with {self.tutor.full_name}"


@dataclass
class BookingStatusChange:
    """Record of a booking status change."""

    booking_id: int
    from_state: SessionState
    to_state: SessionState
    changed_by_user_id: int | None
    reason: str | None = None
    timestamp: datetime = field(default_factory=utc_now)
