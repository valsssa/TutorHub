"""
Wallet Payment Routes

Handles wallet credit top-ups via Stripe Checkout.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from core.rate_limiting import limiter
from sqlalchemy.orm import Session

from core.dependencies import get_current_student_user
from core.stripe_client import create_checkout_session
from database import get_db
from models import Payment, StudentProfile, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallet", tags=["wallet"])


# ============================================================================
# Schemas
# ============================================================================


class WalletCheckoutRequest(BaseModel):
    """Request to create wallet top-up checkout session."""

    amount_cents: int = Field(..., gt=0, le=1000000, description="Amount in cents (max $10,000)")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class WalletCheckoutResponse(BaseModel):
    """Wallet checkout session response."""

    checkout_url: str
    session_id: str
    amount_cents: int
    currency: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/checkout",
    response_model=WalletCheckoutResponse,
    summary="Create wallet top-up checkout session",
    description="""
**Create a Stripe Checkout session for wallet credit top-up**

Creates a secure payment page hosted by Stripe. The student will be redirected
to complete payment, then returned to the wallet page with added credits.

**Requirements:**
- User must be a student
- Amount must be between $0.01 and $10,000

**Flow:**
1. Student selects amount to add
2. Checkout session created
3. Student redirected to Stripe
4. Payment processed
5. Webhook updates student credit balance
6. Student redirected back to wallet page
    """,
)
@limiter.limit("10/minute")
async def create_wallet_checkout(
    request: Request,
    checkout_request: WalletCheckoutRequest,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
) -> WalletCheckoutResponse:
    """Create a Stripe checkout session for wallet top-up."""

    # Verify student profile exists
    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student_profile:
        # Create profile if it doesn't exist
        student_profile = StudentProfile(user_id=current_user.id)
        db.add(student_profile)
        db.commit()
        db.refresh(student_profile)

    # Create checkout session
    session = create_checkout_session(
        booking_id=None,  # No booking for wallet top-ups
        amount_cents=checkout_request.amount_cents,
        currency=checkout_request.currency.lower(),
        tutor_name=None,
        subject_name="Wallet Credit Top-Up",
        success_url=f"{request.headers.get('origin', 'http://localhost:3000')}/wallet?payment=success",
        cancel_url=f"{request.headers.get('origin', 'http://localhost:3000')}/wallet?payment=cancelled",
        customer_email=current_user.email,
        metadata={
            "payment_type": "wallet_topup",
            "student_id": str(current_user.id),
            "student_profile_id": str(student_profile.id),
        },
        tutor_connect_account_id=None,  # Platform keeps 100% for wallet top-ups
    )

    # Create payment record (status: pending)
    payment = Payment(
        booking_id=None,  # Wallet top-ups aren't tied to bookings
        user_id=current_user.id,
        amount_cents=checkout_request.amount_cents,
        currency=checkout_request.currency.lower(),
        status="pending",
        stripe_checkout_session_id=session.id,
        created_at=datetime.now(UTC),
    )
    db.add(payment)
    db.commit()

    logger.info(
        f"Created wallet checkout session {session.id} for student {current_user.id}, "
        f"amount: {checkout_request.amount_cents} {checkout_request.currency}"
    )

    return WalletCheckoutResponse(
        checkout_url=session.url,
        session_id=session.id,
        amount_cents=checkout_request.amount_cents,
        currency=checkout_request.currency,
    )


@router.get(
    "/balance",
    summary="Get wallet balance",
    description="Get current student's wallet credit balance",
)
@limiter.limit("30/minute")
async def get_wallet_balance(
    request: Request,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get student's current wallet balance."""

    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student_profile:
        # Create profile if it doesn't exist
        student_profile = StudentProfile(user_id=current_user.id)
        db.add(student_profile)
        db.commit()
        db.refresh(student_profile)

    return {
        "balance_cents": student_profile.credit_balance_cents or 0,
        "currency": current_user.currency or "USD",
    }
