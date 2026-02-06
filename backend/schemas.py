"""Pydantic schemas for request/response validation."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.constants import is_valid_language_code, is_valid_proficiency_level
from core.sanitization import sanitize_html, sanitize_url, validate_phone_number, validate_video_url
from core.timezone import is_valid_timezone
from core.utils import StringUtils

# ============================================================================
# Authentication Schemas
# ============================================================================


class UserCreate(BaseModel):
    """Schema for user registration.

    Both first_name and last_name are required for all registered users.
    Names are normalized: trimmed, whitespace-only values rejected.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name (required)")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name (required)")
    role: str | None = Field(default="student")
    timezone: str | None = Field(default="UTC")
    currency: str | None = Field(default="USD")

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, email_value: str) -> str:
        return StringUtils.normalize_email(email_value)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str, info) -> str:
        """Validate and normalize name fields.

        - Sanitizes HTML to prevent stored XSS
        - Trims leading/trailing whitespace
        - Rejects whitespace-only strings
        - Enforces min 1 char after trim, max 100 chars
        """
        if not value:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} is required")

        # Sanitize HTML to prevent stored XSS
        normalized = sanitize_html(value) or ""

        # Normalize: trim whitespace
        normalized = normalized.strip()

        # Reject whitespace-only strings
        if not normalized:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} cannot be empty or whitespace only")

        # Enforce length constraints after normalization
        if len(normalized) > 100:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} must not exceed 100 characters")

        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password_value: str) -> str:
        """Validate password complexity requirements."""
        if len(password_value) < 8 or len(password_value) > 128:
            raise ValueError("Password must be 8-128 characters")

        # Check for uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password_value)
        has_lower = any(c.islower() for c in password_value)
        has_digit = any(c.isdigit() for c in password_value)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password_value)

        if not has_upper:
            raise ValueError("Password must contain at least one uppercase letter")
        if not has_lower:
            raise ValueError("Password must contain at least one lowercase letter")
        if not has_digit:
            raise ValueError("Password must contain at least one number")
        if not has_special:
            raise ValueError("Password must contain at least one special character (!@#$%^&* etc.)")

        return password_value

    @field_validator("role")
    @classmethod
    def validate_role(cls, role_value: str | None) -> str:
        if not role_value:
            return "student"
        if role_value not in ["student", "tutor", "admin"]:
            raise ValueError("Role must be student, tutor, or admin")
        return role_value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone_value: str | None) -> str:
        if not timezone_value:
            return "UTC"
        if not is_valid_timezone(timezone_value):
            raise ValueError(f"Invalid IANA timezone: {timezone_value}")
        return timezone_value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, currency_value: str | None) -> str:
        if not currency_value:
            return "USD"
        return currency_value.upper()


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response (for refresh endpoint)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None  # Access token expiry in seconds (optional for backwards compat)


class TokenWithRefresh(BaseModel):
    """JWT token response with refresh token.

    Used for login response to provide both access and refresh tokens.
    The refresh token should be stored securely (httpOnly cookie recommended).
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiry in seconds


class TokenRefreshRequest(BaseModel):
    """Request to refresh an access token using a refresh token."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response schema with computed full_name."""

    id: int
    email: str
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    full_name: str | None = None  # Computed field: "{first_name} {last_name}"
    profile_incomplete: bool = False  # True if user needs to complete profile (missing names)
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    avatar_url: str | None = None
    currency: str = "USD"
    timezone: str = "UTC"
    preferred_language: str | None = None
    locale: str | None = None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        """Compute full_name and profile_incomplete after initialization."""
        # Compute full_name from first_name and last_name
        if self.first_name or self.last_name:
            self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        else:
            self.full_name = None
        # Set profile_incomplete if names are missing
        self.profile_incomplete = not (self.first_name and self.last_name)

    @field_validator("avatar_url", mode="before")
    @classmethod
    def ensure_avatar_url_is_string(cls, value: Any | None) -> str | None:
        """Normalize avatar URL inputs (e.g., Pydantic Url) into plain strings."""
        if value is None:
            return None
        return str(value)


# ============================================================================
# Profile Schemas
# ============================================================================


class UserProfileUpdate(BaseModel):
    """Update user profile."""

    phone: str | None = None
    bio: str | None = None
    timezone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, phone_value: str | None) -> str | None:
        """Validate phone number format (E.164)."""
        if not phone_value:
            return phone_value
        if not validate_phone_number(phone_value):
            raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
        return phone_value


