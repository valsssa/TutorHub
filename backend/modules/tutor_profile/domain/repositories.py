# flake8: noqa: E704
"""Repository interfaces for tutor profile domain."""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Protocol

from .entities import TutorAvailabilityEntity, TutorProfileAggregate


@dataclass(slots=True)
class TutorListingFilter:
    """Filters for listing tutors."""

    subject_id: Optional[int] = None
    min_rate: Optional[Decimal] = None
    max_rate: Optional[Decimal] = None
    min_rating: Optional[Decimal] = None
    min_experience: Optional[int] = None
    language: Optional[str] = None
    search_query: Optional[str] = None
    sort_by: Optional[str] = None  # 'rating', 'rate_asc', 'rate_desc', 'experience'


class TutorProfileRepository(Protocol):
    """Repository contract for tutor profile aggregate."""

    def get_or_create_by_user(self, db, user_id: int) -> TutorProfileAggregate: ...

    def get_by_id(self, db, tutor_id: int) -> Optional[TutorProfileAggregate]: ...

    def list_public(
        self, db, filters: TutorListingFilter
    ) -> List[TutorProfileAggregate]: ...

    def update_about(
        self,
        db,
        user_id: int,
        *,
        title: str,
        headline: Optional[str],
        bio: Optional[str],
        experience_years: int,
        languages: Optional[list[str]]
    ) -> TutorProfileAggregate: ...

    def replace_certifications(
        self, db, user_id: int, certifications: list[dict]
    ) -> TutorProfileAggregate: ...

    def replace_educations(
        self, db, user_id: int, educations: list[dict]
    ) -> TutorProfileAggregate: ...

    def replace_subjects(
        self, db, user_id: int, subjects: list[dict]
    ) -> TutorProfileAggregate: ...

    def update_description(
        self, db, user_id: int, description: str
    ) -> TutorProfileAggregate: ...

    def update_video(
        self, db, user_id: int, video_url: str
    ) -> TutorProfileAggregate: ...

    def update_pricing(
        self,
        db,
        user_id: int,
        *,
        hourly_rate: Decimal,
        pricing_options: list[dict],
        expected_version: int
    ) -> TutorProfileAggregate: ...

    def replace_availability(
        self,
        db,
        user_id: int,
        availability: list[TutorAvailabilityEntity],
        timezone: Optional[str],
        expected_version: int,
    ) -> TutorProfileAggregate: ...
