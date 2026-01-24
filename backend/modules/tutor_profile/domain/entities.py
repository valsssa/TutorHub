"""Domain entities for tutor profiles."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal


@dataclass(slots=True)
class TutorSubjectEntity:
    """Tutor subject specialization."""

    id: int | None
    subject_id: int
    subject_name: str | None
    proficiency_level: str
    years_experience: int | None


@dataclass(slots=True)
class TutorAvailabilityEntity:
    """Tutor availability window."""

    id: int | None
    day_of_week: int
    start_time: time
    end_time: time
    is_recurring: bool
    timezone: str | None = None


@dataclass(slots=True)
class TutorCertificationEntity:
    """Tutor certification credential."""

    id: int | None
    name: str
    issuing_organization: str | None
    issue_date: date | None
    expiration_date: date | None
    credential_id: str | None
    credential_url: str | None
    document_url: str | None


@dataclass(slots=True)
class TutorEducationEntity:
    """Tutor education entry."""

    id: int | None
    institution: str
    degree: str | None
    field_of_study: str | None
    start_year: int | None
    end_year: int | None
    description: str | None
    document_url: str | None


@dataclass(slots=True)
class TutorPricingOptionEntity:
    """Tutor pricing option entity."""

    id: int | None
    title: str
    description: str | None
    duration_minutes: int
    price: Decimal


@dataclass(slots=True)
class TutorProfileAggregate:
    """Aggregate root representing full tutor profile."""

    id: int
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    headline: str | None = None
    bio: str | None = None
    description: str | None = None
    teaching_philosophy: str | None = None
    hourly_rate: Decimal = Decimal("0.00")
    experience_years: int = 0
    education: str | None = None
    languages: list[str] = field(default_factory=list)
    video_url: str | None = None
    auto_confirm: bool = False
    is_approved: bool = False
    profile_status: str = "incomplete"
    rejection_reason: str | None = None
    average_rating: Decimal = Decimal("0.00")
    total_reviews: int = 0
    total_sessions: int = 0
    timezone: str | None = "UTC"
    version: int = 1
    created_at: datetime | None = None
    subjects: list[TutorSubjectEntity] = field(default_factory=list)
    availabilities: list[TutorAvailabilityEntity] = field(default_factory=list)
    certifications: list[TutorCertificationEntity] = field(default_factory=list)
    educations: list[TutorEducationEntity] = field(default_factory=list)
    pricing_options: list[TutorPricingOptionEntity] = field(default_factory=list)
