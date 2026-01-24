"""Tutor profile application service."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from core.pagination import PaginatedResponse, PaginationParams
from core.storage import delete_files, store_supporting_document
from schemas import (
    TutorAboutUpdate,
    TutorAvailabilityBulkUpdate,
    TutorAvailabilityInput,
    TutorCertificationInput,
    TutorDescriptionUpdate,
    TutorEducationInput,
    TutorPricingUpdate,
    TutorSubjectInput,
    TutorVideoUpdate,
)

from ..domain.entities import TutorAvailabilityEntity
from ..domain.repositories import TutorListingFilter, TutorProfileRepository
from .dto import aggregate_to_profile_response, aggregate_to_public_profile


class TutorProfileService:
    """Coordinator for tutor profile use cases."""

    def __init__(self, repository: TutorProfileRepository):
        self.repository = repository

    # --------------------------------------------------------------------- #
    # Queries
    # --------------------------------------------------------------------- #
    def get_profile_by_user(self, db: Session, user_id: int):
        aggregate = self.repository.get_or_create_by_user(db, user_id)
        return aggregate_to_profile_response(aggregate)

    def get_profile_by_id(self, db: Session, tutor_id: int):
        aggregate = self.repository.get_by_id(db, tutor_id)
        if not aggregate:
            return None
        return aggregate_to_profile_response(aggregate)

    def get_public_profile_by_id(self, db: Session, tutor_id: int):
        aggregate = self.repository.get_by_id(db, tutor_id)
        if not aggregate:
            return None
        return aggregate_to_public_profile(aggregate)

    def list_public_profiles(
        self,
        db: Session,
        *,
        pagination: PaginationParams,
        subject_id: int | None = None,
        min_rate: float | None = None,
        max_rate: float | None = None,
        min_rating: float | None = None,
        min_experience: int | None = None,
        language: str | None = None,
        search_query: str | None = None,
        sort_by: str | None = None,
    ):
        filters = TutorListingFilter(
            subject_id=subject_id,
            min_rate=min_rate,
            max_rate=max_rate,
            min_rating=min_rating,
            min_experience=min_experience,
            language=language,
            search_query=search_query,
            sort_by=sort_by,
        )
        aggregates, total = self.repository.list_public(db, filters, pagination)
        items = [aggregate_to_public_profile(agg) for agg in aggregates]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # --------------------------------------------------------------------- #
    # Commands
    # --------------------------------------------------------------------- #
    def update_about(self, db: Session, user_id: int, payload: TutorAboutUpdate):
        aggregate = self.repository.update_about(
            db,
            user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            title=payload.title,
            headline=payload.headline,
            bio=payload.bio,
            experience_years=payload.experience_years,
            languages=payload.languages,
        )
        return aggregate_to_profile_response(aggregate)

    async def replace_certifications(
        self,
        db: Session,
        user_id: int,
        payload: list[TutorCertificationInput],
        file_map: dict[int, UploadFile],
    ):
        current = self.repository.get_or_create_by_user(db, user_id)
        new_items: list[dict] = []
        stored_urls: list[str] = []
        for idx, item in enumerate(payload):
            item_data = item.model_dump()
            upload = file_map.get(idx)
            if upload:
                document_url = await store_supporting_document(user_id, "certifications", upload)
                stored_urls.append(document_url)
                item_data["document_url"] = document_url
            new_items.append(item_data)

        try:
            aggregate = self.repository.replace_certifications(
                db,
                user_id,
                list(new_items),
            )
        except Exception:
            delete_files(stored_urls)
            raise

        preserved_urls = {item.get("document_url") for item in new_items if item.get("document_url")}
        stale_urls = [
            cert.document_url
            for cert in current.certifications
            if cert.document_url and cert.document_url not in preserved_urls
        ]
        delete_files(stale_urls)
        return aggregate_to_profile_response(aggregate)

    def replace_subjects(
        self,
        db: Session,
        user_id: int,
        payload: list[TutorSubjectInput],
    ):
        aggregate = self.repository.replace_subjects(
            db,
            user_id,
            [item.model_dump() for item in payload],
        )
        return aggregate_to_profile_response(aggregate)

    async def replace_educations(
        self,
        db: Session,
        user_id: int,
        payload: list[TutorEducationInput],
        file_map: dict[int, UploadFile],
    ):
        current = self.repository.get_or_create_by_user(db, user_id)
        new_items: list[dict] = []
        stored_urls: list[str] = []
        for idx, item in enumerate(payload):
            item_data = item.model_dump()
            upload = file_map.get(idx)
            if upload:
                document_url = await store_supporting_document(user_id, "education", upload)
                stored_urls.append(document_url)
                item_data["document_url"] = document_url
            new_items.append(item_data)

        try:
            aggregate = self.repository.replace_educations(
                db,
                user_id,
                list(new_items),
            )
        except Exception:
            delete_files(stored_urls)
            raise

        preserved_urls = {item.get("document_url") for item in new_items if item.get("document_url")}
        stale_urls = [
            edu.document_url
            for edu in current.educations
            if edu.document_url and edu.document_url not in preserved_urls
        ]
        delete_files(stale_urls)
        return aggregate_to_profile_response(aggregate)

    def update_description(self, db: Session, user_id: int, payload: TutorDescriptionUpdate):
        aggregate = self.repository.update_description(db, user_id, payload.description)
        return aggregate_to_profile_response(aggregate)

    def update_video(self, db: Session, user_id: int, payload: TutorVideoUpdate):
        aggregate = self.repository.update_video(db, user_id, payload.video_url)
        return aggregate_to_profile_response(aggregate)

    async def update_profile_photo(self, db: Session, user_id: int, upload: UploadFile):
        """Update tutor profile photo."""
        from core.storage import delete_file, store_profile_photo

        # Get existing avatar_key from User model
        from models import User

        user = db.query(User).filter(User.id == user_id).first()
        existing_url = user.avatar_key if user and user.avatar_key else None

        # Store new photo
        photo_url = await store_profile_photo(user_id, upload, existing_url=existing_url)

        # Update User avatar_key with new photo URL
        aggregate = self.repository.update_profile_photo(db, user_id, photo_url)

        # Delete old photo if it exists and is different
        if existing_url and existing_url != photo_url:
            delete_file(existing_url)

        return aggregate_to_profile_response(aggregate)

    def update_pricing(self, db: Session, user_id: int, payload: TutorPricingUpdate):
        aggregate = self.repository.update_pricing(
            db,
            user_id,
            hourly_rate=payload.hourly_rate,
            pricing_options=[item.model_dump() for item in payload.pricing_options],
            expected_version=payload.version,
        )
        return aggregate_to_profile_response(aggregate)

    def replace_availability(
        self,
        db: Session,
        user_id: int,
        payload: TutorAvailabilityBulkUpdate,
    ):
        availability_entities = [self._to_availability_entity(item, payload.timezone) for item in payload.availability]
        aggregate = self.repository.replace_availability(
            db,
            user_id,
            availability_entities,
            payload.timezone,
            expected_version=payload.version,
        )
        return aggregate_to_profile_response(aggregate)

    def submit_for_review(self, db: Session, user_id: int):
        """Submit tutor profile for admin review."""
        aggregate = self.repository.submit_for_review(db, user_id)
        return aggregate_to_profile_response(aggregate)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _to_availability_entity(
        self,
        payload: TutorAvailabilityInput,
        timezone: str | None,
    ) -> TutorAvailabilityEntity:
        return TutorAvailabilityEntity(
            id=None,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_recurring=payload.is_recurring,
            timezone=timezone,
        )
