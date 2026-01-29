"""
Stripe Connect Router - Tutor Onboarding and Payout Management

Handles:
- Connect account creation for tutors
- Onboarding link generation
- Account status checking
- Payout balance and history
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from core.dependencies import CurrentUser, DatabaseSession, TutorUser
from core.stripe_client import (
    create_connect_account,
    create_connect_account_link,
    is_connect_account_ready,
    update_connect_account_payout_settings,
)
from models import TutorProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tutor/connect",
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


# ============================================================================
# Admin Endpoints - Payout Settings Management
# ============================================================================


class PayoutSettingsUpdateRequest(BaseModel):
    """Request to update payout settings for a tutor."""
    tutor_user_id: int
    delay_days: int | None = None  # None uses system default


class PayoutSettingsUpdateResponse(BaseModel):
    """Response from updating payout settings."""
    tutor_user_id: int
    account_id: str
    delay_days: int
    success: bool
    message: str


class BatchPayoutSettingsResponse(BaseModel):
    """Response from batch payout settings update."""
    total_tutors: int
    updated_count: int
    skipped_count: int
    failed_count: int
    delay_days: int
    results: list[dict]


# Create a separate admin router for these endpoints
admin_connect_router = APIRouter(
    prefix="/admin/connect",
    tags=["admin-payments"],
)


@admin_connect_router.post(
    "/update-payout-settings",
    response_model=PayoutSettingsUpdateResponse,
    summary="Update tutor payout settings (admin only)",
    description="""
**Update payout delay settings for a specific tutor**

SECURITY: This endpoint allows admins to add or modify the payout delay on
a tutor's Connect account. The delay protects against refund scenarios where
a tutor might withdraw funds before a session completes or gets cancelled.

Use this to:
- Add delay to existing tutors who were onboarded before this protection
- Modify delay for specific tutors based on risk assessment
    """,
)
async def admin_update_payout_settings(
    request: PayoutSettingsUpdateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> PayoutSettingsUpdateResponse:
    """Update payout settings for a specific tutor (admin only)."""
    from core.config import Roles, settings

    # Admin only
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Get tutor profile
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == request.tutor_user_id)
        .first()
    )

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor profile not found for user {request.tutor_user_id}",
        )

    if not tutor_profile.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tutor {request.tutor_user_id} does not have a Connect account",
        )

    # Determine delay days
    delay_days = request.delay_days if request.delay_days is not None else settings.STRIPE_PAYOUT_DELAY_DAYS

    try:
        update_connect_account_payout_settings(
            account_id=tutor_profile.stripe_account_id,
            delay_days=delay_days,
        )

        logger.info(
            f"Admin {current_user.id} updated payout settings for tutor {request.tutor_user_id}: "
            f"{delay_days}-day delay"
        )

        return PayoutSettingsUpdateResponse(
            tutor_user_id=request.tutor_user_id,
            account_id=tutor_profile.stripe_account_id,
            delay_days=delay_days,
            success=True,
            message=f"Payout delay set to {delay_days} days",
        )

    except HTTPException as e:
        return PayoutSettingsUpdateResponse(
            tutor_user_id=request.tutor_user_id,
            account_id=tutor_profile.stripe_account_id,
            delay_days=delay_days,
            success=False,
            message=str(e.detail),
        )


@admin_connect_router.post(
    "/batch-update-payout-settings",
    response_model=BatchPayoutSettingsResponse,
    summary="Batch update all tutor payout settings (admin only)",
    description="""
**Update payout delay settings for all tutors with Connect accounts**

SECURITY: Use this endpoint to migrate existing tutors to the secure payout
delay configuration. This is a one-time migration task for tutors who were
onboarded before the payout delay protection was implemented.

The endpoint processes all tutors with Connect accounts and applies the
configured payout delay (default from STRIPE_PAYOUT_DELAY_DAYS setting).

WARNING: This makes API calls for each tutor, so it may take time for
large numbers of tutors. Consider running during low-traffic periods.
    """,
)
async def admin_batch_update_payout_settings(
    current_user: CurrentUser,
    db: DatabaseSession,
    delay_days: Annotated[int | None, Query(description="Override delay days (None uses system default)")] = None,
) -> BatchPayoutSettingsResponse:
    """Batch update payout settings for all tutors (admin only)."""
    from core.config import Roles, settings

    # Admin only
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Determine delay days
    effective_delay = delay_days if delay_days is not None else settings.STRIPE_PAYOUT_DELAY_DAYS

    # Get all tutors with Connect accounts
    tutors_with_accounts = (
        db.query(TutorProfile)
        .filter(TutorProfile.stripe_account_id.isnot(None))
        .all()
    )

    total = len(tutors_with_accounts)
    updated = 0
    skipped = 0
    failed = 0
    results = []

    for tutor in tutors_with_accounts:
        try:
            update_connect_account_payout_settings(
                account_id=tutor.stripe_account_id,
                delay_days=effective_delay,
            )
            updated += 1
            results.append({
                "tutor_user_id": tutor.user_id,
                "account_id": tutor.stripe_account_id,
                "status": "updated",
            })

        except HTTPException as e:
            if "service unavailable" in str(e.detail).lower():
                # Circuit breaker or service issue - stop batch
                failed += 1
                results.append({
                    "tutor_user_id": tutor.user_id,
                    "account_id": tutor.stripe_account_id,
                    "status": "failed",
                    "error": str(e.detail),
                })
                logger.warning(
                    f"Stopping batch update due to service unavailability at tutor {tutor.user_id}"
                )
                break
            else:
                failed += 1
                results.append({
                    "tutor_user_id": tutor.user_id,
                    "account_id": tutor.stripe_account_id,
                    "status": "failed",
                    "error": str(e.detail),
                })

    logger.info(
        f"Admin {current_user.id} batch updated payout settings: "
        f"{updated}/{total} tutors updated with {effective_delay}-day delay"
    )

    return BatchPayoutSettingsResponse(
        total_tutors=total,
        updated_count=updated,
        skipped_count=skipped,
        failed_count=failed,
        delay_days=effective_delay,
        results=results,
    )
