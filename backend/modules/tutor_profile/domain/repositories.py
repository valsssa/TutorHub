# flake8: noqa: E704
"""Repository interfaces for tutor profile domain."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from .entities import TutorAvailabilityEntity, TutorProfileAggregate


@dataclass(slots=True)
class TutorListingFilter:
    """Filters for listing tutors."""

    subject_id: int | None = None
    min_rate: Decimal | None = None
    max_rate: Decimal | None = None
    min_rating: Decimal | None = None
    min_experience: int | None = None
    language: str | None = None
    search_query: str | None = None
    sort_by: str | None = None  # 'rating', 'rate_asc', 'rate_desc', 'experience'


class TutorProfileRepository(Protocol):
    """Repository contract for tutor profile aggregate."""

    def get_or_create_by_user(self, db, user_id: int) -> TutorProfileAggregate: ...

    def get_by_id(self, db, tutor_id: int) -> TutorProfileAggregate | None: ...

    def list_public(self, db, filters: TutorListingFilter) -> list[TutorProfileAggregate]: ...

    def update_about(
        self,
        db,
        user_id: int,
        *,
        first_name: str | None,
        last_name: str | None,
        title: str,
        headline: str | None,
        bio: str | None,
        experience_years: int,
        languages: list[str] | None,
    ) -> TutorProfileAggregate: ...

    def replace_certifications(self, db, user_id: int, certifications: list[dict]) -> TutorProfileAggregate: ...

    def replace_educations(self, db, user_id: int, educations: list[dict]) -> TutorProfileAggregate: ...

    def replace_subjects(self, db, user_id: int, subjects: list[dict]) -> TutorProfileAggregate: ...

    def update_description(self, db, user_id: int, description: str) -> TutorProfileAggregate: ...

    def update_video(self, db, user_id: int, video_url: str) -> TutorProfileAggregate: ...

    def update_pricing(
        self, db, user_id: int, *, hourly_rate: Decimal, pricing_options: list[dict], expected_version: int
    ) -> TutorProfileAggregate: ...

    def replace_availability(
        self,
        db,
        user_id: int,
        availability: list[TutorAvailabilityEntity],
        timezone: str | None,
        expected_version: int,
    ) -> TutorProfileAggregate: ...
