"""
Payments Router - Stripe Integration

Handles:
- Checkout session creation for booking payments
- Webhook processing for payment events
- Refund processing
- Payment status queries
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.dependencies import CurrentUser, DatabaseSession
from core.stripe_client import (
    create_checkout_session,
    create_refund,
    format_amount_for_display,
    verify_webhook_signature,
)
from models import Booking, Payment, TutorProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/payments",
    tags=["payments"],
)


# ============================================================================
# Request/Response Schemas
# ============================================================================


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    booking_id: int


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str
    expires_at: datetime | None = None


class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    booking_id: int
    status: str  # pending, paid, failed, refunded
    amount_cents: int
    currency: str
    amount_display: str
    paid_at: datetime | None = None
    stripe_payment_intent_id: str | None = None


class RefundRequest(BaseModel):
    """Refund request."""
    booking_id: int
    reason: str | None = None


class RefundResponse(BaseModel):
    """Refund response."""
    booking_id: int
    refund_id: str
    amount_cents: int
    status: str


# ============================================================================
# Checkout Endpoints
# ============================================================================


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create checkout session",
    description="""
**Create a Stripe Checkout session for a booking payment**

Creates a secure payment page hosted by Stripe. The student will be redirected
to complete payment, then returned to the booking page.

**Requirements:**
- Booking must be in PENDING or CONFIRMED status
- Booking must not already be paid
- Student must own the booking

