"""Pydantic schemas for request/response validation."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.constants import is_valid_language_code, is_valid_proficiency_level
from core.sanitization import sanitize_url, validate_phone_number, validate_video_url

# ============================================================================
# Authentication Schemas
# ============================================================================


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = Field(default="student")
    timezone: Optional[str] = Field(default="UTC")
    currency: Optional[str] = Field(default="USD")

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password complexity requirements."""
        if len(v) < 8 or len(v) > 128:
            raise ValueError("Password must be 8-128 characters")

        # Check for uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in v)

        if not has_upper:
            raise ValueError("Password must contain at least one uppercase letter")
        if not has_lower:
            raise ValueError("Password must contain at least one lowercase letter")
        if not has_digit:
            raise ValueError("Password must contain at least one number")
        if not has_special:
            raise ValueError("Password must contain at least one special character (!@#$%^&* etc.)")

        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> str:
        if not v:
            return "student"
        if v not in ["student", "tutor", "admin"]:
            raise ValueError("Role must be student, tutor, or admin")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> str:
        if not v:
            return "UTC"
        # Basic validation - could be enhanced with pytz
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> str:
        if not v:
            return "USD"
        return v.upper()


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    avatar_url: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"

    model_config = {"from_attributes": True}

    @field_validator("avatar_url", mode="before")
    @classmethod
    def ensure_avatar_url_is_string(cls, value: Optional[Any]) -> Optional[str]:
        """Normalize avatar URL inputs (e.g., Pydantic Url) into plain strings."""
        if value is None:
            return None
        return str(value)


# ============================================================================
# Profile Schemas
# ============================================================================


class UserProfileUpdate(BaseModel):
    """Update user profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (E.164)."""
        if not v:
            return v
        if not validate_phone_number(v):
            raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
        return v


class UserPreferencesUpdate(BaseModel):
    """Update user preferences (timezone)."""

    timezone: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    timezone: str

    model_config = {"from_attributes": True}


# ============================================================================
# Subject Schemas
# ============================================================================


class SubjectResponse(BaseModel):
    """Subject response."""

    id: int
    name: str
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


# ============================================================================
# Tutor Schemas
# ============================================================================


class TutorSubjectInput(BaseModel):
    """Tutor subject input."""

    subject_id: int
    proficiency_level: str = "b2"  # Updated default to CEFR standard
    years_experience: Optional[int] = None

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency(cls, v: str) -> str:
        """Validate proficiency level against CEFR framework."""
        v_lower = v.lower().strip()
        if not is_valid_proficiency_level(v_lower):
            raise ValueError(
                "Proficiency must be one of: a1, a2, b1, b2, c1, c2, native (CEFR framework)"
            )
        return v_lower


class TutorSubjectResponse(BaseModel):
    """Tutor subject response."""

    id: int
    subject_id: int
    subject_name: str
    proficiency_level: str
    years_experience: Optional[int]

    model_config = {"from_attributes": True}


class TutorAvailabilityInput(BaseModel):
    """Tutor availability input."""

    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    is_recurring: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: time, info) -> time:
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class TutorAvailabilityResponse(BaseModel):
    """Tutor availability response."""

    id: int
    day_of_week: int
    start_time: time
    end_time: time
    is_recurring: bool

    model_config = {"from_attributes": True}


class TutorAvailabilityBulkUpdate(BaseModel):
    """Bulk update for tutor availability."""

    availability: List[TutorAvailabilityInput] = Field(default_factory=list)
    timezone: Optional[str] = Field(default="UTC", max_length=64)
    version: int = Field(
        ..., ge=1, description="Current version for optimistic locking"
    )


# Alias for creating availability
TutorAvailabilityCreate = TutorAvailabilityInput


class AvailableSlot(BaseModel):
    """Available time slot for booking."""

    start_time: str  # ISO format datetime
    end_time: str  # ISO format datetime
    duration_minutes: int


