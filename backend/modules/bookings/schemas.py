"""Enhanced booking schemas per booking_detail.md spec."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Enums as Literals
# ============================================================================

# New four-field status system
SessionState = Literal[
    "REQUESTED",  # Waiting for tutor response
    "SCHEDULED",  # Confirmed, session upcoming
    "ACTIVE",  # Session happening now
    "ENDED",  # Session lifecycle complete
    "EXPIRED",  # Request timed out (24h)
    "CANCELLED",  # Explicitly cancelled
]

SessionOutcome = Literal[
    "COMPLETED",  # Session happened successfully
    "NOT_HELD",  # Session didn't happen (cancelled/expired)
    "NO_SHOW_STUDENT",  # Student didn't attend
    "NO_SHOW_TUTOR",  # Tutor didn't attend
]

PaymentState = Literal[
    "PENDING",  # Awaiting authorization
    "AUTHORIZED",  # Funds held
    "CAPTURED",  # Tutor earned payment
    "VOIDED",  # Authorization released
    "REFUNDED",  # Full refund issued
    "PARTIALLY_REFUNDED",  # Partial refund issued
]

DisputeState = Literal[
    "NONE",  # No dispute
    "OPEN",  # Under review
    "RESOLVED_UPHELD",  # Original decision stands
    "RESOLVED_REFUNDED",  # Refund granted
]

CancelledByRole = Literal["STUDENT", "TUTOR", "ADMIN", "SYSTEM"]

# Legacy status (for backward compatibility)
BookingStatus = Literal[
    "PENDING",
    "CONFIRMED",
    "CANCELLED_BY_STUDENT",
    "CANCELLED_BY_TUTOR",
    "NO_SHOW_STUDENT",
    "NO_SHOW_TUTOR",
    "COMPLETED",
    "REFUNDED",
]

LessonType = Literal["TRIAL", "REGULAR", "PACKAGE"]

CreatedBy = Literal["STUDENT", "TUTOR", "ADMIN"]


# ============================================================================
# Nested schemas for booking response
# ============================================================================


class TutorInfoDTO(BaseModel):
    """Tutor information embedded in booking response."""

    id: int
    name: str
    avatar_url: str | None = None
    rating_avg: Decimal = Field(default=Decimal("0.00"))
    title: str | None = None


class StudentInfoDTO(BaseModel):
    """Student information embedded in booking response."""

    id: int
    name: str
    avatar_url: str | None = None
    level: str | None = None


# ============================================================================
# Request schemas
# ============================================================================


class BookingCreateRequest(BaseModel):
    """Create booking request (student initiated)."""

    tutor_profile_id: int
    start_at: datetime
    duration_minutes: int = Field(..., ge=15, le=180)
    lesson_type: LessonType = "REGULAR"
    subject_id: int | None = None
    notes_student: str | None = Field(None, max_length=2000)
    use_package_id: int | None = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, duration_value: int) -> int:
        """Ensure duration matches allowed values."""
        allowed = [25, 30, 45, 50, 60, 90, 120]
        if duration_value not in allowed:
            raise ValueError(f"Duration must be one of: {allowed}")
        return duration_value


class BookingCancelRequest(BaseModel):
    """Cancel booking request."""

    reason: str | None = Field(None, max_length=500)


class BookingRescheduleRequest(BaseModel):
    """Reschedule booking request."""

    new_start_at: datetime


class BookingConfirmRequest(BaseModel):
    """Tutor confirms booking."""

    notes_tutor: str | None = Field(None, max_length=2000)


class BookingDeclineRequest(BaseModel):
    """Tutor declines booking."""

    reason: str | None = Field(None, max_length=500)


class MarkNoShowRequest(BaseModel):
    """Mark no-show (tutor or student)."""

    notes: str | None = Field(None, max_length=500)


# ============================================================================
# Response schemas
# ============================================================================


class BookingDTO(BaseModel):
    """Complete booking data transfer object per spec."""

    id: int
    lesson_type: LessonType

    # New four-field status system
    session_state: str
    session_outcome: str | None = None
    payment_state: str
    dispute_state: str

    # Legacy status field (computed for backward compatibility)
    status: str  # Computed from session_state + session_outcome

    # Cancellation info
    cancelled_by_role: str | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None

    start_at: datetime  # ISO UTC
    end_at: datetime  # ISO UTC
    student_tz: str
    tutor_tz: str
    rate_cents: int
    currency: str
    platform_fee_pct: Decimal
    platform_fee_cents: int
    tutor_earnings_cents: int
    join_url: str | None = None
    notes_student: str | None = None
    notes_tutor: str | None = None
    tutor: TutorInfoDTO
    student: StudentInfoDTO
    subject_name: str | None = None
    topic: str | None = None
    created_at: datetime
    updated_at: datetime

    # Dispute information (only included if dispute exists)
    dispute_reason: str | None = None
    disputed_at: datetime | None = None

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Paginated list of bookings."""

    bookings: list[BookingDTO]
    total: int
    page: int
    page_size: int