**Flow:**
1. Call this endpoint with booking_id
2. Redirect user to checkout_url
3. User completes payment on Stripe
4. Webhook updates booking status
5. User returns to success_url
    """,
)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CheckoutResponse:
    """Create a Stripe checkout session for a booking."""

    # Get booking
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify ownership
    if booking.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only pay for your own bookings",
        )

    # Check booking status
    if booking.status not in ["PENDING", "CONFIRMED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for booking with status {booking.status}",
        )

    # Check if already paid
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.booking_id == booking.id,
            Payment.status == "completed",
        )
        .first()
    )
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already paid",
        )

    # Get tutor's Connect account (if they have one)
    tutor_connect_account_id = None
    if booking.tutor_profile:
        tutor_profile = booking.tutor_profile
        # Check if tutor has stripe_account_id (you may need to add this field)
        tutor_connect_account_id = getattr(tutor_profile, 'stripe_account_id', None)

    # Create checkout session
    session = create_checkout_session(
        booking_id=booking.id,
        amount_cents=booking.rate_cents or 0,
        currency=booking.currency or "usd",
        tutor_name=booking.tutor_name or "Tutor",
        subject_name=booking.subject_name,
        session_date=booking.start_time.strftime("%B %d, %Y at %H:%M") if booking.start_time else "TBD",
        student_email=current_user.email,
        tutor_connect_account_id=tutor_connect_account_id,
        platform_fee_cents=booking.platform_fee_cents or 0,
        metadata={
            "student_id": str(current_user.id),
            "tutor_profile_id": str(booking.tutor_profile_id),
        },
    )

    # Store checkout session ID on booking for reference
    booking.stripe_checkout_session_id = session.id
    booking.updated_at = datetime.now(UTC)
    db.commit()

    logger.info(
        f"Created checkout session {session.id} for booking {booking.id}, "
        f"student {current_user.id}"
    )

    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.id,
        expires_at=datetime.fromtimestamp(session.expires_at, tz=UTC) if session.expires_at else None,
    )


@router.get(
    "/status/{booking_id}",
    response_model=PaymentStatusResponse,
    summary="Get payment status",
)
async def get_payment_status(
    booking_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> PaymentStatusResponse:
    """Get the payment status for a booking."""

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check access (student or tutor of booking)
    is_student = booking.student_id == current_user.id
    is_tutor = booking.tutor_profile and booking.tutor_profile.user_id == current_user.id

    if not (is_student or is_tutor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get payment record
    payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
        .first()
    )

    amount_cents = booking.rate_cents or 0
    currency = booking.currency or "usd"

    if payment:
        return PaymentStatusResponse(
            booking_id=booking_id,
            status=payment.status,
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            amount_display=format_amount_for_display(payment.amount_cents, payment.currency),
            paid_at=payment.paid_at,
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
        )

    # No payment record yet
    return PaymentStatusResponse(
        booking_id=booking_id,
        status="pending",
        amount_cents=amount_cents,
        currency=currency,
        amount_display=format_amount_for_display(amount_cents, currency),
        paid_at=None,
        stripe_payment_intent_id=None,
    )


# ============================================================================
# Webhook Endpoint
# ============================================================================


@router.post(
    "/webhook",
    include_in_schema=False,  # Hide from OpenAPI docs for security
)
async def stripe_webhook(
    request: Request,
    db: DatabaseSession,
    stripe_signature: Annotated[str, Header(alias="Stripe-Signature")],
):
    """
    Handle Stripe webhook events.

    Events handled:
    - checkout.session.completed: Payment successful
    - payment_intent.succeeded: Payment confirmed
    - payment_intent.payment_failed: Payment failed
    - charge.refunded: Refund processed
    """

    # Get raw body for signature verification
    payload = await request.body()

    # Verify webhook signature
    event = verify_webhook_signature(payload, stripe_signature)

    event_type = event.type
    event_data = event.data.object

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(db, event_data)

        elif event_type == "payment_intent.succeeded":
            await _handle_payment_succeeded(db, event_data)

        elif event_type == "payment_intent.payment_failed":
            await _handle_payment_failed(db, event_data)

        elif event_type == "charge.refunded":
            await _handle_charge_refunded(db, event_data)

        elif event_type == "account.updated":
            await _handle_account_updated(db, event_data)

        else:
            logger.debug(f"Unhandled webhook event type: {event_type}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
        # Return 200 to prevent Stripe from retrying (we logged the error)
        return {"status": "error", "message": str(e)}


# ============================================================================
# Webhook Handlers
# ============================================================================


async def _handle_checkout_completed(db: Session, session: dict):
    """Handle successful checkout session."""

    metadata = session.get("metadata", {})
    payment_type = metadata.get("payment_type")

    # Handle wallet top-up payments
    if payment_type == "wallet_topup":
        await _handle_wallet_topup(db, session)
        return

    # Handle booking payments
    booking_id = metadata.get("booking_id")

    if not booking_id:
        logger.warning("Checkout completed without booking_id or payment_type in metadata")
        return

    booking = db.query(Booking).filter(Booking.id == int(booking_id)).first()
    if not booking:
        logger.error(f"Booking {booking_id} not found for completed checkout")
        return

    # Create or update payment record
    payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking.id)
        .first()
    )

    if not payment:
        payment = Payment(
            booking_id=booking.id,
            amount_cents=session.get("amount_total", 0),
            currency=session.get("currency", "usd"),
            status="completed",
            stripe_checkout_session_id=session.get("id"),
            stripe_payment_intent_id=session.get("payment_intent"),
            paid_at=datetime.now(UTC),
        )
        db.add(payment)
    else:
        payment.status = "completed"
        payment.stripe_payment_intent_id = session.get("payment_intent")
        payment.paid_at = datetime.now(UTC)

    # Update booking status if pending
    if booking.status == "PENDING":
        booking.status = "CONFIRMED"
        booking.updated_at = datetime.now(UTC)

    db.commit()

    logger.info(f"Payment completed for booking {booking_id}")


async def _handle_payment_succeeded(db: Session, payment_intent: dict):
    """Handle successful payment intent."""

    metadata = payment_intent.get("metadata", {})
    booking_id = metadata.get("booking_id")

    if not booking_id:
        return

    # Update payment record if exists
    payment = (
        db.query(Payment)
        .filter(Payment.stripe_payment_intent_id == payment_intent.get("id"))
        .first()
    )

    if payment:
        payment.status = "completed"
        payment.paid_at = datetime.now(UTC)
        db.commit()

    logger.info(f"Payment intent succeeded for booking {booking_id}")


async def _handle_payment_failed(db: Session, payment_intent: dict):
    """Handle failed payment intent."""

    metadata = payment_intent.get("metadata", {})
    booking_id = metadata.get("booking_id")

    if not booking_id:
        return

    # Update payment record if exists
    payment = (
        db.query(Payment)
        .filter(Payment.stripe_payment_intent_id == payment_intent.get("id"))
        .first()
    )

    if payment:
        payment.status = "failed"
        payment.error_message = payment_intent.get("last_payment_error", {}).get("message")
        db.commit()

    logger.warning(f"Payment failed for booking {booking_id}")


async def _handle_charge_refunded(db: Session, charge: dict):
    """Handle refund event."""

    payment_intent_id = charge.get("payment_intent")
    if not payment_intent_id:
        return

    payment = (
        db.query(Payment)
        .filter(Payment.stripe_payment_intent_id == payment_intent_id)
        .first()
    )

    if payment:
        refund_amount = charge.get("amount_refunded", 0)
        if refund_amount >= payment.amount_cents:
            payment.status = "refunded"
        else:
            payment.status = "partially_refunded"

        payment.refunded_at = datetime.now(UTC)
        payment.refund_amount_cents = refund_amount

        # Update booking status
        if payment.booking:
            payment.booking.status = "REFUNDED"
            payment.booking.updated_at = datetime.now(UTC)

        db.commit()

    logger.info(f"Refund processed for payment intent {payment_intent_id}")


async def _handle_account_updated(db: Session, account: dict):
    """Handle Connect account update (onboarding completion)."""

    account_id = account.get("id")
    if not account_id:
        return

    # Find tutor with this account
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.stripe_account_id == account_id)
        .first()
    )

    if tutor_profile:
        charges_enabled = account.get("charges_enabled", False)
        payouts_enabled = account.get("payouts_enabled", False)

        tutor_profile.stripe_charges_enabled = charges_enabled
        tutor_profile.stripe_payouts_enabled = payouts_enabled
        tutor_profile.updated_at = datetime.now(UTC)

        db.commit()

        logger.info(
            f"Updated Connect status for tutor {tutor_profile.id}: "
            f"charges={charges_enabled}, payouts={payouts_enabled}"
        )


# ============================================================================
# Refund Endpoint
# ============================================================================


@router.post(
    "/refund",
    response_model=RefundResponse,
    summary="Request refund (admin only)",
)
async def request_refund(
    request: RefundRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> RefundResponse:
    """
    Process a refund for a booking.

    Currently admin-only. In the future, may allow automatic refunds
    based on cancellation policy.
    """
    from core.config import Roles

    # Admin only for now
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for refunds",
        )

    # Get booking
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Get payment
    payment = (
        db.query(Payment)
        .filter(
            Payment.booking_id == booking.id,
            Payment.status == "completed",
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed payment found for this booking",
        )

    if not payment.stripe_payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment was not processed through Stripe",
        )

    # Process refund
    refund = create_refund(
        payment_intent_id=payment.stripe_payment_intent_id,
        reason="requested_by_customer",
        metadata={
            "booking_id": str(booking.id),
            "admin_user_id": str(current_user.id),
            "reason": request.reason or "Admin refund",
        },
    )

    # Update payment record
    payment.status = "refunded"
    payment.refunded_at = datetime.now(UTC)
    payment.refund_amount_cents = refund.amount

    # Update booking status
    booking.status = "REFUNDED"
    booking.updated_at = datetime.now(UTC)

    db.commit()

    logger.info(
        f"Refund {refund.id} processed for booking {booking.id} "
        f"by admin {current_user.id}"
    )

    return RefundResponse(
        booking_id=booking.id,
        refund_id=refund.id,
        amount_cents=refund.amount,
        status="succeeded",
    )


async def _handle_wallet_topup(db: Session, session: dict):
    """Handle successful wallet top-up payment."""
    from models import StudentProfile

    metadata = session.get("metadata", {})
    student_id = metadata.get("student_id")
    student_profile_id = metadata.get("student_profile_id")

    if not student_id or not student_profile_id:
        logger.warning("Wallet top-up completed without student_id or student_profile_id in metadata")
        return

    amount_cents = session.get("amount_total", 0)

    # Get student profile
    student_profile = db.query(StudentProfile).filter(StudentProfile.id == int(student_profile_id)).first()
    if not student_profile:
        logger.error(f"StudentProfile {student_profile_id} not found for wallet top-up")
        return

    # Add credits to student balance
    current_balance = student_profile.credit_balance_cents or 0
    student_profile.credit_balance_cents = current_balance + amount_cents
    student_profile.updated_at = datetime.now(UTC)

    # Update payment record
    payment = (
        db.query(Payment)
        .filter(Payment.stripe_checkout_session_id == session.get("id"))
        .first()
    )

    if payment:
        payment.status = "completed"
        payment.stripe_payment_intent_id = session.get("payment_intent")
        payment.paid_at = datetime.now(UTC)

    db.commit()

    logger.info(
        f"Wallet top-up completed for student {student_id}: "
        f"added {amount_cents} cents, new balance: {student_profile.credit_balance_cents}"
    )
