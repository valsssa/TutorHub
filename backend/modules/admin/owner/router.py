"""
Owner Analytics Router - Business Intelligence Dashboard

Provides high-level business metrics and KPIs for platform owners.
Requires 'owner' role (highest privilege level).
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import Roles
from core.dependencies import DatabaseSession, OwnerUser
from models import Booking, TutorProfile, User

router = APIRouter(
    prefix="/owner",
    tags=["owner-analytics"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Owner access required"},
    },
)


# ============================================================================
# Response Schemas
# ============================================================================


class RevenueMetrics(BaseModel):
    """Platform revenue metrics."""

    total_gmv_cents: int  # Gross Merchandise Value (total booking value)
    total_platform_fees_cents: int  # Platform's revenue
    total_tutor_payouts_cents: int  # Paid to tutors
    average_booking_value_cents: int
    period_days: int


class GrowthMetrics(BaseModel):
    """User and booking growth metrics."""

    total_users: int
    new_users_period: int
    total_tutors: int
    approved_tutors: int
    total_students: int
    total_bookings: int
    completed_bookings: int
    completion_rate: float  # percentage
    period_days: int


class MarketplaceHealth(BaseModel):
    """Marketplace health indicators."""

    average_tutor_rating: float
    tutors_with_bookings_pct: float  # % of tutors who have at least 1 booking
    repeat_booking_rate: float  # % of students with >1 booking
    cancellation_rate: float
    no_show_rate: float
    average_response_time_hours: float | None


class CommissionTierBreakdown(BaseModel):
    """Commission tier distribution."""

    standard_tutors: int  # 20% tier
    silver_tutors: int  # 15% tier
    gold_tutors: int  # 10% tier
    total_tutors: int


class OwnerDashboard(BaseModel):
    """Complete owner dashboard response."""

    revenue: RevenueMetrics
    growth: GrowthMetrics
    health: MarketplaceHealth
    commission_tiers: CommissionTierBreakdown
    generated_at: datetime


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/dashboard",
    response_model=OwnerDashboard,
    summary="Owner Dashboard - Complete business metrics",
    description="""
**Business Intelligence Dashboard for Platform Owners**

Returns comprehensive metrics including:
- **Revenue**: GMV, platform fees, tutor payouts, average booking value
- **Growth**: User counts, new signups, booking volume
- **Health**: Ratings, completion rates, cancellation rates
- **Commission Tiers**: Distribution of tutors across fee tiers

