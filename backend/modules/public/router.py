"""
Public Stats Router - Unauthenticated platform statistics.

Provides basic platform metrics for the public homepage without requiring authentication.
Statistics are cached for performance and to prevent database load from unauthenticated requests.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from core.config import Roles
from core.dependencies import DatabaseSession
from models import Booking, Review, TutorProfile, User

router = APIRouter(
    prefix="/public",
    tags=["public"],
    responses={
        200: {"description": "Success"},
    },
)


# ============================================================================
# Response Schemas
# ============================================================================


class PlatformStats(BaseModel):
    """Public platform statistics for homepage display."""

    tutor_count: int  # Number of approved tutors
    student_count: int  # Number of registered students
    average_rating: float  # Platform-wide average tutor rating
    completed_sessions: int  # Total completed sessions
    generated_at: datetime


class FeaturedReview(BaseModel):
    """A featured review for testimonials section."""

    quote: str
    author: str  # First name + last initial
    role: str  # "Student" or context
    rating: int
    initials: str
    tutor_name: str | None = None


class FeaturedReviewsResponse(BaseModel):
    """Response containing featured reviews for testimonials."""

    reviews: list[FeaturedReview]
    total_reviews: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=PlatformStats,
    summary="Get public platform statistics",
    description="""
**Public Platform Statistics**

Returns basic platform metrics for display on the public homepage.
No authentication required.

Metrics include:
- Number of approved tutors
- Number of registered students
- Platform-wide average tutor rating
- Total completed sessions

Statistics are cached and may be slightly delayed from real-time values.
    """,
)
async def get_platform_stats(db: DatabaseSession) -> PlatformStats:
    """Get public platform statistics for homepage display."""

    # Count approved tutors
    tutor_count = (
        db.query(TutorProfile)
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
        )
        .count()
    )

    # Count students
    student_count = (
        db.query(User)
        .filter(
            User.role == Roles.STUDENT,
            User.deleted_at.is_(None),
        )
        .count()
    )

    # Calculate average rating across all approved tutors
    avg_rating = (
        db.query(func.avg(TutorProfile.average_rating))
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
            TutorProfile.average_rating.isnot(None),
        )
        .scalar()
    )

    # Count completed sessions
    completed_sessions = (
        db.query(Booking)
        .filter(
            Booking.session_state == "ENDED",
            Booking.session_outcome == "COMPLETED",
            Booking.deleted_at.is_(None),
        )
        .count()
    )

    return PlatformStats(
        tutor_count=tutor_count,
        student_count=student_count,
        average_rating=round(float(avg_rating), 1) if avg_rating else 0.0,
        completed_sessions=completed_sessions,
        generated_at=datetime.now(UTC),
    )


@router.get(
    "/featured-reviews",
    response_model=FeaturedReviewsResponse,
    summary="Get featured reviews for testimonials",
    description="""
**Featured Reviews for Testimonials**

Returns high-rated reviews for display in the homepage testimonials section.
No authentication required.

Reviews are filtered to:
- Only include 4-5 star ratings
- Only include reviews with meaningful comments
- Protect student privacy (first name + last initial only)

Maximum 4 reviews are returned for homepage display.
    """,
)
async def get_featured_reviews(
    db: DatabaseSession,
    limit: int = Query(default=4, ge=1, le=10, description="Number of reviews to return"),
) -> FeaturedReviewsResponse:
    """Get featured reviews for homepage testimonials."""

    from sqlalchemy.orm import joinedload as jl

    # Get high-rated reviews with comments, eagerly loading reviewer
    # Note: Review uses student_id, not reviewer_id
    reviews = (
        db.query(Review)
        .options(jl(Review.student))
        .join(User, Review.student_id == User.id)
        .filter(
            Review.rating >= 4,
            Review.comment.isnot(None),
            Review.comment != "",
            User.deleted_at.is_(None),
        )
        .order_by(Review.rating.desc(), Review.created_at.desc())
        .limit(limit)
        .all()
    )

    # Get total review count for context
    total_reviews = db.query(Review).count()

    featured_reviews = []
    for review in reviews:
        # Use eagerly loaded reviewer (avoids N+1 query)
        reviewer = review.student
        if not reviewer:
            continue

        # Format name for privacy (First Name + Last Initial)
        first_name = reviewer.first_name or "Student"
        last_initial = (reviewer.last_name[0] + ".") if reviewer.last_name else ""
        author = f"{first_name} {last_initial}".strip()

        # Generate initials
        initials = ""
        if reviewer.first_name:
            initials += reviewer.first_name[0].upper()
        if reviewer.last_name:
            initials += reviewer.last_name[0].upper()
        if not initials:
            initials = "S"

        # Determine role description based on user data
        role = "Student"
        if reviewer.role == "tutor":
            role = "Tutor"

        featured_reviews.append(
            FeaturedReview(
                quote=review.comment[:300] if review.comment else "",  # Limit length
                author=author,
                role=role,
                rating=review.rating,
                initials=initials,
            )
        )

    return FeaturedReviewsResponse(
        reviews=featured_reviews,
        total_reviews=total_reviews,
    )