class TutorCertificationInput(BaseModel):
    """Tutor certification input."""

    name: str = Field(..., min_length=2, max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=100)
    credential_url: Optional[str] = Field(None, max_length=500)
    document_url: Optional[str] = None

    @field_validator("expiration_date")
    @classmethod
    def validate_dates(cls, v: Optional[date], info) -> Optional[date]:
        issue_date = info.data.get("issue_date")
        if v and issue_date and v < issue_date:
            raise ValueError("expiration_date cannot be before issue_date")
        return v

    @field_validator("credential_url")
    @classmethod
    def validate_credential_url(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize credential URL to prevent XSS."""
        if not v:
            return v
        sanitized = sanitize_url(v)
        if not sanitized:
            raise ValueError("Invalid or potentially malicious URL")
        return sanitized


class TutorCertificationResponse(TutorCertificationInput):
    """Tutor certification response."""

    id: int
    document_url: Optional[str] = None

    model_config = {"from_attributes": True}


class TutorEducationInput(BaseModel):
    """Tutor education input."""

    institution: str = Field(..., min_length=2, max_length=255)
    degree: Optional[str] = Field(None, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    end_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 10)
    description: Optional[str] = None
    document_url: Optional[str] = None

    @field_validator("end_year")
    @classmethod
    def validate_years(cls, v: Optional[int], info) -> Optional[int]:
        start_year = info.data.get("start_year")
        if v and start_year and v < start_year:
            raise ValueError("end_year cannot be before start_year")
        return v


class TutorEducationResponse(TutorEducationInput):
    """Tutor education response."""

    id: int
    document_url: Optional[str] = None

    model_config = {"from_attributes": True}


class TutorPricingOptionInput(BaseModel):
    """Tutor pricing option input."""

    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0, le=600)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)


class TutorPricingOptionResponse(TutorPricingOptionInput):
    """Tutor pricing option response."""

    id: int

    model_config = {"from_attributes": True}


class TutorAboutUpdate(BaseModel):
    """Tutor about section."""

    title: str = Field(..., min_length=5, max_length=200)
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    experience_years: int = Field(default=0, ge=0)
    languages: Optional[List[str]] = Field(default=None)

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate language codes against ISO 639-1 standard."""
        if not v:
            return None
        # Filter out empty strings
        filtered = [lang.strip().lower() for lang in v if lang and lang.strip()]
        if not filtered:
            return None
        for lang in filtered:
            if not is_valid_language_code(lang):
                raise ValueError(
                    f"Invalid language code: {lang}. Must be ISO 639-1 code (e.g., 'en', 'es', 'fr')"
                )
        return filtered


class TutorDescriptionUpdate(BaseModel):
    """Tutor long description update."""

    description: str = Field(
        ..., min_length=400, max_length=5000
    )  # Updated per struct.txt requirements


class TutorVideoUpdate(BaseModel):
    """Tutor intro video update."""

    video_url: str = Field(..., max_length=500)

    @field_validator("video_url")
    @classmethod
    def validate_video_url_field(cls, v: str) -> str:
        """Validate video URL is from allowed platforms."""
        if not validate_video_url(v):
            raise ValueError(
                "Video URL must be from YouTube, Vimeo, Loom, Wistia, or Vidyard"
            )
        # Also sanitize the URL
        sanitized = sanitize_url(v)
        if not sanitized:
            raise ValueError("Invalid or potentially malicious URL")
        return sanitized


class TutorPricingUpdate(BaseModel):
    """Tutor pricing update."""

    hourly_rate: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    pricing_options: List[TutorPricingOptionInput] = Field(default_factory=list)
    version: int = Field(
        ..., ge=1, description="Current version for optimistic locking"
    )


class TutorProfileCreate(BaseModel):
    """Create/update tutor profile (legacy)."""

    title: str = Field(..., min_length=5, max_length=200)
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    experience_years: int = Field(default=0, ge=0)
    education: Optional[str] = None
    languages: Optional[List[str]] = None
    video_url: Optional[str] = None
    subjects: List[TutorSubjectInput] = []


class TutorProfileResponse(BaseModel):
    """Tutor profile response."""

    id: int
    user_id: int
    title: str
    headline: Optional[str]
    bio: Optional[str]
    description: Optional[str]
    hourly_rate: Decimal
    experience_years: int
    education: Optional[str]
    languages: Optional[List[str]]
    video_url: Optional[str]
    is_approved: bool
    profile_status: str
    rejection_reason: Optional[str]
    average_rating: Decimal
    total_reviews: int
    total_sessions: int
    created_at: datetime
    timezone: Optional[str]
    version: int
    subjects: List[TutorSubjectResponse] = []
    availabilities: List[TutorAvailabilityResponse] = []
    certifications: List[TutorCertificationResponse] = []
    educations: List[TutorEducationResponse] = []
    pricing_options: List[TutorPricingOptionResponse] = []

    model_config = {"from_attributes": True}


class TutorPublicProfile(BaseModel):
    """Public tutor profile (for listings)."""

    id: int
    title: str
    headline: Optional[str]
    bio: Optional[str]
    hourly_rate: Decimal
    experience_years: int
    average_rating: Decimal
    total_reviews: int
    total_sessions: int
    subjects: List[str] = []

    model_config = {"from_attributes": True}


# ============================================================================
# Student Schemas
# ============================================================================


class StudentProfileUpdate(BaseModel):
    """Update student profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    grade_level: Optional[str] = None
    school_name: Optional[str] = None
    learning_goals: Optional[str] = None
    interests: Optional[str] = None


class StudentProfileResponse(BaseModel):
    """Student profile response."""

    id: int
    user_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    grade_level: Optional[str]
    school_name: Optional[str]
    learning_goals: Optional[str]
    interests: Optional[str]
    total_sessions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Booking Schemas
# ============================================================================


class BookingCreate(BaseModel):
    """Create booking request."""

    tutor_profile_id: int
    subject_id: int
    start_time: datetime
    end_time: datetime
    topic: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def validate_booking_time(cls, v: datetime, info) -> datetime:
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class BookingStatusUpdate(BaseModel):
    """Update booking status with decision tracking."""

    status: str
    join_url: Optional[str] = None  # Meeting URL for virtual sessions
    cancellation_reason: Optional[str] = Field(None, max_length=500)
    is_instant_booking: Optional[bool] = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ["confirmed", "cancelled", "completed", "no_show"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


class BookingResponse(BaseModel):
    """Booking response with immutable snapshot context and decision tracking."""

    id: int
    tutor_profile_id: int
    student_id: int
    subject_id: Optional[int]
    start_time: datetime
    end_time: datetime
    status: str
    topic: Optional[str]
    notes: Optional[str]
    join_url: Optional[str]  # Meeting URL for virtual sessions
    hourly_rate: Decimal
    total_amount: Decimal
    pricing_type: Optional[str] = "hourly"
    pricing_option_id: Optional[int] = None
    # Immutable snapshot fields (what was agreed at booking time)
    tutor_name: Optional[str] = None
    tutor_title: Optional[str] = None
    student_name: Optional[str] = None
    subject_name: Optional[str] = None
    pricing_snapshot: Optional[str] = None  # JSON string
    agreement_terms: Optional[str] = None
    # Decision tracking fields
    is_instant_booking: Optional[bool] = False
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    is_rebooked: Optional[bool] = False
    original_booking_id: Optional[int] = None
    # Enhanced tutor view fields
    student_avatar_url: Optional[str] = None
    student_language_level: Optional[str] = None
    tutor_earnings: Optional[Decimal] = None
    lesson_type: Optional[str] = "regular"
    student_timezone: Optional[str] = None
    # Enhanced student view fields
    tutor_photo_url: Optional[str] = None
    tutor_rating: Optional[float] = None
    tutor_language: Optional[str] = None
    tutor_total_lessons: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("pricing_snapshot", mode="before")
    @classmethod
    def serialize_pricing_snapshot(cls, v):
        """Convert dict to JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, dict):
            import json

            return json.dumps(v)
        return v


