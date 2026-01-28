"""Reviews API routes."""

import json
import logging
from datetime import UTC
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from core.rate_limiting import limiter

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.audit import AuditLogger
from core.cache import cache_with_ttl, invalidate_cache
from core.dependencies import get_current_student_user
from core.sanitization import sanitize_text_input
from database import get_db
from models import Booking, Review, TutorProfile, User
from schemas import ReviewCreate, ReviewResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@cache_with_ttl(ttl_seconds=300)  # Cache for 5 minutes
def _get_cached_tutor_reviews(db: Session, tutor_id: int, page: int, page_size: int) -> list[Review]:
    """Helper to fetch tutor reviews with caching."""
    offset = (page - 1) * page_size
    return (
        db.query(Review)
        .filter(Review.tutor_profile_id == tutor_id, Review.is_public.is_(True))
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_review(
    request: Request,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Create review for completed booking."""
    try:
        # Verify booking exists and belongs to student
        booking = db.query(Booking).filter(Booking.id == review_data.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if booking.status != "completed":
            raise HTTPException(status_code=400, detail="Can only review completed bookings")

        # Check if review already exists
        existing_review = db.query(Review).filter(Review.booking_id == review_data.booking_id).first()
        if existing_review:
            raise HTTPException(status_code=400, detail="Review already exists")

        # Sanitize comment
        sanitized_comment = None
        if review_data.comment:
            sanitized_comment = sanitize_text_input(review_data.comment, max_length=2000)
            if not sanitized_comment.strip():
                sanitized_comment = None

        # Create booking snapshot - immutable record of what was agreed upon
        booking_snapshot = json.dumps(
            {
                "tutor_name": booking.tutor_name,
                "tutor_title": booking.tutor_title,
                "subject_name": booking.subject_name,
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "hourly_rate": float(booking.hourly_rate),
                "total_amount": float(booking.total_amount),
                "pricing_type": booking.pricing_type,
                "status": booking.status,
                "topic": booking.topic,
            }
        )

        # Create review with decision tracking
        review = Review(
            booking_id=review_data.booking_id,
            tutor_profile_id=booking.tutor_profile_id,
            student_id=current_user.id,
            rating=review_data.rating,
            comment=sanitized_comment,
            booking_snapshot=booking_snapshot,  # Immutable context
        )

        db.add(review)
        db.flush()  # Get review ID without committing

        # Log the review decision in audit trail
        AuditLogger.log_action(
            db=db,
            table_name="reviews",
            record_id=review.id,
            action="INSERT",
            new_data={
                "booking_id": review_data.booking_id,
                "tutor_profile_id": booking.tutor_profile_id,
                "rating": review_data.rating,
                "has_comment": bool(sanitized_comment),
                "decision": "student_reviewed_session",
                "snapshot_captured": True,
            },
            changed_by=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Update tutor average rating and total reviews
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == booking.tutor_profile_id).first()

        if tutor_profile:
            # Calculate new average rating
            avg_rating = (
                db.query(func.avg(Review.rating)).filter(Review.tutor_profile_id == booking.tutor_profile_id).scalar()
            )

            total_reviews = (
                db.query(func.count(Review.id)).filter(Review.tutor_profile_id == booking.tutor_profile_id).scalar()
            )

            tutor_profile.average_rating = Decimal(str(round(float(avg_rating), 2))) if avg_rating else Decimal("0.00")
            tutor_profile.total_reviews = total_reviews or 0

            # Update timestamp in application code (no DB triggers)
            from datetime import datetime

            tutor_profile.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(review)

        logger.info(
            f"Review created: ID {review.id} for tutor {booking.tutor_profile_id} "
            f"by student {current_user.email} with rating {review_data.rating}"
        )

        # Invalidate tutor reviews cache
        invalidate_cache(pattern=f"_get_cached_tutor_reviews_{booking.tutor_profile_id}_")

        return review

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail="Failed to create review")


@router.get("/tutors/{tutor_id}", response_model=list[ReviewResponse])
@limiter.limit("60/minute")
async def get_tutor_reviews(
    request: Request,
    tutor_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Get all reviews for a tutor with pagination and caching."""
    # Verify tutor exists
    tutor = db.query(TutorProfile).filter(TutorProfile.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    try:
        reviews = _get_cached_tutor_reviews(db, tutor_id, page, page_size)
        logger.info(f"Retrieved {len(reviews)} reviews for tutor {tutor_id} (page {page})")
        return reviews
    except Exception as e:
        logger.error(f"Error retrieving tutor reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reviews")