**Owner Role Required** - This endpoint requires the highest privilege level.
    """,
)
async def get_owner_dashboard(
    owner: OwnerUser,
    db: DatabaseSession,
    period_days: Annotated[int, Query(ge=1, le=365, description="Analysis period in days")] = 30,
) -> OwnerDashboard:
    """Get complete owner dashboard with business metrics."""

    now = datetime.now(UTC)
    period_start = now - timedelta(days=period_days)

    # Revenue metrics
    revenue = _calculate_revenue_metrics(db, period_start, period_days)

    # Growth metrics
    growth = _calculate_growth_metrics(db, period_start, period_days)

    # Health metrics
    health = _calculate_health_metrics(db)

    # Commission tier breakdown
    tiers = _calculate_commission_tiers(db)

    return OwnerDashboard(
        revenue=revenue,
        growth=growth,
        health=health,
        commission_tiers=tiers,
        generated_at=now,
    )


@router.get(
    "/revenue",
    response_model=RevenueMetrics,
    summary="Revenue metrics",
)
async def get_revenue_metrics(
    owner: OwnerUser,
    db: DatabaseSession,
    period_days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> RevenueMetrics:
    """Get platform revenue metrics."""
    period_start = datetime.now(UTC) - timedelta(days=period_days)
    return _calculate_revenue_metrics(db, period_start, period_days)


@router.get(
    "/growth",
    response_model=GrowthMetrics,
    summary="Growth metrics",
)
async def get_growth_metrics(
    owner: OwnerUser,
    db: DatabaseSession,
    period_days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> GrowthMetrics:
    """Get user and booking growth metrics."""
    period_start = datetime.now(UTC) - timedelta(days=period_days)
    return _calculate_growth_metrics(db, period_start, period_days)


@router.get(
    "/health",
    response_model=MarketplaceHealth,
    summary="Marketplace health indicators",
)
async def get_marketplace_health(
    owner: OwnerUser,
    db: DatabaseSession,
) -> MarketplaceHealth:
    """Get marketplace health indicators."""
    return _calculate_health_metrics(db)


@router.get(
    "/commission-tiers",
    response_model=CommissionTierBreakdown,
    summary="Commission tier distribution",
)
async def get_commission_tiers(
    owner: OwnerUser,
    db: DatabaseSession,
) -> CommissionTierBreakdown:
    """Get distribution of tutors across commission tiers."""
    return _calculate_commission_tiers(db)


# ============================================================================
# Helper Functions
# ============================================================================


def _calculate_revenue_metrics(db: Session, period_start: datetime, period_days: int) -> RevenueMetrics:
    """Calculate revenue metrics for the given period."""

    # Get completed bookings in period
    bookings = (
        db.query(Booking)
        .filter(
            Booking.status == "COMPLETED",
            Booking.created_at >= period_start,
        )
        .all()
    )

    total_gmv = sum(b.rate_cents or 0 for b in bookings)
    total_fees = sum(b.platform_fee_cents or 0 for b in bookings)
    total_payouts = sum(b.tutor_earnings_cents or 0 for b in bookings)
    avg_value = total_gmv // len(bookings) if bookings else 0

    return RevenueMetrics(
        total_gmv_cents=total_gmv,
        total_platform_fees_cents=total_fees,
        total_tutor_payouts_cents=total_payouts,
        average_booking_value_cents=avg_value,
        period_days=period_days,
    )


def _calculate_growth_metrics(db: Session, period_start: datetime, period_days: int) -> GrowthMetrics:
    """Calculate growth metrics."""

    # User counts
    total_users = db.query(User).filter(User.deleted_at.is_(None)).count()
    new_users = (
        db.query(User)
        .filter(
            User.created_at >= period_start,
            User.deleted_at.is_(None),
        )
        .count()
    )

    # Role breakdown
    total_tutors = db.query(User).filter(User.role == Roles.TUTOR, User.deleted_at.is_(None)).count()
    approved_tutors = (
        db.query(TutorProfile)
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
        )
        .count()
    )
    total_students = db.query(User).filter(User.role == Roles.STUDENT, User.deleted_at.is_(None)).count()

    # Booking metrics
    total_bookings = db.query(Booking).filter(Booking.deleted_at.is_(None)).count()
    completed_bookings = (
        db.query(Booking)
        .filter(
            Booking.status == "COMPLETED",
            Booking.deleted_at.is_(None),
        )
        .count()
    )

    completion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0

    return GrowthMetrics(
        total_users=total_users,
        new_users_period=new_users,
        total_tutors=total_tutors,
        approved_tutors=approved_tutors,
        total_students=total_students,
        total_bookings=total_bookings,
        completed_bookings=completed_bookings,
        completion_rate=round(completion_rate, 2),
        period_days=period_days,
    )


def _calculate_health_metrics(db: Session) -> MarketplaceHealth:
    """Calculate marketplace health indicators."""

    # Average tutor rating
    avg_rating = (
        db.query(func.avg(TutorProfile.average_rating))
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
        )
        .scalar()
    )

    # Tutors with bookings
    approved_tutors = (
        db.query(TutorProfile)
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
        )
        .count()
    )

    tutors_with_bookings = (
        db.query(func.count(func.distinct(Booking.tutor_profile_id)))
        .filter(Booking.deleted_at.is_(None))
        .scalar()
    )

    tutors_with_bookings_pct = (
        (tutors_with_bookings / approved_tutors * 100) if approved_tutors > 0 else 0
    )

    # Repeat booking rate
    total_students_with_bookings = (
        db.query(func.count(func.distinct(Booking.student_id)))
        .filter(Booking.deleted_at.is_(None))
        .scalar()
    )

    repeat_students = (
        db.query(Booking.student_id)
        .filter(Booking.deleted_at.is_(None))
        .group_by(Booking.student_id)
        .having(func.count(Booking.id) > 1)
        .count()
    )

    repeat_rate = (
        (repeat_students / total_students_with_bookings * 100)
        if total_students_with_bookings > 0
        else 0
    )

    # Cancellation and no-show rates
    total_bookings = db.query(Booking).filter(Booking.deleted_at.is_(None)).count()

    cancelled = (
        db.query(Booking)
        .filter(
            Booking.status.in_(["CANCELLED_BY_STUDENT", "CANCELLED_BY_TUTOR"]),
            Booking.deleted_at.is_(None),
        )
        .count()
    )

    no_shows = (
        db.query(Booking)
        .filter(
            Booking.status.in_(["NO_SHOW_STUDENT", "NO_SHOW_TUTOR"]),
            Booking.deleted_at.is_(None),
        )
        .count()
    )

    cancellation_rate = (cancelled / total_bookings * 100) if total_bookings > 0 else 0
    no_show_rate = (no_shows / total_bookings * 100) if total_bookings > 0 else 0

    # Calculate average response time from response log
    from modules.bookings.services.response_tracking import ResponseTrackingService

    response_service = ResponseTrackingService(db)
    avg_response_time_hours = response_service.get_platform_average_response_time()

    return MarketplaceHealth(
        average_tutor_rating=float(avg_rating or 0),
        tutors_with_bookings_pct=round(tutors_with_bookings_pct, 2),
        repeat_booking_rate=round(repeat_rate, 2),
        cancellation_rate=round(cancellation_rate, 2),
        no_show_rate=round(no_show_rate, 2),
        average_response_time_hours=avg_response_time_hours,
    )


def _calculate_commission_tiers(db: Session) -> CommissionTierBreakdown:
    """Calculate distribution of tutors across commission tiers."""
    from core.currency import get_tutor_lifetime_earnings

    approved_tutors = (
        db.query(TutorProfile)
        .filter(
            TutorProfile.is_approved.is_(True),
            TutorProfile.deleted_at.is_(None),
        )
        .all()
    )

    standard = 0  # < $1,000
    silver = 0  # $1,000 - $4,999
    gold = 0  # $5,000+

    for tutor in approved_tutors:
        earnings = get_tutor_lifetime_earnings(db, tutor.id)

        if earnings >= 500_000:  # $5,000+
            gold += 1
        elif earnings >= 100_000:  # $1,000+
            silver += 1
        else:
            standard += 1

    return CommissionTierBreakdown(
        standard_tutors=standard,
        silver_tutors=silver,
        gold_tutors=gold,
        total_tutors=len(approved_tutors),
    )
