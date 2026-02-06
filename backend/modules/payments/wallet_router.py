"""
Wallet Payment Routes

Handles wallet credit top-ups via Stripe Checkout.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_current_student_user
from core.rate_limiting import limiter
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
        success_url=f"{settings.FRONTEND_URL}/wallet?payment=success",
        cancel_url=f"{settings.FRONTEND_URL}/wallet?payment=cancelled",
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
        student_id=current_user.id,
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


class TransactionResponse(BaseModel):
    """Response model for a single wallet transaction.

    Fields:
        id: Unique transaction identifier
        type: Transaction type (DEPOSIT, WITHDRAWAL, TRANSFER, REFUND, PAYOUT, PAYMENT, FEE)
        amount_cents: Amount in cents (positive for credits, negative for debits)
        currency: ISO 4217 currency code (e.g., USD, EUR)
        description: Human-readable transaction description
        status: Transaction status (PENDING, COMPLETED, FAILED, CANCELLED)
        reference_id: External reference (e.g., Stripe payment intent ID)
        created_at: When the transaction was initiated (ISO 8601 format)
        completed_at: When the transaction completed (ISO 8601 format, null if pending)
    """

    id: int
    type: str
    amount_cents: int
    currency: str
    description: str | None
    status: str
    reference_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Paginated list of wallet transactions.

    Standard pagination response format matching other endpoints.

    Fields:
        items: List of transactions for the current page
        total: Total number of transactions matching the filters
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_pages: Total number of pages available
    """

    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"from_attributes": True}


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


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="Get wallet transactions",
    description="""
**Get paginated list of wallet transactions**

Returns all transactions for the current user's wallet with optional filtering.

**Filters:**
- `type`: Filter by transaction type (DEPOSIT, WITHDRAWAL, REFUND, PAYMENT, FEE, PAYOUT, TRANSFER)
- `status`: Filter by status (PENDING, COMPLETED, FAILED, CANCELLED)
- `from_date`: Start date (inclusive)
- `to_date`: End date (inclusive)
- `page`: Page number (default 1)
- `page_size`: Items per page (default 20, max 100)
    """,
)
@limiter.limit("30/minute")
async def get_wallet_transactions(
    request: Request,
    type: str | None = None,
    status: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """Get paginated wallet transactions for current user."""

    from models import Wallet, WalletTransaction

    # Ensure page_size is within bounds
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)

    # Get or create user's wallet
    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == current_user.id)
        .first()
    )

    if not wallet:
        # No wallet means no transactions
        return TransactionListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )

    # Build base query
    query = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    )

    # Apply filters
    if type:
        query = query.filter(WalletTransaction.type == type.upper())

    if status:
        query = query.filter(WalletTransaction.status == status.upper())

    if from_date:
        query = query.filter(WalletTransaction.created_at >= from_date)

    if to_date:
        query = query.filter(WalletTransaction.created_at <= to_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    offset = (page - 1) * page_size

    # Get transactions ordered by date descending
    transactions = (
        query.order_by(WalletTransaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Convert to response models
    items = [
        TransactionResponse(
            id=t.id,
            type=t.type,
            amount_cents=t.amount_cents,
            currency=t.currency,
            description=t.description,
            status=t.status,
            reference_id=t.reference_id,
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in transactions
    ]

    logger.info(
        f"Retrieved {len(items)} transactions for user {current_user.id}, "
        f"page {page}/{total_pages}"
    )

    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