class UserPreferencesUpdate(BaseModel):
    """Update user preferences (timezone)."""

    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone_value: str | None) -> str | None:
        if not timezone_value:
            return timezone_value
        if not is_valid_timezone(timezone_value):
            raise ValueError(f"Invalid IANA timezone: {timezone_value}")
        return timezone_value


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: int
    phone: str | None
    bio: str | None
    timezone: str

    model_config = {"from_attributes": True}


# ============================================================================
# Subject Schemas
# ============================================================================


class SubjectResponse(BaseModel):
    """Subject response."""

    id: int
    name: str
    description: str | None
    category: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PublicSubjectItem(BaseModel):
    """Minimal subject info for public tutor listings."""

    id: int
    name: str

    model_config = {"from_attributes": True}


# ============================================================================
# Tutor Schemas
# ============================================================================


class TutorSubjectInput(BaseModel):
    """Tutor subject input."""

    subject_id: int
    proficiency_level: str = "b2"  # Updated default to CEFR standard
    years_experience: int | None = None

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency(cls, proficiency_value: str) -> str:
        """Validate proficiency level against CEFR framework."""
        proficiency_lower = proficiency_value.lower().strip()
        if not is_valid_proficiency_level(proficiency_lower):
            raise ValueError("Proficiency must be one of: a1, a2, b1, b2, c1, c2, native (CEFR framework)")
        return proficiency_lower


class TutorSubjectResponse(BaseModel):
    """Tutor subject response."""

    id: int
    subject_id: int
    subject_name: str
    proficiency_level: str
    years_experience: int | None

    model_config = {"from_attributes": True}


class TutorAvailabilityInput(BaseModel):
    """Tutor availability input."""

    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    is_recurring: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, end_time_value: time, info) -> time:
        if "start_time" in info.data and end_time_value <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return end_time_value


class TutorAvailabilityResponse(BaseModel):
    """Tutor availability response."""

    id: int
    day_of_week: int
    start_time: time
    end_time: time
    is_recurring: bool
    timezone: str | None = "UTC"  # IANA timezone in which times are expressed

    model_config = {"from_attributes": True}


class TutorAvailabilityBulkUpdate(BaseModel):
    """Bulk update for tutor availability."""

    availability: list[TutorAvailabilityInput] = Field(default_factory=list)
    timezone: str | None = Field(default="UTC", max_length=64)
    version: int = Field(..., ge=1, description="Current version for optimistic locking")


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
    issuing_organization: str | None = Field(None, max_length=255)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_id: str | None = Field(None, max_length=100)
    credential_url: str | None = Field(None, max_length=500)
    document_url: str | None = None

    @field_validator("expiration_date")
    @classmethod
    def validate_dates(cls, expiration_value: date | None, info) -> date | None:
        issue_date = info.data.get("issue_date")
        if expiration_value and issue_date and expiration_value < issue_date:
            raise ValueError("expiration_date cannot be before issue_date")
        return expiration_value

    @field_validator("credential_url")
    @classmethod
    def validate_credential_url(cls, url_value: str | None) -> str | None:
        """Sanitize credential URL to prevent XSS."""
        if not url_value:
            return url_value
        sanitized = sanitize_url(url_value)
        if not sanitized:
            raise ValueError("Invalid or potentially malicious URL")
        return sanitized


class TutorCertificationResponse(TutorCertificationInput):
    """Tutor certification response."""

    id: int
    document_url: str | None = None

    model_config = {"from_attributes": True}


