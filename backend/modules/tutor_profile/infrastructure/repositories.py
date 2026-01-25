"""SQLAlchemy repository implementation for tutor profiles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from models import (
    TutorAvailability,
    TutorCertification,
    TutorEducation,
    TutorPricingOption,
    TutorProfile,
    TutorSubject,
    User,
    UserProfile,
)

from ...tutor_profile.domain.entities import (
    TutorAvailabilityEntity,
    TutorCertificationEntity,
    TutorEducationEntity,
    TutorPricingOptionEntity,
    TutorProfileAggregate,
    TutorSubjectEntity,
)
from ...tutor_profile.domain.repositories import (
    TutorListingFilter,
    TutorProfileRepository,
)


@dataclass(slots=True)
class SqlAlchemyTutorProfileRepository(TutorProfileRepository):
    """Repository backed by SQLAlchemy ORM."""

    def get_or_create_by_user(self, db: Session, user_id: int) -> TutorProfileAggregate:
        # CRITICAL: Validate user has tutor role before creating profile
        from fastapi import HTTPException, status

        from models import User

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.role != "tutor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role is '{user.role}', not 'tutor'. "
                "Contact an administrator to change your role before accessing tutor features.",
            )

        profile = self._query_base(db).filter(TutorProfile.user_id == user_id).first()
        if not profile:
            profile = TutorProfile(
                user_id=user_id,
                title="",
                headline=None,
                bio=None,
                description=None,
                hourly_rate=Decimal("1.00"),
                experience_years=0,
                education=None,
                languages=[],
                video_url=None,
            )
            db.add(profile)
            db.commit()
            profile = self._query_base(db).filter(TutorProfile.user_id == user_id).first()
        return self._to_aggregate(profile)

    def get_by_id(self, db: Session, tutor_id: int) -> TutorProfileAggregate | None:
        profile = self._query_base(db).filter(TutorProfile.id == tutor_id).first()
        if not profile or not profile.is_approved:
            return None
        return self._to_aggregate(profile)

    def list_public(
        self, db: Session, filters: TutorListingFilter, pagination
    ) -> tuple[list[TutorProfileAggregate], int]:
        # Use eager loading base query for optimal performance
        # Only show approved tutors to students
        query = self._query_base(db).filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.profile_status == "approved",
        )

        # Filter by subject (join only if filtering, eager load already loaded)
        if filters.subject_id is not None:
            # The join is already loaded via joinedload, just filter
            query = query.filter(TutorProfile.subjects.any(TutorSubject.subject_id == filters.subject_id))

        # Filter by rate range
        if filters.min_rate is not None:
            query = query.filter(TutorProfile.hourly_rate >= filters.min_rate)
        if filters.max_rate is not None:
            query = query.filter(TutorProfile.hourly_rate <= filters.max_rate)

        # Filter by rating
        if filters.min_rating is not None:
            query = query.filter(TutorProfile.average_rating >= filters.min_rating)

        # Filter by experience
        if filters.min_experience is not None:
            query = query.filter(TutorProfile.experience_years >= filters.min_experience)

        # Filter by language
        if filters.language is not None:
            try:
                # Try PostgreSQL-specific array containment
                from sqlalchemy import String, cast
                from sqlalchemy.dialects.postgresql import ARRAY

                query = query.filter(cast(TutorProfile.languages, ARRAY(String)).contains([filters.language]))
            except Exception:
                # Fallback for SQLite/other DBs - serialize check
                query = query.filter(TutorProfile.languages.contains(filters.language))

        # Search in title, headline, and bio
        if filters.search_query is not None:
            search = f"%{filters.search_query}%"
            query = query.filter(
                (TutorProfile.title.ilike(search))
                | (TutorProfile.headline.ilike(search))
                | (TutorProfile.bio.ilike(search))
            )

        # Get total count before pagination
        total = query.count()

        # Sorting
        if filters.sort_by == "rating":
            query = query.order_by(TutorProfile.average_rating.desc())
        elif filters.sort_by == "rate_asc":
            query = query.order_by(TutorProfile.hourly_rate.asc())
        elif filters.sort_by == "rate_desc":
            query = query.order_by(TutorProfile.hourly_rate.desc())
        elif filters.sort_by == "experience":
            query = query.order_by(TutorProfile.experience_years.desc())
        else:
            # Default sort by rating
            query = query.order_by(TutorProfile.average_rating.desc())

        # Apply pagination
        profiles = query.offset(pagination.skip).limit(pagination.limit).all()
        return [self._to_aggregate(profile) for profile in profiles], total

    def update_about(
        self,
        db: Session,
        user_id: int,
        *,
        first_name: str | None,
        last_name: str | None,
        title: str,
        headline: str | None,
        bio: str | None,
        teaching_philosophy: str | None,
        experience_years: int,
        languages: list[str] | None,
    ) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        profile.title = title
        profile.headline = headline
        profile.bio = bio
        profile.teaching_philosophy = teaching_philosophy
        profile.experience_years = experience_years
        profile.languages = languages or []

        # NOTE: first_name/last_name sync removed - names now stored directly in users table
        profile.updated_at = datetime.now(UTC)
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def replace_certifications(
        self,
        db: Session,
        user_id: int,
        certifications: list[dict],
    ) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        db.query(TutorCertification).filter(TutorCertification.tutor_profile_id == profile.id).delete()
        now = datetime.now(UTC)
        for item in certifications:
            cert = TutorCertification(tutor_profile_id=profile.id, **item)
            cert.updated_at = now  # Set timestamp in application code
            db.add(cert)
        profile.updated_at = now  # Also update parent profile
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def replace_educations(
        self,
        db: Session,
        user_id: int,
        educations: list[dict],
    ) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        db.query(TutorEducation).filter(TutorEducation.tutor_profile_id == profile.id).delete()
        now = datetime.now(UTC)
        for item in educations:
            edu = TutorEducation(tutor_profile_id=profile.id, **item)
            edu.updated_at = now  # Set timestamp in application code
            db.add(edu)
        profile.updated_at = now  # Also update parent profile
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def replace_subjects(
        self,
        db: Session,
        user_id: int,
        subjects: list[dict],
    ) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        db.query(TutorSubject).filter(TutorSubject.tutor_profile_id == profile.id).delete()
        now = datetime.now(UTC)
        for item in subjects:
            subj = TutorSubject(tutor_profile_id=profile.id, **item)
            # Note: TutorSubject may not have updated_at column, check model
            if hasattr(subj, "updated_at"):
                subj.updated_at = now  # Set timestamp in application code
            db.add(subj)
        profile.updated_at = now  # Always update parent profile
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def update_description(self, db: Session, user_id: int, description: str) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        profile.description = description.strip()
        profile.updated_at = datetime.now(UTC)  # Update in code
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def update_video(self, db: Session, user_id: int, video_url: str) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        profile.video_url = video_url
        profile.updated_at = datetime.now(UTC)  # Update in code
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def update_profile_photo(self, db: Session, user_id: int, photo_url: str) -> TutorProfileAggregate:
        from datetime import datetime

        profile = self._ensure_profile(db, user_id)
        # Update User avatar_key instead of TutorProfile (which doesn't have photo field)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.avatar_key = photo_url
            user.updated_at = datetime.now(UTC)  # Update in code
        profile.updated_at = datetime.now(UTC)  # Update in code
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def update_pricing(
        self,
        db: Session,
        user_id: int,
        *,
        hourly_rate: Decimal,
        pricing_options: list[dict],
        expected_version: int,
    ) -> TutorProfileAggregate:
        from fastapi import HTTPException, status

        profile = self._ensure_profile(db, user_id)

        # Optimistic locking check - prevent concurrent edits
        if profile.version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile has been modified by another request. Please refresh and try again. Expected version {expected_version}, but current version is {profile.version}.",
            )

        from datetime import datetime

        now = datetime.now(UTC)
        profile.hourly_rate = hourly_rate

        # Atomic update: delete old and insert new pricing options
        db.query(TutorPricingOption).filter(TutorPricingOption.tutor_profile_id == profile.id).delete()
        for item in pricing_options:
            option = TutorPricingOption(tutor_profile_id=profile.id, **item)
            option.updated_at = now  # Set timestamp in application code
            db.add(option)

        # Increment version after successful update
        profile.version += 1
        profile.updated_at = now  # Update parent profile

        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def replace_availability(
        self,
        db: Session,
        user_id: int,
        availability: list[TutorAvailabilityEntity],
        timezone: str | None,
        expected_version: int,
    ) -> TutorProfileAggregate:
        from fastapi import HTTPException, status

        profile = self._ensure_profile(db, user_id)

        # Optimistic locking check - prevent concurrent edits
        if profile.version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile has been modified by another request. Please refresh and try again. Expected version {expected_version}, but current version is {profile.version}.",
            )

        from datetime import datetime

        # Update timezone on user profile if provided
        if timezone:
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == profile.user_id).first()
            if not user_profile:
                user_profile = UserProfile(user_id=profile.user_id, timezone=timezone)
                db.add(user_profile)
            else:
                user_profile.timezone = timezone
                user_profile.updated_at = datetime.now(UTC)  # Update in code

        # Atomic update: delete old and insert new
        db.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == profile.id).delete()
        for slot in availability:
            db.add(
                TutorAvailability(
                    tutor_profile_id=profile.id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    is_recurring=slot.is_recurring,
                )
            )

        # Increment version after successful update
        profile.version += 1
        profile.updated_at = datetime.now(UTC)  # Update in code

        db.commit()
        return self._aggregate_from_db(db, profile.id)

    def submit_for_review(self, db: Session, user_id: int) -> TutorProfileAggregate:
        """Submit tutor profile for admin review."""
        profile = self._ensure_profile(db, user_id)

        # Validate profile has required fields
        # Note: Avatar is now stored in users.avatar_key, not in tutor profile
        has_title = profile.title and len(profile.title) > 0
        normalized_description = (profile.description or "").strip()
        has_description = len(normalized_description) >= 400

        # Check if user has avatar
        user = db.query(User).filter(User.id == user_id).first()
        has_photo = user and user.avatar_key is not None

        if not (has_photo and has_title and has_description):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail="Profile must have photo, title, and description (min 400 chars) before submission",
            )

        # Treat repeated submissions from pending_approval as idempotent
        if profile.profile_status == "pending_approval":
            return self._aggregate_from_db(db, profile.id)

        # Only allow submission if status is incomplete or rejected
        if profile.profile_status not in ["incomplete", "rejected"]:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail=f"Profile cannot be submitted from status: {profile.profile_status}",
            )

        profile.profile_status = "pending_approval"
        profile.rejection_reason = None  # Clear any previous rejection reason
        db.commit()
        return self._aggregate_from_db(db, profile.id)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _query_base(self, db: Session):
        return db.query(TutorProfile).options(
            joinedload(TutorProfile.subjects).joinedload(TutorSubject.subject),
            joinedload(TutorProfile.availabilities),
            joinedload(TutorProfile.certifications),
            joinedload(TutorProfile.educations),
            joinedload(TutorProfile.pricing_options),
            joinedload(TutorProfile.user).joinedload(User.profile),
        )

    def _ensure_profile(self, db: Session, user_id: int) -> TutorProfile:
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()
        if not profile:
            profile = TutorProfile(
                user_id=user_id,
                title="",
                hourly_rate=Decimal("1.00"),
                languages=[],
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    def _aggregate_from_db(self, db: Session, profile_id: int) -> TutorProfileAggregate:
        profile = self._query_base(db).filter(TutorProfile.id == profile_id).first()
        return self._to_aggregate(profile)

    def _to_aggregate(self, profile: TutorProfile) -> TutorProfileAggregate:
        timezone = "UTC"
        if profile.user and profile.user.profile and profile.user.profile.timezone:
            timezone = profile.user.profile.timezone

        subjects = [
            TutorSubjectEntity(
                id=subject.id,
                subject_id=subject.subject_id,
                subject_name=subject.subject.name if subject.subject else None,
                proficiency_level=subject.proficiency_level,
                years_experience=subject.years_experience,
            )
            for subject in profile.subjects
        ]

        availabilities = [
            TutorAvailabilityEntity(
                id=slot.id,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                is_recurring=slot.is_recurring,
                timezone=timezone,
            )
            for slot in profile.availabilities
        ]

        certifications = [
            TutorCertificationEntity(
                id=item.id,
                name=item.name,
                issuing_organization=item.issuing_organization,
                issue_date=item.issue_date,
                expiration_date=item.expiration_date,
                credential_id=item.credential_id,
                credential_url=item.credential_url,
                document_url=item.document_url,
            )
            for item in profile.certifications
        ]

        educations = [
            TutorEducationEntity(
                id=item.id,
                institution=item.institution,
                degree=item.degree,
                field_of_study=item.field_of_study,
                start_year=item.start_year,
                end_year=item.end_year,
                description=item.description,
                document_url=item.document_url,
            )
            for item in profile.educations
        ]

        pricing_options = [
            TutorPricingOptionEntity(
                id=item.id,
                title=item.title,
                description=item.description,
                duration_minutes=item.duration_minutes,
                price=item.price,
            )
            for item in profile.pricing_options
        ]

        first_name = None
        last_name = None
        profile_photo_url = None
        if profile.user:
            first_name = getattr(profile.user, "first_name", None)
            last_name = getattr(profile.user, "last_name", None)
            avatar_key = getattr(profile.user, "avatar_key", None)
            # avatar_key should contain the full public URL from MinIO storage
            # Format: {MINIO_PUBLIC_ENDPOINT}/{MINIO_BUCKET}/tutor_profiles/{user_id}/photo/{filename}
            # If it's an old avatar URL format, it will need to be re-uploaded to get the correct URL
            profile_photo_url = avatar_key

        return TutorProfileAggregate(
            id=profile.id,
            user_id=profile.user_id,
            first_name=first_name,
            last_name=last_name,
            title=profile.title or "",
            headline=profile.headline,
            bio=profile.bio,
            description=profile.description,
            teaching_philosophy=profile.teaching_philosophy,
            hourly_rate=profile.hourly_rate or Decimal("0.00"),
            experience_years=profile.experience_years or 0,
            education=profile.education,
            languages=profile.languages or [],
            video_url=profile.video_url,
            auto_confirm=bool(profile.auto_confirm),
            is_approved=profile.is_approved,
            profile_status=profile.profile_status or "incomplete",
            rejection_reason=profile.rejection_reason,
            average_rating=profile.average_rating or Decimal("0.00"),
            total_reviews=profile.total_reviews or 0,
            total_sessions=profile.total_sessions or 0,
            timezone=timezone,
            version=profile.version or 1,
            profile_photo_url=profile_photo_url,
            subjects=subjects,
            availabilities=availabilities,
            certifications=certifications,
            educations=educations,
            pricing_options=pricing_options,
            created_at=profile.created_at,
        )
