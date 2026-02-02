"""SQLAlchemy repository implementation for public module.

Provides concrete implementation of the PublicTutorRepository protocol
defined in the domain layer for public tutor search and profiles.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session, joinedload

from core.avatar_storage import build_avatar_url
from models import Subject, TutorProfile, TutorSubject, User

from modules.public.domain.entities import (
    PublicTutorProfileEntity,
    SearchResultEntity,
    SubjectInfo,
)
from modules.public.domain.value_objects import (
    DEFAULT_PAGE_SIZE,
    PaginationParams,
    SearchFilters,
    SearchQuery,
    SortOrder,
)

logger = logging.getLogger(__name__)


class PublicTutorRepositoryImpl:
    """SQLAlchemy implementation of PublicTutorRepository.

    Handles public tutor search and profile retrieval.
    Only returns approved, active tutors with public profiles.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def search(
        self,
        query: SearchQuery | None = None,
        filters: SearchFilters | None = None,
        pagination: PaginationParams | None = None,
        sort_by: SortOrder = SortOrder.RELEVANCE,
    ) -> SearchResultEntity:
        """Search for tutors with optional query, filters, and pagination.

        Args:
            query: Optional search query for text matching
            filters: Optional filters for subject, rating, price, availability
            pagination: Pagination parameters (page, page_size)
            sort_by: Sort order for results

        Returns:
            SearchResultEntity containing matching tutors and pagination info
        """
        pagination = pagination or PaginationParams.default()

        # Build base query with public tutor filters
        base_query = self._build_search_query(query, filters)

        # Get total count before pagination
        total_count = base_query.count()

        # Apply sorting
        sorted_query = self._apply_sorting(base_query, sort_by, query)

        # Apply pagination
        tutors = (
            sorted_query
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        # Convert to entities
        tutor_entities = [self._to_public_entity(t) for t in tutors]

        return SearchResultEntity(
            tutors=tutor_entities,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_public_profile(
        self,
        tutor_id: int,
    ) -> PublicTutorProfileEntity | None:
        """Get a single public tutor profile by tutor profile ID.

        Only returns the profile if the tutor is approved and visible.

        Args:
            tutor_id: Tutor profile ID

        Returns:
            PublicTutorProfileEntity if found and public, None otherwise
        """
        profile = (
            self._base_public_query()
            .filter(TutorProfile.id == tutor_id)
            .first()
        )

        if not profile:
            return None

        return self._to_public_entity(profile)

    def get_public_profile_by_user_id(
        self,
        user_id: int,
    ) -> PublicTutorProfileEntity | None:
        """Get a single public tutor profile by user ID.

        Only returns the profile if the tutor is approved and visible.

        Args:
            user_id: User ID of the tutor

        Returns:
            PublicTutorProfileEntity if found and public, None otherwise
        """
        profile = (
            self._base_public_query()
            .filter(TutorProfile.user_id == user_id)
            .first()
        )

        if not profile:
            return None

        return self._to_public_entity(profile)

    def get_featured(
        self,
        limit: int = 6,
    ) -> list[PublicTutorProfileEntity]:
        """Get featured tutors for homepage display.

        Featured tutors are those with high ratings and many completed sessions.
        Returns top tutors sorted by a combination of rating and session count.

        Args:
            limit: Maximum number of featured tutors to return

        Returns:
            List of featured tutor profiles
        """
        # Featured tutors: high rating, at least some reviews
        profiles = (
            self._base_public_query()
            .filter(TutorProfile.total_reviews >= 1)
            .order_by(
                TutorProfile.average_rating.desc(),
                TutorProfile.total_sessions.desc(),
            )
            .limit(limit)
            .all()
        )

        return [self._to_public_entity(p) for p in profiles]

    def get_by_subject(
        self,
        subject_id: int,
        pagination: PaginationParams | None = None,
        sort_by: SortOrder = SortOrder.RATING,
    ) -> SearchResultEntity:
        """Get tutors who teach a specific subject.

        Args:
            subject_id: Subject ID to filter by
            pagination: Pagination parameters
            sort_by: Sort order for results

        Returns:
            SearchResultEntity containing tutors for the subject
        """
        pagination = pagination or PaginationParams.default()

        # Build query with subject filter
        base_query = (
            self._base_public_query()
            .filter(TutorProfile.subjects.any(TutorSubject.subject_id == subject_id))
        )

        # Get total count
        total_count = base_query.count()

        # Apply sorting
        sorted_query = self._apply_sorting(base_query, sort_by)

        # Apply pagination
        tutors = (
            sorted_query
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        return SearchResultEntity(
            tutors=[self._to_public_entity(t) for t in tutors],
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_top_rated(
        self,
        limit: int = 10,
        min_reviews: int = 3,
    ) -> list[PublicTutorProfileEntity]:
        """Get top-rated tutors.

        Only includes tutors with a minimum number of reviews
        to ensure statistical significance.

        Args:
            limit: Maximum number of tutors to return
            min_reviews: Minimum number of reviews required

        Returns:
            List of top-rated tutor profiles
        """
        profiles = (
            self._base_public_query()
            .filter(TutorProfile.total_reviews >= min_reviews)
            .order_by(TutorProfile.average_rating.desc())
            .limit(limit)
            .all()
        )

        return [self._to_public_entity(p) for p in profiles]

    def count_by_subject(
        self,
        subject_id: int,
    ) -> int:
        """Count tutors teaching a specific subject.

        Args:
            subject_id: Subject ID to filter by

        Returns:
            Number of tutors teaching the subject
        """
        count = (
            self._base_public_query()
            .filter(TutorProfile.subjects.any(TutorSubject.subject_id == subject_id))
            .count()
        )
        return count

    def get_subjects_with_tutors(self) -> list[tuple[int, str, int]]:
        """Get all subjects that have active tutors.

        Returns:
            List of tuples (subject_id, subject_name, tutor_count)
        """
        # Subquery to get active tutor profile IDs
        active_tutor_ids = (
            self.db.query(TutorProfile.id)
            .filter(
                TutorProfile.is_approved.is_(True),
                TutorProfile.profile_status == "approved",
                TutorProfile.deleted_at.is_(None),
            )
            .join(TutorProfile.user)
            .filter(
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .subquery()
        )

        # Query subjects with tutor count
        results = (
            self.db.query(
                Subject.id,
                Subject.name,
                func.count(TutorSubject.tutor_profile_id).label("tutor_count"),
            )
            .join(TutorSubject, Subject.id == TutorSubject.subject_id)
            .filter(
                TutorSubject.tutor_profile_id.in_(active_tutor_ids),
                Subject.is_active.is_(True),
            )
            .group_by(Subject.id, Subject.name)
            .having(func.count(TutorSubject.tutor_profile_id) > 0)
            .order_by(func.count(TutorSubject.tutor_profile_id).desc())
            .all()
        )

        return [(r[0], r[1], r[2]) for r in results]

    def _base_public_query(self):
        """Build base query for public tutor profiles.

        Returns only approved, active tutors with non-deleted accounts.

        Returns:
            SQLAlchemy query with public filters applied
        """
        return (
            self.db.query(TutorProfile)
            .options(
                joinedload(TutorProfile.subjects).joinedload(TutorSubject.subject),
                joinedload(TutorProfile.user),
            )
            .filter(
                TutorProfile.is_approved.is_(True),
                TutorProfile.profile_status == "approved",
                TutorProfile.deleted_at.is_(None),
            )
            .join(TutorProfile.user)
            .filter(
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )

    def _build_search_query(
        self,
        query: SearchQuery | None,
        filters: SearchFilters | None,
    ):
        """Build dynamic search query with filters.

        Args:
            query: Optional search query for text matching
            filters: Optional filters for subject, rating, price, availability

        Returns:
            SQLAlchemy query with all filters applied
        """
        base = self._base_public_query()

        # Apply text search
        if query and not query.is_empty:
            search_term = f"%{query.value}%"
            # Search in tutor profile fields and user name
            base = base.filter(
                or_(
                    TutorProfile.title.ilike(search_term),
                    TutorProfile.headline.ilike(search_term),
                    TutorProfile.bio.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                )
            )

        # Apply filters if provided
        if filters:
            # Subject filter
            if filters.subject_id is not None:
                base = base.filter(
                    TutorProfile.subjects.any(
                        TutorSubject.subject_id == filters.subject_id
                    )
                )

            # Minimum rating filter
            if filters.min_rating is not None:
                base = base.filter(
                    TutorProfile.average_rating >= Decimal(str(filters.min_rating))
                )

            # Maximum price filter (hourly_rate is in dollars, max_price in cents)
            if filters.max_price is not None:
                max_price_dollars = Decimal(filters.max_price) / 100
                base = base.filter(TutorProfile.hourly_rate <= max_price_dollars)

            # Availability filter is noted but implementation depends on
            # availability data structure - could be added in the future

        return base

    def _apply_sorting(
        self,
        query,
        sort_by: SortOrder,
        search_query: SearchQuery | None = None,
    ):
        """Apply sorting to the query.

        Args:
            query: SQLAlchemy query
            sort_by: Sort order to apply
            search_query: Optional search query (for relevance scoring)

        Returns:
            Sorted query
        """
        if sort_by == SortOrder.RATING:
            return query.order_by(
                TutorProfile.average_rating.desc(),
                TutorProfile.total_reviews.desc(),
            )
        elif sort_by == SortOrder.PRICE_LOW:
            return query.order_by(TutorProfile.hourly_rate.asc())
        elif sort_by == SortOrder.PRICE_HIGH:
            return query.order_by(TutorProfile.hourly_rate.desc())
        elif sort_by == SortOrder.NEWEST:
            return query.order_by(TutorProfile.created_at.desc())
        else:
            # RELEVANCE or default - use rating + sessions as proxy for relevance
            # If there's a search query, results are already filtered by relevance
            return query.order_by(
                TutorProfile.average_rating.desc(),
                TutorProfile.total_sessions.desc(),
            )

    def _to_public_entity(self, model: TutorProfile) -> PublicTutorProfileEntity:
        """Convert SQLAlchemy model to public domain entity.

        Maps tutor profile to minimal public information only.
        Excludes sensitive data like contact details.

        Args:
            model: TutorProfile SQLAlchemy model

        Returns:
            PublicTutorProfileEntity domain entity
        """
        # Get user information
        first_name = ""
        last_name = None
        avatar_url = None

        if model.user:
            first_name = model.user.first_name or ""
            last_name = model.user.last_name
            avatar_key = getattr(model.user, "avatar_key", None)
            avatar_url = build_avatar_url(avatar_key, allow_absolute=True)

        # Build subject list
        subjects = []
        for ts in model.subjects:
            if ts.subject:
                subjects.append(
                    SubjectInfo(
                        id=ts.subject.id,
                        name=ts.subject.name,
                        category=ts.subject.category,
                    )
                )

        # Convert hourly rate to cents
        hourly_rate_cents = None
        if model.hourly_rate is not None:
            hourly_rate_cents = int(model.hourly_rate * 100)

        # Determine if featured (high rating with reviews)
        is_featured = (
            model.total_reviews is not None
            and model.total_reviews >= 5
            and model.average_rating is not None
            and float(model.average_rating) >= 4.5
        )

        return PublicTutorProfileEntity(
            id=model.id,
            user_id=model.user_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            headline=model.headline,
            bio=model.bio,
            subjects=subjects,
            average_rating=float(model.average_rating) if model.average_rating else None,
            total_reviews=model.total_reviews or 0,
            completed_sessions=model.total_sessions or 0,
            hourly_rate_cents=hourly_rate_cents,
            currency=model.currency or "USD",
            years_experience=model.experience_years,
            response_time_hours=None,  # Could be populated from TutorMetrics
            is_featured=is_featured,
        )