class TutorEducationInput(BaseModel):
    """Tutor education input."""

    institution: str = Field(..., min_length=2, max_length=255)
    degree: str | None = Field(None, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_year: int | None = Field(None, ge=1900, le=datetime.now().year)
    end_year: int | None = Field(None, ge=1900, le=datetime.now().year + 10)
    description: str | None = None
    document_url: str | None = None

    @field_validator("end_year")
    @classmethod
    def validate_years(cls, end_year_value: int | None, info) -> int | None:
        start_year = info.data.get("start_year")
        if end_year_value and start_year and end_year_value < start_year:
            raise ValueError("end_year cannot be before start_year")
        return end_year_value


class TutorEducationResponse(TutorEducationInput):
    """Tutor education response."""

    id: int
    document_url: str | None = None

    model_config = {"from_attributes": True}


class TutorPricingOptionInput(BaseModel):
    """Tutor pricing option input."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(..., gt=0, le=600)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    validity_days: int | None = Field(None, gt=0, description="Number of days package is valid after purchase (NULL = no expiration)")


class TutorPricingOptionResponse(TutorPricingOptionInput):
    """Tutor pricing option response."""

    id: int

    model_config = {"from_attributes": True}


class TutorAboutUpdate(BaseModel):
    """Tutor about section."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    title: str = Field(..., min_length=5, max_length=200)
    headline: str | None = Field(None, max_length=255)
    bio: str | None = None
    experience_years: int = Field(default=0, ge=0)
    languages: list[str] | None = Field(default=None)

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, languages_value: list[str] | None) -> list[str] | None:
        """Validate language codes against ISO 639-1 standard."""
        if not languages_value:
            return None
        # Filter out empty strings
        filtered = [lang.strip().lower() for lang in languages_value if lang and lang.strip()]
        if not filtered:
            return None
        for lang in filtered:
            if not is_valid_language_code(lang):
                raise ValueError(f"Invalid language code: {lang}. Must be ISO 639-1 code (e.g., 'en', 'es', 'fr')")
        return filtered


class TutorDescriptionUpdate(BaseModel):
    """Tutor long description update."""

    description: str = Field(..., min_length=400, max_length=5000)  # Updated per struct.txt requirements


class TutorVideoUpdate(BaseModel):
    """Tutor intro video update."""

    video_url: str = Field(..., max_length=500)

    @field_validator("video_url")
    @classmethod
    def validate_video_url_field(cls, url_value: str) -> str:
        """Validate video URL is from allowed platforms."""
        if not validate_video_url(url_value):
            raise ValueError("Video URL must be from YouTube, Vimeo, Loom, Wistia, or Vidyard")
        # Also sanitize the URL
        sanitized = sanitize_url(url_value)
        if not sanitized:
            raise ValueError("Invalid or potentially malicious URL")
        return sanitized


class TutorPricingUpdate(BaseModel):
    """Tutor pricing update."""

    hourly_rate: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    pricing_options: list[TutorPricingOptionInput] = Field(default_factory=list)
    version: int = Field(..., ge=1, description="Current version for optimistic locking")


class TutorProfileCreate(BaseModel):
    """Create/update tutor profile (legacy)."""

    title: str = Field(..., min_length=5, max_length=200)
    headline: str | None = Field(None, max_length=255)
    bio: str | None = None
    description: str | None = None
    hourly_rate: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    experience_years: int = Field(default=0, ge=0)
    education: str | None = None
    languages: list[str] | None = None
    video_url: str | None = None
    subjects: list[TutorSubjectInput] = []


class TutorProfileResponse(BaseModel):
    """Tutor profile response."""

    id: int
    user_id: int
    name: str
    title: str
    headline: str | None
    bio: str | None
    description: str | None
    hourly_rate: Decimal
    experience_years: int
    education: str | None
    languages: list[str] | None
    video_url: str | None
    is_approved: bool
    profile_status: str
    rejection_reason: str | None
    approved_at: datetime | None = None
    average_rating: float
    total_reviews: int
    total_sessions: int
    created_at: datetime
    timezone: str | None
    version: int
    profile_photo_url: str | None = None
    subjects: list[TutorSubjectResponse] = []
    availabilities: list[TutorAvailabilityResponse] = []
    certifications: list[TutorCertificationResponse] = []
    educations: list[TutorEducationResponse] = []
    pricing_options: list[TutorPricingOptionResponse] = []

    model_config = {"from_attributes": True}


class TutorPublicProfile(BaseModel):
    """Public tutor profile (for listings).

    Note: first_name and last_name are required for tutors to be listed publicly.
    Tutors without complete names should not appear in search results.
    """

    id: int
    user_id: int
    first_name: str
    last_name: str
    title: str
    headline: str | None
    bio: str | None
    hourly_rate: Decimal
    currency: str = Field(default="USD", description="Currency for hourly_rate")
    experience_years: int
    average_rating: float
    total_reviews: int
    total_sessions: int
    subjects: list[PublicSubjectItem] = []
    education: list[str] = []
    video_url: str | None = None
    profile_photo_url: str | None = None
    recent_review: str | None = None
    next_available_slots: list[str] = []

    model_config = {"from_attributes": True}


