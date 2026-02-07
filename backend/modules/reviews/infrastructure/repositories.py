"""SQLAlchemy repository implementation for reviews."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.datetime_utils import utc_now
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from models.reviews import Review
from modules.reviews.domain.entities import ReviewEntity, ReviewSummary
from modules.reviews.domain.exceptions import DuplicateReviewError
from modules.reviews.domain.repositories import ReviewRepository
from modules.reviews.domain.value_objects import (
    BookingId,
    ReviewId,
    StudentId,
    TutorProfileId,
)


@dataclass(slots=True)
class ReviewRepositoryImpl(ReviewRepository):
    """Repository backed by SQLAlchemy ORM."""

    db: Session

    def get_by_id(self, review_id: ReviewId) -> ReviewEntity | None:
        """
        Get a review by its ID.

        Args:
            review_id: Review's unique identifier

        Returns:
            ReviewEntity if found, None otherwise
        """
        review = self.db.query(Review).filter(Review.id == int(review_id)).first()
        if not review:
            return None
        return self._to_entity(review)

    def get_by_booking(self, booking_id: BookingId) -> ReviewEntity | None:
        """
        Get a review for a specific booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            ReviewEntity if found, None otherwise
        """
        review = self.db.query(Review).filter(Review.booking_id == int(booking_id)).first()
        if not review:
            return None
        return self._to_entity(review)

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        only_public: bool = True,
        min_rating: int | None = None,
        max_rating: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ReviewEntity]:
        """
        Get reviews for a tutor with optional filtering.

        Args:
            tutor_profile_id: Tutor's profile ID
            only_public: Only return public reviews
            min_rating: Filter by minimum rating
            max_rating: Filter by maximum rating
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching reviews, ordered by created_at descending
        """
        query = self.db.query(Review).filter(
            Review.tutor_profile_id == int(tutor_profile_id)
        )

        if only_public:
            query = query.filter(Review.is_public.is_(True))

        if min_rating is not None:
            query = query.filter(Review.rating >= min_rating)

        if max_rating is not None:
            query = query.filter(Review.rating <= max_rating)

        query = query.order_by(Review.created_at.desc())

        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()

        return [self._to_entity(r) for r in reviews]

    def get_by_student(
        self,
        student_id: StudentId,
        *,
        tutor_profile_id: TutorProfileId | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ReviewEntity]:
        """
        Get reviews written by a student.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Optional filter by tutor
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of reviews by the student, ordered by created_at descending
        """
        query = self.db.query(Review).filter(Review.student_id == int(student_id))

        if tutor_profile_id is not None:
            query = query.filter(Review.tutor_profile_id == int(tutor_profile_id))

        query = query.order_by(Review.created_at.desc())

        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()

        return [self._to_entity(r) for r in reviews]

    def create(self, review: ReviewEntity) -> ReviewEntity:
        """
        Create a new review.

        Args:
            review: Review entity to create

        Returns:
            Created review with populated ID and timestamps

        Raises:
            DuplicateReviewError: If a review already exists for the booking
        """
        if self.exists_for_booking(review.booking_id):
            existing = self.get_by_booking(review.booking_id)
            raise DuplicateReviewError(
                booking_id=int(review.booking_id),
                existing_review_id=int(existing.id) if existing and existing.id else None,
            )

        now = utc_now()
        model = self._to_model(review)
        model.created_at = now

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def update(self, review: ReviewEntity) -> ReviewEntity:
        """
        Update an existing review.

        Args:
            review: Review entity with updated fields

        Returns:
            Updated review entity
        """
        if review.id is None:
            raise ValueError("Cannot update review without ID")

        model = self.db.query(Review).filter(Review.id == int(review.id)).first()
        if not model:
            raise ValueError(f"Review with ID {review.id} not found")

        model.rating = review.rating
        model.comment = review.content
        model.is_public = review.is_public
        model.booking_snapshot = review.booking_snapshot

        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def delete(self, review_id: ReviewId) -> bool:
        """
        Delete a review.

        Args:
            review_id: ID of the review to delete

        Returns:
            True if deleted, False if not found
        """
        result = self.db.query(Review).filter(Review.id == int(review_id)).delete()
        self.db.commit()
        return result > 0

    def calculate_average_rating(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> tuple[Decimal, int]:
        """
        Calculate average rating for a tutor using SQL aggregation.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Tuple of (average_rating, total_review_count)
            Returns (Decimal("0.00"), 0) if no reviews exist
        """
        result = (
            self.db.query(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_count"),
            )
            .filter(Review.tutor_profile_id == int(tutor_profile_id))
            .first()
        )

        if not result or result.total_count == 0:
            return Decimal("0.00"), 0

        avg_rating = Decimal(str(round(float(result.avg_rating), 2)))
        return avg_rating, result.total_count

    def get_summary(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> ReviewSummary:
        """
        Get review summary statistics for a tutor.

        Includes average rating, total count, and rating distribution.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            ReviewSummary with statistics
        """
        result = (
            self.db.query(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_count"),
                func.sum(case((Review.rating == 5, 1), else_=0)).label("five_star"),
                func.sum(case((Review.rating == 4, 1), else_=0)).label("four_star"),
                func.sum(case((Review.rating == 3, 1), else_=0)).label("three_star"),
                func.sum(case((Review.rating == 2, 1), else_=0)).label("two_star"),
                func.sum(case((Review.rating == 1, 1), else_=0)).label("one_star"),
            )
            .filter(Review.tutor_profile_id == int(tutor_profile_id))
            .first()
        )

        if not result or result.total_count == 0:
            return ReviewSummary.empty(tutor_profile_id)

        return ReviewSummary(
            tutor_profile_id=tutor_profile_id,
            total_reviews=result.total_count,
            average_rating=round(float(result.avg_rating), 2),
            five_star_count=result.five_star or 0,
            four_star_count=result.four_star or 0,
            three_star_count=result.three_star or 0,
            two_star_count=result.two_star or 0,
            one_star_count=result.one_star or 0,
        )

    def count_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        only_public: bool = True,
    ) -> int:
        """
        Count reviews for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            only_public: Only count public reviews

        Returns:
            Count of matching reviews
        """
        query = self.db.query(func.count(Review.id)).filter(
            Review.tutor_profile_id == int(tutor_profile_id)
        )

        if only_public:
            query = query.filter(Review.is_public.is_(True))

        return query.scalar() or 0

    def count_by_student(
        self,
        student_id: StudentId,
    ) -> int:
        """
        Count reviews written by a student.

        Args:
            student_id: Student's user ID

        Returns:
            Count of reviews by student
        """
        return (
            self.db.query(func.count(Review.id))
            .filter(Review.student_id == int(student_id))
            .scalar()
            or 0
        )

    def exists_for_booking(self, booking_id: BookingId) -> bool:
        """
        Check if a review exists for a booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            True if review exists, False otherwise
        """
        return (
            self.db.query(func.count(Review.id))
            .filter(Review.booking_id == int(booking_id))
            .scalar()
            or 0
        ) > 0

    def get_recent_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        limit: int = 5,
    ) -> list[ReviewEntity]:
        """
        Get the most recent public reviews for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            limit: Maximum number of reviews to return

        Returns:
            List of recent public reviews
        """
        reviews = (
            self.db.query(Review)
            .filter(
                Review.tutor_profile_id == int(tutor_profile_id),
                Review.is_public.is_(True),
            )
            .order_by(Review.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_entity(r) for r in reviews]

    def get_featured_reviews(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        limit: int = 3,
    ) -> list[ReviewEntity]:
        """
        Get featured reviews for a tutor (high-rated with content).

        Selects reviews that are:
        - Public
        - Rating of 4 or 5
        - Has non-empty content

        Args:
            tutor_profile_id: Tutor's profile ID
            limit: Maximum number of reviews to return

        Returns:
            List of featured reviews
        """
        reviews = (
            self.db.query(Review)
            .filter(
                Review.tutor_profile_id == int(tutor_profile_id),
                Review.is_public.is_(True),
                Review.rating >= 4,
                Review.comment.isnot(None),
                Review.comment != "",
            )
            .order_by(Review.rating.desc(), Review.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_entity(r) for r in reviews]

    def _to_entity(self, model: Review) -> ReviewEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: Review SQLAlchemy model

        Returns:
            ReviewEntity domain object
        """
        tutor_id = None
        if model.tutor_profile:
            tutor_id = model.tutor_profile.user_id

        return ReviewEntity(
            id=ReviewId(model.id) if model.id else None,
            booking_id=BookingId(model.booking_id),
            student_id=StudentId(model.student_id),
            tutor_id=tutor_id or 0,
            tutor_profile_id=TutorProfileId(model.tutor_profile_id),
            rating=model.rating,
            content=model.comment,
            is_public=model.is_public if model.is_public is not None else True,
            created_at=model.created_at,
            updated_at=None,
            response=None,
            responded_at=None,
            booking_snapshot=model.booking_snapshot,
        )

    def _to_model(self, entity: ReviewEntity) -> Review:
        """
        Convert domain entity to SQLAlchemy model for creation.

        Args:
            entity: ReviewEntity domain object

        Returns:
            Review SQLAlchemy model (for insertion)
        """
        model = Review(
            booking_id=int(entity.booking_id),
            tutor_profile_id=int(entity.tutor_profile_id),
            student_id=int(entity.student_id),
            rating=entity.rating,
            comment=entity.content,
            is_public=entity.is_public,
            booking_snapshot=entity.booking_snapshot,
        )

        if entity.id is not None:
            model.id = int(entity.id)

        return model
