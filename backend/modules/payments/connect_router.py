"""
Stripe Connect Router - Tutor Onboarding and Payout Management

Handles:
- Connect account creation for tutors
- Onboarding link generation
- Account status checking
- Payout balance and history
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from core.dependencies import DatabaseSession, TutorUser
from core.stripe_client import (
    create_connect_account,
    create_connect_account_link,
    is_connect_account_ready,
)
from models import TutorProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tutor/connect",
    tags=["tutor-payments"],
)


# ============================================================================
# Response Schemas
# ============================================================================


class ConnectStatusResponse(BaseModel):
    """Connect account status."""
    has_account: bool
    account_id: str | None = None
    is_ready: bool = False
    charges_enabled: bool = False
    payouts_enabled: bool = False
    onboarding_completed: bool = False
    status_message: str


class OnboardingLinkResponse(BaseModel):
    """Onboarding link response."""
    url: str
    expires_at: datetime | None = None


class ConnectDashboardLinkResponse(BaseModel):
    """Express dashboard link response."""
    url: str


class PayoutBalanceResponse(BaseModel):
    """Tutor payout balance."""
    available_cents: int
    pending_cents: int
    currency: str
    next_payout_date: datetime | None = None


class PayoutHistoryItem(BaseModel):
    """Single payout history item."""
    id: str
    amount_cents: int
    currency: str
    status: str
    arrival_date: datetime | None = None
    created_at: datetime


class PayoutHistoryResponse(BaseModel):
    """Payout history response."""
    payouts: list[PayoutHistoryItem]
    total_paid_cents: int


# ============================================================================
# Connect Account Endpoints
# ============================================================================


@router.get(
    "/status",
    response_model=ConnectStatusResponse,
    summary="Get Connect account status",
    description="""
**Check tutor's Stripe Connect account status**

Returns:
- Whether tutor has a Connect account
- Account verification status
- Whether they can receive payouts
    """,
)
async def get_connect_status(
    current_user: TutorUser,
    db: DatabaseSession,
) -> ConnectStatusResponse:
    """Get the current tutor's Connect account status."""

    # Get tutor profile
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found",
        )

    # Check if they have a Connect account
    if not tutor_profile.stripe_account_id:
        return ConnectStatusResponse(
            has_account=False,
            status_message="No payout account connected. Set up your account to receive payments.",
        )

    # Check account status with Stripe
    is_ready, status_message = is_connect_account_ready(tutor_profile.stripe_account_id)

    return ConnectStatusResponse(
        has_account=True,
        account_id=tutor_profile.stripe_account_id,
        is_ready=is_ready,
        charges_enabled=tutor_profile.stripe_charges_enabled or False,
        payouts_enabled=tutor_profile.stripe_payouts_enabled or False,
        onboarding_completed=tutor_profile.stripe_onboarding_completed or False,
        status_message=status_message,
    )


@router.post(
    "/create",
    response_model=OnboardingLinkResponse,
    summary="Create Connect account and get onboarding link",
    description="""
**Create a Stripe Connect Express account for the tutor**

This endpoint:
1. Creates a new Connect Express account
2. Returns an onboarding link to complete setup
3. The tutor completes identity verification on Stripe's hosted page
4. Webhook updates account status when complete
    """,
)
async def create_connect_and_onboard(
    current_user: TutorUser,
    db: DatabaseSession,
    country: Annotated[str, Query(min_length=2, max_length=2, description="Two-letter country code")] = "US",
) -> OnboardingLinkResponse:
    """Create Connect account and return onboarding link."""

    # Get tutor profile
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found. Complete your profile first.",
        )

    # Check if already has account
    if tutor_profile.stripe_account_id:
        # Account exists, just return new onboarding link
        account_link = create_connect_account_link(tutor_profile.stripe_account_id)
        return OnboardingLinkResponse(url=account_link.url)

    # Create new Connect account
    account = create_connect_account(
        tutor_user_id=current_user.id,
        tutor_email=current_user.email,
        country=country.upper(),
    )

    # Save account ID to tutor profile
    tutor_profile.stripe_account_id = account.id
    tutor_profile.updated_at = datetime.now(UTC)
    db.commit()

    # Create onboarding link
    account_link = create_connect_account_link(account.id)

    logger.info(
        f"Created Connect account {account.id} for tutor {current_user.id}"
    )

    return OnboardingLinkResponse(url=account_link.url)


@router.get(
    "/onboarding-link",
    response_model=OnboardingLinkResponse,
    summary="Get new onboarding link",
    description="""
**Get a fresh onboarding link for an existing Connect account**

Use this if the previous link expired or the tutor needs to update their information.
    """,
)
async def get_onboarding_link(
    current_user: TutorUser,
    db: DatabaseSession,
) -> OnboardingLinkResponse:
    """Get a new onboarding link for existing account."""

    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile or not tutor_profile.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Connect account found. Create one first.",
        )

    account_link = create_connect_account_link(tutor_profile.stripe_account_id)

    return OnboardingLinkResponse(url=account_link.url)


