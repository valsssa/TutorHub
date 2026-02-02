"""Reviews API routes."""

import contextlib
import json
import logging
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.audit import AuditLogger
from core.cache import cache_with_ttl, invalidate_cache
from core.dependencies import get_current_student_user
from core.query_helpers import get_by_id_or_404
from core.rate_limiting import limiter
from core.sanitization import sanitize_text_input
from database import get_db
from models import Booking, Review, TutorProfile, User
from schemas import ReviewCreate, ReviewResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


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
        booking = get_by_id_or_404(db, Booking, review_data.booking_id, detail="Booking not found")
        if booking.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if booking.session_state != "ENDED" or booking.session_outcome != "COMPLETED":
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
                "session_state": booking.session_state,
                "session_outcome": booking.session_outcome,
                "topic": booking.topic,
            }
        )

        # Create review with decision tracking
        review_created_at = datetime.now(UTC)
        review = Review(
            booking_id=review_data.booking_id,
            tutor_profile_id=booking.tutor_profile_id,
            student_id=current_user.id,
            rating=review_data.rating,
            comment=sanitized_comment,
            booking_snapshot=booking_snapshot,
            is_public=True,
            created_at=review_created_at,
        )

        db.add(review)
        db.flush()  # Get review ID for audit log

        # Log the review decision in audit trail (immediate mode to avoid post-commit issues)
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
            immediate=True,  # Write audit log immediately, not deferred
        )

        # Update tutor average rating and total reviews
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == booking.tutor_profile_id).first()

        if tutor_profile:
            # Calculate new average rating (includes the new review after flush)
            avg_rating = (
                db.query(func.avg(Review.rating)).filter(Review.tutor_profile_id == booking.tutor_profile_id).scalar()
            )

            total_reviews = (
                db.query(func.count(Review.id)).filter(Review.tutor_profile_id == booking.tutor_profile_id).scalar()
            )

            tutor_profile.average_rating = Decimal(str(round(float(avg_rating), 2))) if avg_rating else Decimal("0.00")
            tutor_profile.total_reviews = total_reviews or 0
            tutor_profile.updated_at = datetime.now(UTC)

        # Capture values for response and logging
        review_id = review.id
        tutor_profile_id_for_cache = booking.tutor_profile_id
        user_email_for_log = current_user.email

        # Commit all changes
        db.commit()

        # Build response after commit using local variables
        response_data = ReviewResponse(
            id=review_id,
            booking_id=review_data.booking_id,
            tutor_profile_id=tutor_profile_id_for_cache,
            student_id=current_user.id,
            rating=review_data.rating,
            comment=sanitized_comment,
            is_public=True,
            booking_snapshot=booking_snapshot,
            created_at=review_created_at,
        )

        logger.info(
            f"Review created: ID {response_data.id} for tutor {tutor_profile_id_for_cache} "
            f"by student {user_email_for_log} with rating {review_data.rating}"
        )

        # Invalidate tutor reviews cache
        invalidate_cache(pattern=f"_get_cached_tutor_reviews_{tutor_profile_id_for_cache}_")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        # Safely attempt rollback - ignore if session already committed
        with contextlib.suppress(Exception):
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
    get_by_id_or_404(db, TutorProfile, tutor_id, detail="Tutor not found")

    try:
        reviews = _get_cached_tutor_reviews(db, tutor_id, page, page_size)
        logger.info(f"Retrieved {len(reviews)} reviews for tutor {tutor_id} (page {page})")
        return reviews
    except Exception as e:
        logger.error(f"Error retrieving tutor reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reviews")