# ============================================================================
# Student Schemas
# ============================================================================


class StudentProfileUpdate(BaseModel):
    """Update student profile."""

    phone: str | None = None
    bio: str | None = None
    grade_level: str | None = None
    school_name: str | None = None
    learning_goals: str | None = None
    interests: str | None = None
    preferred_language: str | None = None


class StudentProfileResponse(BaseModel):
    """Student profile response."""

    id: int
    user_id: int
    phone: str | None
    bio: str | None
    grade_level: str | None
    school_name: str | None
    learning_goals: str | None
    interests: str | None
    total_sessions: int
    preferred_language: str | None
    timezone: str
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
    topic: str | None = None
    notes: str | None = None

    @field_validator("end_time")
    @classmethod
    def validate_booking_time(cls, end_time_value: datetime, info) -> datetime:
        if "start_time" in info.data and end_time_value <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return end_time_value


class BookingStatusUpdate(BaseModel):
    """Update booking status with decision tracking."""

    status: str
    join_url: str | None = None  # Meeting URL for virtual sessions
    cancellation_reason: str | None = Field(None, max_length=500)
    is_instant_booking: bool | None = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, status_value: str) -> str:
        allowed = [
            "PENDING",
            "CONFIRMED",
            "CANCELLED_BY_STUDENT",
            "CANCELLED_BY_TUTOR",
            "NO_SHOW_STUDENT",
            "NO_SHOW_TUTOR",
            "COMPLETED",
            "REFUNDED",
        ]
        status_upper = status_value.upper()
        if status_upper not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return status_upper


class BookingResponse(BaseModel):
    """
    Booking response with immutable snapshot context and decision tracking.

    Rate Locking Behavior:
    ----------------------
    The `hourly_rate` and `total_amount` fields represent the rate that was LOCKED
    at the time of booking creation, NOT the tutor's current rate. This is intentional:

    1. Price Certainty: Students are charged the rate they agreed to when booking.
    2. Fair Expectations: Tutors honor the rate that was advertised at booking time.
    3. Pending Bookings: If a tutor changes their rate, pending bookings are NOT affected.

    The `created_at` timestamp indicates when the rate was locked.
    To get the tutor's current rate, query the tutor profile separately.
    """

    id: int
    tutor_profile_id: int
    student_id: int
    subject_id: int | None
    start_time: datetime
    end_time: datetime
    status: str
    topic: str | None
    notes: str | None
    join_url: str | None  # Meeting URL for virtual sessions
    # Pricing fields - IMPORTANT: These are LOCKED rates from booking creation,
    # not the tutor's current rate. Rate changes do NOT affect pending bookings.
    hourly_rate: Decimal
    total_amount: Decimal
    pricing_type: str | None = "hourly"
    pricing_option_id: int | None = None
    # Immutable snapshot fields (what was agreed at booking time)
    tutor_name: str | None = None
    tutor_title: str | None = None
    student_name: str | None = None
    subject_name: str | None = None
    pricing_snapshot: str | None = None  # JSON string
    agreement_terms: str | None = None
    # Decision tracking fields
    is_instant_booking: bool | None = False
    confirmed_at: datetime | None = None
    confirmed_by: int | None = None
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    is_rebooked: bool | None = False
    original_booking_id: int | None = None
    # Enhanced tutor view fields
    student_avatar_url: str | None = None
    student_language_level: str | None = None
    tutor_earnings: Decimal | None = None
    lesson_type: str | None = "regular"
    student_timezone: str | None = None
    # Enhanced student view fields
    tutor_photo_url: str | None = None
    tutor_rating: float | None = None
    tutor_language: str | None = None
    tutor_total_lessons: int | None = None
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
    comment: str | None = None


class ReviewResponse(BaseModel):
    """Review response with immutable booking context."""

    id: int
    booking_id: int
    tutor_profile_id: int
    student_id: int
    rating: int
    comment: str | None
    is_public: bool
    booking_snapshot: str | None = None  # JSON string
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Message Schemas
# ============================================================================