# ============================================================================
# Review Schemas
# ============================================================================


class ReviewCreate(BaseModel):
    """Create review."""

    booking_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response with immutable booking context."""

    id: int
    booking_id: int
    tutor_profile_id: int
    student_id: int
    rating: int
    comment: Optional[str]
    is_public: bool
    booking_snapshot: Optional[str] = None  # JSON string
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Message Schemas
# ============================================================================


class MessageCreate(BaseModel):
    """Create message."""

    recipient_id: int
    booking_id: Optional[int] = None
    message: str = Field(..., min_length=1, max_length=2000)


class MessageAttachmentResponse(BaseModel):
    """Message attachment metadata."""
    
    id: int
    message_id: int
    file_key: str
    original_filename: str
    file_size: int
    mime_type: str
    file_category: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[int] = None
    is_scanned: bool = False
    scan_result: Optional[str] = None
    created_at: datetime
    download_url: Optional[str] = None  # Presigned URL (computed field)
    
    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Message response with full metadata."""

    id: int
    sender_id: int
    recipient_id: int
    booking_id: Optional[int] = None
    message: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    attachments: List["MessageAttachmentResponse"] = []  # File attachments

    model_config = {"from_attributes": True}


# ============================================================================
# Notification Schemas
# ============================================================================


class NotificationResponse(BaseModel):
    """Notification response."""

    id: int
    type: str
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Admin Schemas
# ============================================================================


class UserUpdate(BaseModel):
    """Admin user update."""

    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["student", "tutor", "admin"]:
            raise ValueError("Role must be student, tutor, or admin")
        return v


class ReportCreate(BaseModel):
    """Create report."""

    reported_user_id: int
    booking_id: Optional[int] = None
    reason: str
    description: str = Field(..., min_length=10)


class ReportResponse(BaseModel):
    """Report response."""

    id: int
    reporter_id: int
    reported_user_id: int
    booking_id: Optional[int]
    reason: str
    description: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TutorRejectionRequest(BaseModel):
    """Tutor profile rejection request."""

    rejection_reason: str = Field(..., min_length=10, max_length=500)


# ============================================================================
# Generic Response
# ============================================================================


class MessageOnly(BaseModel):
    """Generic message response."""

    message: str
