"""Enhanced booking schemas per booking_detail.md spec."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Enums as Literals
# ============================================================================

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
    avatar_url: Optional[str] = None
    rating_avg: Decimal = Field(default=Decimal("0.00"))
    title: Optional[str] = None


class StudentInfoDTO(BaseModel):
    """Student information embedded in booking response."""

    id: int
    name: str
    avatar_url: Optional[str] = None
    level: Optional[str] = None


# ============================================================================
# Request schemas
# ============================================================================


class BookingCreateRequest(BaseModel):
    """Create booking request (student initiated)."""

    tutor_id: int
    start_at: datetime
    duration_minutes: int = Field(..., ge=15, le=180)
    lesson_type: LessonType = "REGULAR"
    subject_id: Optional[int] = None
    notes_student: Optional[str] = Field(None, max_length=2000)
    use_package_id: Optional[int] = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Ensure duration matches allowed values."""
        allowed = [30, 45, 60, 90, 120]
        if v not in allowed:
            raise ValueError(f"Duration must be one of: {allowed}")
        return v


class BookingCancelRequest(BaseModel):
    """Cancel booking request."""

    reason: Optional[str] = Field(None, max_length=500)


class BookingRescheduleRequest(BaseModel):
    """Reschedule booking request."""

    new_start_at: datetime


class BookingConfirmRequest(BaseModel):
    """Tutor confirms booking."""

    notes_tutor: Optional[str] = Field(None, max_length=2000)


class BookingDeclineRequest(BaseModel):
    """Tutor declines booking."""

    reason: Optional[str] = Field(None, max_length=500)


class MarkNoShowRequest(BaseModel):
    """Mark no-show (tutor or student)."""

    notes: Optional[str] = Field(None, max_length=500)


# ============================================================================
# Response schemas
# ============================================================================


class BookingDTO(BaseModel):
    """Complete booking data transfer object per spec."""

    id: int
    lesson_type: LessonType
    status: str  # Using str for backward compat with old statuses
    start_at: datetime  # ISO UTC
    end_at: datetime  # ISO UTC
    student_tz: str
    tutor_tz: str
    rate_cents: int
    currency: str
    platform_fee_pct: Decimal
    platform_fee_cents: int
    tutor_earnings_cents: int
    join_url: Optional[str] = None
    notes_student: Optional[str] = None
    notes_tutor: Optional[str] = None
    tutor: TutorInfoDTO
    student: StudentInfoDTO
    subject_name: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime
    updated_at: datetime

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
    def validate_time_order(cls, v: int, info) -> int:
        if "start_minute" in info.data and v <= info.data["start_minute"]:
            raise ValueError("end_minute must be after start_minute")
        return v


class AvailabilityUpdateRequest(BaseModel):
    """Update tutor availability (recurring windows)."""

    windows: list[AvailabilityWindowCreate]
    effective_from: datetime
    effective_to: Optional[datetime] = None


class BlackoutCreateRequest(BaseModel):
    """Create blackout period (vacation, etc.)."""

    start_at: datetime
    end_at: datetime
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator("end_at")
    @classmethod
    def validate_time_order(cls, v: datetime, info) -> datetime:
        if "start_at" in info.data and v <= info.data["start_at"]:
            raise ValueError("end_at must be after start_at")
        return v


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

    booking_id: Optional[int] = None
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""

    id: int
    client_secret: str
    amount_cents: int
    currency: str
    status: str