class MessageCreate(BaseModel):
    """Create message."""

    recipient_id: int
    booking_id: int | None = None
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
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    is_scanned: bool = False
    scan_result: str | None = None
    created_at: datetime
    download_url: str | None = None  # Presigned URL (computed field)

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Message response with full metadata."""

    id: int
    sender_id: int
    recipient_id: int
    conversation_id: int | None = None
    booking_id: int | None = None
    message: str
    is_read: bool = False
    read_at: datetime | None = None
    is_edited: bool = False
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by: int | None = None
    created_at: datetime
    updated_at: datetime
    attachments: list["MessageAttachmentResponse"] = []  # File attachments

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
    link: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Admin Schemas
# ============================================================================


class UserUpdate(BaseModel):
    """Admin user update."""

    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, role_value: str | None) -> str | None:
        if role_value and role_value not in ["student", "tutor", "admin", "owner"]:
            raise ValueError("Role must be student, tutor, admin, or owner")
        return role_value


class UserSelfUpdate(BaseModel):
    """User self-update for basic profile information.

    Names cannot be cleared once set - they can only be updated to valid non-empty values.
    """

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    timezone: str | None = None
    currency: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_if_provided(cls, value: str | None, info) -> str | None:
        """Validate and normalize name fields if provided.

        If a name is provided, it must be non-empty after trimming.
        This prevents clearing names via update.
        Sanitizes HTML to prevent stored XSS.
        """
        if value is None:
            return None

        # Sanitize HTML to prevent stored XSS
        normalized = sanitize_html(value) or ""

        # Normalize: trim whitespace
        normalized = normalized.strip()

        # Reject whitespace-only strings (prevents clearing via "   ")
        if not normalized:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} cannot be empty or whitespace only")

        # Enforce length constraints after normalization
        if len(normalized) > 100:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} must not exceed 100 characters")

        return normalized


class ReportCreate(BaseModel):
    """Create report."""

    reported_user_id: int
    booking_id: int | None = None
    reason: str
    description: str = Field(..., min_length=10)


class ReportResponse(BaseModel):
    """Report response."""

    id: int
    reporter_id: int
    reported_user_id: int
    booking_id: int | None
    reason: str
    description: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TutorRejectionRequest(BaseModel):
    """Tutor profile rejection request."""

    rejection_reason: str = Field(..., min_length=10, max_length=500)


# ============================================================================
# Favorite Tutor Schemas
# ============================================================================


class FavoriteTutorResponse(BaseModel):
    """Favorite tutor response."""

    id: int
    student_id: int
    tutor_profile_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Student Notes Schemas
# ============================================================================


class StudentNoteUpdate(BaseModel):
    """Student note update request."""

    notes: str | None = Field(None, max_length=10000, description="Private notes about the student")


class StudentNoteResponse(BaseModel):
    """Student note response."""

    id: int
    tutor_id: int
    student_id: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FavoriteTutorCreate(BaseModel):
    """Create favorite tutor."""

    tutor_profile_id: int = Field(..., gt=0)


# ============================================================================
# Tutor Blackout Schemas
# ============================================================================


class TutorBlackoutCreate(BaseModel):
    """Create blackout period (unavailable time)."""

    start_datetime: datetime
    end_datetime: datetime
    reason: str | None = Field(None, max_length=500)

    @field_validator("end_datetime")
    @classmethod
    def validate_time_range(cls, end_value: datetime, info) -> datetime:
        if "start_datetime" in info.data and end_value <= info.data["start_datetime"]:
            raise ValueError("end_datetime must be after start_datetime")
        return end_value


class TutorBlackoutResponse(BaseModel):
    """Blackout period response."""

    id: int
    tutor_id: int
    start_at: datetime
    end_at: datetime
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConflictingBookingInfo(BaseModel):
    """Information about a booking that conflicts with a blackout period."""

    id: int
    start_time: datetime
    end_time: datetime
    session_state: str
    student_name: str | None
    subject_name: str | None


class TutorBlackoutCreateResponse(BaseModel):
    """Response for blackout creation with potential warnings."""

    blackout: TutorBlackoutResponse
    warning: str | None = None
    conflicting_bookings: list[ConflictingBookingInfo] = []
    action_required: str | None = None


# ============================================================================
# Generic Response
# ============================================================================


class MessageOnly(BaseModel):
    """Generic message response."""

    message: str