@router.get(
    "/dashboard-link",
    response_model=ConnectDashboardLinkResponse,
    summary="Get Express dashboard link",
    description="""
**Get a link to the Stripe Express dashboard**

Tutors can use this to:
- View their payout history
- Update bank account details
- Manage tax information
    """,
)
async def get_dashboard_link(
    current_user: TutorUser,
    db: DatabaseSession,
) -> ConnectDashboardLinkResponse:
    """Get link to Stripe Express dashboard."""

    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile or not tutor_profile.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Connect account found",
        )

    import stripe

    from core.stripe_client import get_stripe_client

    client = get_stripe_client()

    try:
        login_link = client.Account.create_login_link(tutor_profile.stripe_account_id)
        return ConnectDashboardLinkResponse(url=login_link.url)

    except stripe.error.StripeError as e:
        logger.error(f"Error creating dashboard link: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account onboarding not complete. Finish setup first.",
        )


# ============================================================================
# Payout Endpoints
# ============================================================================


@router.get(
    "/balance",
    response_model=PayoutBalanceResponse,
    summary="Get payout balance",
    description="""
**Get tutor's current balance and pending payouts**

Shows:
- Available balance (ready to pay out)
- Pending balance (from recent transactions)
- Next scheduled payout date
    """,
)
async def get_payout_balance(
    current_user: TutorUser,
    db: DatabaseSession,
) -> PayoutBalanceResponse:
    """Get tutor's payout balance."""

    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile or not tutor_profile.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Connect account found",
        )

    import stripe

    from core.stripe_client import get_stripe_client

    client = get_stripe_client()

    try:
        balance = client.Balance.retrieve(
            stripe_account=tutor_profile.stripe_account_id
        )

        # Get primary currency balance
        currency = tutor_profile.currency or "usd"
        available_cents = 0
        pending_cents = 0

        for available in balance.available:
            if available.currency.lower() == currency.lower():
                available_cents = available.amount

        for pending in balance.pending:
            if pending.currency.lower() == currency.lower():
                pending_cents = pending.amount

        return PayoutBalanceResponse(
            available_cents=available_cents,
            pending_cents=pending_cents,
            currency=currency,
            next_payout_date=None,  # Would need to check payout schedule
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve balance",
        )


@router.get(
    "/payouts",
    response_model=PayoutHistoryResponse,
    summary="Get payout history",
    description="""
**Get tutor's payout history**

Returns list of all payouts to their bank account.
    """,
)
async def get_payout_history(
    current_user: TutorUser,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PayoutHistoryResponse:
    """Get tutor's payout history."""

    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile or not tutor_profile.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Connect account found",
        )

    import stripe

    from core.stripe_client import get_stripe_client

    client = get_stripe_client()

    try:
        payouts = client.Payout.list(
            limit=limit,
            stripe_account=tutor_profile.stripe_account_id,
        )

        history = []
        total_paid = 0

        for payout in payouts.data:
            arrival_date = None
            if payout.arrival_date:
                arrival_date = datetime.fromtimestamp(payout.arrival_date, tz=UTC)

            history.append(PayoutHistoryItem(
                id=payout.id,
                amount_cents=payout.amount,
                currency=payout.currency,
                status=payout.status,
                arrival_date=arrival_date,
                created_at=datetime.fromtimestamp(payout.created, tz=UTC),
            ))

            if payout.status == "paid":
                total_paid += payout.amount

        return PayoutHistoryResponse(
            payouts=history,
            total_paid_cents=total_paid,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error getting payout history: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve payout history",
        )


# ============================================================================
# Earnings Summary
# ============================================================================


@router.get(
    "/earnings-summary",
    summary="Get earnings summary",
    description="""
**Get tutor's earnings summary from the platform**

Shows total earnings, platform fees, and net payouts based on completed bookings.
    """,
)
async def get_earnings_summary(
    current_user: TutorUser,
    db: DatabaseSession,
):
    """Get earnings summary from completed bookings."""
    from sqlalchemy import func

    from models import Booking

    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == current_user.id)
        .first()
    )

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found",
        )

    # Get earnings from completed bookings
    result = (
        db.query(
            func.count(Booking.id).label("total_sessions"),
            func.coalesce(func.sum(Booking.rate_cents), 0).label("gross_cents"),
            func.coalesce(func.sum(Booking.platform_fee_cents), 0).label("fees_cents"),
            func.coalesce(func.sum(Booking.tutor_earnings_cents), 0).label("net_cents"),
        )
        .filter(
            Booking.tutor_profile_id == tutor_profile.id,
            Booking.status == "COMPLETED",
        )
        .first()
    )

    # Get commission tier
    from core.currency import get_commission_tier

    lifetime_earnings = int(result.net_cents or 0)
    current_fee_pct, tier_name = get_commission_tier(lifetime_earnings)

    return {
        "total_sessions": result.total_sessions or 0,
        "gross_earnings_cents": int(result.gross_cents or 0),
        "platform_fees_cents": int(result.fees_cents or 0),
        "net_earnings_cents": lifetime_earnings,
        "currency": tutor_profile.currency or "USD",
        "commission_tier": tier_name,
        "current_fee_percentage": float(current_fee_pct),
    }