# ============================================================================
# Availability schemas
# ============================================================================


class AvailabilityWindowCreate(BaseModel):
    """Single recurring availability window."""

    weekday: int = Field(..., ge=0, le=6)
    start_minute: int = Field(..., ge=0, le=1439)
    end_minute: int = Field(..., ge=0, le=1439)

    @field_validator("end_minute")
    @classmethod
    def validate_time_order(cls, end_minute_value: int, info) -> int:
        if "start_minute" in info.data and end_minute_value <= info.data["start_minute"]:
            raise ValueError("end_minute must be after start_minute")
        return end_minute_value


class AvailabilityUpdateRequest(BaseModel):
    """Update tutor availability (recurring windows)."""

    windows: list[AvailabilityWindowCreate]
    effective_from: datetime
    effective_to: datetime | None = None


class BlackoutCreateRequest(BaseModel):
    """Create blackout period (vacation, etc.)."""

    start_at: datetime
    end_at: datetime
    reason: str | None = Field(None, max_length=500)

    @field_validator("end_at")
    @classmethod
    def validate_time_order(cls, end_at_value: datetime, info) -> datetime:
        if "start_at" in info.data and end_at_value <= info.data["start_at"]:
            raise ValueError("end_at must be after start_at")
        return end_at_value


class AvailabilitySlotDTO(BaseModel):
    """Single bookable slot."""

    start_at: datetime  # UTC
    end_at: datetime  # UTC
    is_bookable: bool


class AvailabilityQueryResponse(BaseModel):
    """Available slots for a tutor."""

    tutor_id: int
    slots: list[AvailabilitySlotDTO]


# ============================================================================
# Payment schemas
# ============================================================================


class PaymentIntentRequest(BaseModel):
    """Create payment intent before booking."""

    booking_id: int | None = None
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""

    id: int
    client_secret: str
    amount_cents: int
    currency: str
    status: str


# ============================================================================
# Dispute schemas
# ============================================================================


class DisputeCreateRequest(BaseModel):
    """Open a dispute on a booking."""

    reason: str = Field(..., min_length=10, max_length=2000)


class DisputeResolveRequest(BaseModel):
    """Admin resolves a dispute."""

    resolution: Literal["RESOLVED_UPHELD", "RESOLVED_REFUNDED"]
    notes: str | None = Field(None, max_length=2000)
    refund_amount_cents: int | None = Field(None, ge=0)


class DisputeDTO(BaseModel):
    """Dispute information for a booking."""

    booking_id: int
    dispute_state: str
    dispute_reason: str | None = None
    disputed_at: datetime | None = None
    disputed_by: int | None = None
    resolved_at: datetime | None = None
    resolved_by: int | None = None
    resolution_notes: str | None = None
