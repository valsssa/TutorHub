"""Domain entities for tutor profiles."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional


@dataclass(slots=True)
class TutorSubjectEntity:
    """Tutor subject specialization."""

    id: Optional[int]
    subject_id: int
    subject_name: Optional[str]
    proficiency_level: str
    years_experience: Optional[int]


@dataclass(slots=True)
class TutorAvailabilityEntity:
    """Tutor availability window."""

    id: Optional[int]
    day_of_week: int
    start_time: time
    end_time: time
    is_recurring: bool
    timezone: Optional[str] = None


@dataclass(slots=True)
class TutorCertificationEntity:
    """Tutor certification credential."""

    id: Optional[int]
    name: str
    issuing_organization: Optional[str]
    issue_date: Optional[date]
    expiration_date: Optional[date]
    credential_id: Optional[str]
    credential_url: Optional[str]
    document_url: Optional[str]


@dataclass(slots=True)
class TutorEducationEntity:
    """Tutor education entry."""

    id: Optional[int]
    institution: str
    degree: Optional[str]
    field_of_study: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    description: Optional[str]
    document_url: Optional[str]


@dataclass(slots=True)
class TutorPricingOptionEntity:
    """Tutor pricing option entity."""

    id: Optional[int]
    title: str
    description: Optional[str]
    duration_minutes: int
    price: Decimal


@dataclass(slots=True)
class TutorProfileAggregate:
    """Aggregate root representing full tutor profile."""

    id: int
    user_id: int
    title: Optional[str]
    headline: Optional[str]
    bio: Optional[str]
    description: Optional[str]
    hourly_rate: Decimal
    experience_years: int
    education: Optional[str]
    languages: List[str] = field(default_factory=list)
    video_url: Optional[str] = None
    is_approved: bool = False
    profile_status: str = "incomplete"
    rejection_reason: Optional[str] = None
    average_rating: Decimal = Decimal("0.00")
    total_reviews: int = 0
    total_sessions: int = 0
    timezone: Optional[str] = "UTC"
    version: int = 1
    created_at: Optional[datetime] = None
    subjects: List[TutorSubjectEntity] = field(default_factory=list)
    availabilities: List[TutorAvailabilityEntity] = field(default_factory=list)
    certifications: List[TutorCertificationEntity] = field(default_factory=list)
    educations: List[TutorEducationEntity] = field(default_factory=list)
    pricing_options: List[TutorPricingOptionEntity] = field(default_factory=list)
