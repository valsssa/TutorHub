"""
Payments Router - Stripe Integration

Handles:
- Checkout session creation for booking payments
- Webhook processing for payment events
- Refund processing
- Payment status queries
- Payment reliability monitoring

Features:
- Circuit breaker pattern for Stripe resilience
- Idempotency keys for double-payment prevention
- Webhook retry tracking
- Payment status polling for timeout recovery

SECURITY: Payout Timing and Refund Protection
=============================================
This module uses Stripe Connect destination charges for tutor payouts. With destination
charges, funds are transferred to the tutor's Connect account balance immediately when
the student pays.

**Risk**: If a session is later cancelled or a refund is needed, the tutor may have
already withdrawn funds from their bank account, forcing the platform to cover the
refund from its own balance.

**Mitigation**: We configure a payout delay (STRIPE_PAYOUT_DELAY_DAYS, default 7 days)
on all tutor Connect accounts. This delay holds funds in the tutor's Stripe balance
before they can be paid out to their bank account. This ensures:

1. Funds remain available for refunds within the cancellation window
2. Platform doesn't have to cover refunds from its own balance
3. Tutors still see their earnings immediately (just can't withdraw yet)

The delay is configured:
- At Connect account creation time (see stripe_client.create_connect_account)
- Can be updated for existing accounts via admin endpoints (see connect_router)

For sessions that complete successfully, the tutor can withdraw after the delay period.
For cancelled/refunded sessions, we can recover the funds from their Stripe balance.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from core.dependencies import CurrentUser, DatabaseSession
from core.payment_reliability import (
    PaymentServiceUnavailable,
    get_payment_reliability_status,
    payment_status_poller,
    webhook_retry_tracker,
)
from core.stripe_client import (
    create_checkout_session,
    create_refund,
    format_amount_for_display,
    retrieve_checkout_session,
    verify_webhook_signature,
)
from models import Booking, Payment, Refund, StudentPackage, StudentProfile, TutorProfile, WebhookEvent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payments",
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
    """Refund request.

    Supports both full and partial refunds. If amount_cents is not provided,
    a full refund of the remaining refundable amount will be processed.
    """

    booking_id: int
    amount_cents: int | None = None
    reason: str | None = None

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_positive(cls, v: int | None) -> int | None:
        """Ensure amount is positive if provided."""
        if v is not None and v <= 0:
            msg = "Refund amount must be positive"
            raise ValueError(msg)
        return v


class RefundResponse(BaseModel):
    """Refund response."""

    booking_id: int
    refund_id: str
    amount_cents: int
    status: str
    total_refunded_cents: int
    remaining_refundable_cents: int


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

    # Check booking status - can only pay for bookings in REQUESTED or SCHEDULED state
    if booking.session_state not in ["REQUESTED", "SCHEDULED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for booking with status {booking.session_state}",
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

    # Check for existing checkout session and handle stale sessions
    if booking.stripe_checkout_session_id:
        try:
            existing_session = retrieve_checkout_session(booking.stripe_checkout_session_id)

            if existing_session.status == "open":
                # Session is still valid, return existing URL
                logger.info(
                    f"Returning existing valid checkout session {existing_session.id} "
                    f"for booking {booking.id}"
                )
                return CheckoutResponse(
                    checkout_url=existing_session.url,
                    session_id=existing_session.id,
                    expires_at=(
                        datetime.fromtimestamp(existing_session.expires_at, tz=UTC)
                        if existing_session.expires_at
                        else None
                    ),
                )

            # Session is expired or completed, clear the stale reference
            logger.info(
                f"Clearing stale checkout session {booking.stripe_checkout_session_id} "
                f"(status: {existing_session.status}) for booking {booking.id}"
            )
            booking.stripe_checkout_session_id = None
            booking.updated_at = datetime.now(UTC)
            db.commit()

        except HTTPException as e:
            # Handle errors from session retrieval
            if e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                # Service unavailable (circuit breaker open) - re-raise
                raise

            # For other errors (502 from InvalidRequestError, etc.),
            # the session is likely invalid - clear reference and create new
            logger.warning(
                f"Checkout session {booking.stripe_checkout_session_id} not found "
                f"or invalid for booking {booking.id} (status: {e.status_code}), "
                f"clearing reference and creating new session"
            )
            booking.stripe_checkout_session_id = None
            booking.updated_at = datetime.now(UTC)
            db.commit()

    # Get tutor's Connect account (if they have one and it's fully verified)
    # SECURITY NOTE: When tutor_connect_account_id is set, we use destination charges.
    # Funds transfer to the tutor's Stripe balance immediately upon payment.
    # To protect against refunds, tutor Connect accounts have a payout delay
    # (configured via STRIPE_PAYOUT_DELAY_DAYS) that holds funds before bank payout.
    # See module docstring for full security documentation.
    tutor_connect_account_id = None
    if booking.tutor_profile:
        tutor_profile = booking.tutor_profile
        stripe_account_id = getattr(tutor_profile, 'stripe_account_id', None)

        if stripe_account_id:
            # Check if Connect account is fully verified with payouts enabled
            payouts_enabled = getattr(tutor_profile, 'stripe_payouts_enabled', False)
            charges_enabled = getattr(tutor_profile, 'stripe_charges_enabled', False)

            if payouts_enabled and charges_enabled:
                tutor_connect_account_id = stripe_account_id
            else:
                # Tutor has Connect account but it's not fully onboarded
                # Funds will be held on platform until tutor completes verification
                logger.warning(
                    f"Tutor {tutor_profile.id} (user_id={tutor_profile.user_id}) has Connect "
                    f"account {stripe_account_id} but payouts_enabled={payouts_enabled}, "
                    f"charges_enabled={charges_enabled}. Creating payment without destination "
                    f"transfer - funds will be held on platform for admin review."
                )

    # Create checkout session (uses destination charges if tutor has verified Connect account)
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


class CheckoutSuccessResponse(BaseModel):
    """Response for checkout success redirect."""

    status: str  # success, processing, failed
    booking_id: int
    message: str
    payment_confirmed: bool = False


@router.get(
    "/checkout/success",
    response_model=CheckoutSuccessResponse,
    summary="Handle checkout success redirect",
    description="""
**Handle return from Stripe checkout**

This endpoint handles the user redirect after completing Stripe checkout.
It gracefully handles the race condition where the webhook may process
before or after the user returns.

**States handled:**
- Payment already confirmed (webhook processed first) - returns success
- Payment pending but Stripe shows paid (webhook slow) - returns success with finalization message
- Payment still processing - returns processing status
- Payment failed - returns failed status

**Note:** This endpoint should be called with the session_id query parameter
that Stripe includes in the success_url redirect.
    """,
)
async def checkout_success(
    session_id: Annotated[str, Query(description="Stripe checkout session ID")],
    db: DatabaseSession,
) -> CheckoutSuccessResponse:
    """
    Handle return from Stripe checkout - may be called before or after webhook.

    This provides a graceful UX regardless of webhook timing by checking both
    the local database state and Stripe's actual payment status.
    """
    from modules.bookings.domain.status import PaymentState

    # Find booking by checkout session ID
    booking = (
        db.query(Booking)
        .filter(Booking.stripe_checkout_session_id == session_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found for this checkout session",
        )

    # Check current payment state - webhook may have already processed
    if booking.payment_state in [PaymentState.AUTHORIZED.value, PaymentState.CAPTURED.value]:
        # Webhook already processed - return success
        logger.info(
            f"Checkout success for booking {booking.id}: "
            f"payment already confirmed (state={booking.payment_state})"
        )
        return CheckoutSuccessResponse(
            status="success",
            booking_id=booking.id,
            message="Payment confirmed",
            payment_confirmed=True,
        )

    if booking.payment_state == PaymentState.PENDING.value:
        # Webhook hasn't arrived yet - check with Stripe directly
        try:
            stripe_session = retrieve_checkout_session(session_id)

            if stripe_session.payment_status == "paid":
                # Payment succeeded at Stripe, webhook just slow - return success anyway
                # The webhook will update the database when it arrives
                logger.info(
                    f"Checkout success for booking {booking.id}: "
                    f"Stripe confirms paid, webhook pending"
                )
                return CheckoutSuccessResponse(
                    status="success",
                    booking_id=booking.id,
                    message="Payment confirmed, finalizing...",
                    payment_confirmed=True,
                )

            if stripe_session.status == "expired":
                logger.warning(
                    f"Checkout session {session_id} expired for booking {booking.id}"
                )
                return CheckoutSuccessResponse(
                    status="failed",
                    booking_id=booking.id,
                    message="Checkout session expired. Please try again.",
                    payment_confirmed=False,
                )

            # Still processing (unpaid, or session open but not completed)
            logger.info(
                f"Checkout for booking {booking.id} still processing: "
                f"session_status={stripe_session.status}, "
                f"payment_status={stripe_session.payment_status}"
            )
            return CheckoutSuccessResponse(
                status="processing",
                booking_id=booking.id,
                message="Payment is being processed...",
                payment_confirmed=False,
            )

        except HTTPException as e:
            # Stripe service unavailable or session not found
            logger.error(
                f"Error checking Stripe session {session_id} for booking {booking.id}: "
                f"status={e.status_code}, detail={e.detail}"
            )
            # Return processing status since we can't confirm either way
            return CheckoutSuccessResponse(
                status="processing",
                booking_id=booking.id,
                message="Verifying payment status...",
                payment_confirmed=False,
            )

    # Failed or other terminal states
    if booking.payment_state in [PaymentState.VOIDED.value, PaymentState.REFUNDED.value]:
        return CheckoutSuccessResponse(
            status="failed",
            booking_id=booking.id,
            message="Payment was cancelled or refunded",
            payment_confirmed=False,
        )

    # Unknown state - return processing to be safe
    logger.warning(
        f"Checkout success called for booking {booking.id} with "
        f"unexpected payment_state={booking.payment_state}"
    )
    return CheckoutSuccessResponse(
        status="processing",
        booking_id=booking.id,
        message="Verifying payment status...",
        payment_confirmed=False,
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

    Idempotency:
    - Each event is tracked by stripe_event_id to prevent duplicate processing
    - Returns success for already-processed events

    Reliability:
    - Tracks retry attempts for monitoring
    - Provides detailed error logging
    """

    # Get raw body for signature verification
    payload = await request.body()

    # Verify webhook signature
    event = verify_webhook_signature(payload, stripe_signature)

    event_type = event.type
    event_id = event.id
    event_data = event.data.object

    logger.info(f"Received Stripe webhook: {event_type} (event_id: {event_id})")

    # Track this webhook attempt for monitoring (before idempotency check)
    retry_info = webhook_retry_tracker.record_attempt(
        event_id=event_id,
        event_type=event_type,
        processed=False,
    )

    if retry_info.attempt_count > 1:
        logger.warning(
            f"Webhook {event_id} received {retry_info.attempt_count} times "
            f"(first: {retry_info.first_received_at.isoformat()})"
        )

    # Check if event was already processed (idempotency check)
    existing_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.stripe_event_id == event_id)
        .first()
    )
    if existing_event:
        logger.info(f"Webhook event {event_id} already processed, skipping")
        # Update tracker to mark as processed
        webhook_retry_tracker.record_attempt(
            event_id=event_id,
            event_type=event_type,
            processed=True,
        )
        return {"status": "already_processed"}

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

        # Record successful processing of this event
        webhook_event = WebhookEvent(
            stripe_event_id=event_id,
            event_type=event_type,
        )
        db.add(webhook_event)
        db.commit()

        # Update retry tracker to mark as processed
        webhook_retry_tracker.record_attempt(
            event_id=event_id,
            event_type=event_type,
            processed=True,
        )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)

        # Track the error in retry tracker
        webhook_retry_tracker.record_attempt(
            event_id=event_id,
            event_type=event_type,
            processed=False,
            error_message=str(e),
        )

        # Return 200 to prevent Stripe from retrying (we logged the error)
        # Note: For transient errors, you might want to return 5xx to trigger retry
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

    # Check for package expiration during checkout (MEDIUM severity race condition fix)
    # If a booking was made with a package, but the package expired during the checkout
    # process, we honor the booking since payment was made in good faith.
    package_expired_during_checkout = False
    if booking.package_id:
        package = (
            db.query(StudentPackage)
            .filter(StudentPackage.id == booking.package_id)
            .first()
        )

        if package:
            now = datetime.now(UTC)
            if package.expires_at and package.expires_at < now:
                # Package expired during checkout - honor the booking anyway
                package_expired_during_checkout = True
                logger.warning(
                    f"Package {package.id} expired during checkout for booking {booking_id}. "
                    f"Package expired at {package.expires_at.isoformat()}, current time {now.isoformat()}. "
                    f"Honoring booking as payment was made in good faith."
                )
            elif package.status != "active":
                # Package status changed during checkout (e.g., marked expired by scheduler)
                package_expired_during_checkout = True
                logger.warning(
                    f"Package {package.id} status changed to '{package.status}' during checkout "
                    f"for booking {booking_id}. Honoring booking as payment was made in good faith."
                )

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

    # Update booking state if requested (await tutor confirmation)
    if booking.session_state == "REQUESTED":
        booking.session_state = "SCHEDULED"
        booking.updated_at = datetime.now(UTC)

    db.commit()

    if package_expired_during_checkout:
        logger.info(
            f"Payment completed for booking {booking_id} "
            f"(package expired during checkout - honored)"
        )
    else:
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

        # Update booking payment state
        if payment.booking:
            payment.booking.payment_state = "REFUNDED"
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

    Supports both full and partial refunds. Validates that cumulative refunds
    do not exceed the original payment amount.

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

    # Get payment - allow refunds on completed or partially_refunded payments
    payment = (
        db.query(Payment)
        .filter(
            Payment.booking_id == booking.id,
            Payment.status.in_(["completed", "partially_refunded"]),
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

    # Calculate total already refunded for this payment
    total_refunded: int = (
        db.query(func.coalesce(func.sum(Refund.amount_cents), 0))
        .filter(Refund.payment_id == payment.id)
        .scalar()
    )

    # Calculate maximum refundable amount
    max_refundable = payment.amount_cents - total_refunded

    if max_refundable <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has already been fully refunded",
        )

    # Determine refund amount
    if request.amount_cents is None:
        # Full refund of remaining amount
        refund_amount_cents = max_refundable
    else:
        refund_amount_cents = request.amount_cents

    # Validate refund amount doesn't exceed remaining refundable amount
    if refund_amount_cents > max_refundable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Refund amount ({refund_amount_cents} cents) exceeds "
                f"remaining refundable amount ({max_refundable} cents). "
                f"Original payment: {payment.amount_cents} cents, "
                f"already refunded: {total_refunded} cents."
            ),
        )

    # Map reason to valid Refund model enum value
    reason_mapping = {
        "student_cancel": "STUDENT_CANCEL",
        "tutor_cancel": "TUTOR_CANCEL",
        "no_show_tutor": "NO_SHOW_TUTOR",
        "goodwill": "GOODWILL",
    }
    refund_reason = reason_mapping.get(
        (request.reason or "").lower().replace(" ", "_"), "OTHER"
    )

    # Process refund through Stripe with idempotency key and timeout handling
    # The create_refund function handles:
    # - Idempotency key to prevent double-refunds on retry
    # - Timeout recovery by checking for existing refunds
    # - Graceful error handling
    refund_result = create_refund(
        payment_intent_id=payment.stripe_payment_intent_id,
        booking_id=booking.id,
        amount_cents=refund_amount_cents,
        reason="requested_by_customer",
        metadata={
            "booking_id": str(booking.id),
            "admin_user_id": str(current_user.id),
            "reason": request.reason or "Admin refund",
        },
    )

    # Log if we found an existing refund (timeout recovery or duplicate request)
    if refund_result.was_existing:
        logger.warning(
            f"Used existing refund {refund_result.id} for booking {booking.id} "
            f"(possibly from timeout recovery or duplicate request)"
        )

    # Create Refund record to track this refund
    refund_record = Refund(
        payment_id=payment.id,
        booking_id=booking.id,
        amount_cents=refund_result.amount,
        currency=payment.currency,
        reason=refund_reason,
        provider_refund_id=refund_result.id,
        refund_metadata={
            "admin_user_id": current_user.id,
            "reason_text": request.reason or "Admin refund",
            "was_existing_refund": refund_result.was_existing,
        },
    )
    db.add(refund_record)

    # Calculate new totals using the actual refund amount from Stripe
    # This ensures accuracy even if an existing refund was recovered
    new_total_refunded = total_refunded + refund_result.amount
    new_remaining_refundable = payment.amount_cents - new_total_refunded

    # Update payment record
    if new_remaining_refundable == 0:
        payment.status = "refunded"
    else:
        payment.status = "partially_refunded"

    payment.refunded_at = datetime.now(UTC)
    payment.refund_amount_cents = new_total_refunded

    # Update booking payment state only for full refunds
    if new_remaining_refundable == 0:
        booking.payment_state = "REFUNDED"
        booking.updated_at = datetime.now(UTC)

        # Restore package credit if this was a package booking (only on full refund)
        if booking.package_id:
            from modules.bookings.service import BookingService

            service = BookingService(db)
            restored = service._restore_package_credit(booking.package_id)
            if restored:
                logger.info(
                    f"Restored package credit for booking {booking.id}, "
                    f"package {booking.package_id}"
                )

    db.commit()

    logger.info(
        f"Refund {refund_result.id} processed for booking {booking.id} "
        f"by admin {current_user.id}: {refund_result.amount} cents "
        f"(total refunded: {new_total_refunded}/{payment.amount_cents} cents)"
    )

    return RefundResponse(
        booking_id=booking.id,
        refund_id=refund_result.id,
        amount_cents=refund_result.amount,
        status=refund_result.status,
        total_refunded_cents=new_total_refunded,
        remaining_refundable_cents=new_remaining_refundable,
    )


async def _handle_wallet_topup(db: Session, session: dict):
    """Handle successful wallet top-up payment."""
    metadata = session.get("metadata", {})
    student_id = metadata.get("student_id")
    student_profile_id = metadata.get("student_profile_id")

    if not student_id or not student_profile_id:
        logger.warning("Wallet top-up completed without student_id or student_profile_id in metadata")
        return

    amount_cents = session.get("amount_total", 0)

    # Verify student profile exists
    student_profile = db.query(StudentProfile).filter(StudentProfile.id == int(student_profile_id)).first()
    if not student_profile:
        logger.error(f"StudentProfile {student_profile_id} not found for wallet top-up")
        return

    # Add credits to student balance using atomic SQL UPDATE to prevent race conditions
    # This ensures concurrent top-ups don't lose money due to read-modify-write patterns
    db.execute(
        update(StudentProfile)
        .where(StudentProfile.id == int(student_profile_id))
        .values(
            credit_balance_cents=StudentProfile.credit_balance_cents + amount_cents,
            updated_at=datetime.now(UTC),
        )
    )

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

    # Refresh to get updated balance for logging
    db.refresh(student_profile)

    logger.info(
        f"Wallet top-up completed for student {student_id}: "
        f"added {amount_cents} cents, new balance: {student_profile.credit_balance_cents}"
    )


# ============================================================================
# Payment Status Polling (Timeout Recovery)
# ============================================================================


class PollPaymentStatusResponse(BaseModel):
    """Response from polling payment status directly from Stripe."""

    booking_id: int
    checkout_session_id: str | None
    payment_intent_id: str | None
    stripe_status: str
    paid: bool
    refunded: bool
    amount_cents: int
    currency: str
    last_checked: datetime
    synced_with_db: bool
    error: str | None = None


@router.get(
    "/poll/{booking_id}",
    response_model=PollPaymentStatusResponse,
    summary="Poll payment status from Stripe",
    description="""
**Poll Stripe directly for payment status**

Use this endpoint when a webhook may have been missed (e.g., after timeout).
This checks the actual status with Stripe and optionally syncs the database.

**Use cases:**
- User returned from checkout but status not updated
- Webhook delivery suspected to have failed
- Manual reconciliation

**Note:** This endpoint may be slower than /status/{booking_id} as it
queries Stripe directly. Use sparingly.
    """,
)
async def poll_payment_status(
    booking_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
    sync: Annotated[bool, Query(description="Sync database with Stripe status")] = False,
) -> PollPaymentStatusResponse:
    """Poll Stripe directly for payment status and optionally sync database."""
    from core.config import Roles

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check access (student, tutor, or admin)
    is_student = booking.student_id == current_user.id
    is_tutor = booking.tutor_profile and booking.tutor_profile.user_id == current_user.id
    is_admin = Roles.has_admin_access(current_user.role)

    if not (is_student or is_tutor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get checkout session ID
    session_id = booking.stripe_checkout_session_id
    if not session_id:
        return PollPaymentStatusResponse(
            booking_id=booking_id,
            checkout_session_id=None,
            payment_intent_id=None,
            stripe_status="no_checkout_session",
            paid=False,
            refunded=False,
            amount_cents=booking.rate_cents or 0,
            currency=booking.currency or "usd",
            last_checked=datetime.now(UTC),
            synced_with_db=False,
            error="No checkout session found for this booking",
        )

    # Poll Stripe
    try:
        status_info = payment_status_poller.check_checkout_session(session_id)
    except PaymentServiceUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    synced = False

    # Optionally sync database with Stripe status
    if sync and status_info.paid and not status_info.error:
        # Check if we need to update the database
        payment = (
            db.query(Payment)
            .filter(Payment.booking_id == booking_id)
            .first()
        )

        if not payment or payment.status != "completed":
            # Create or update payment record
            if not payment:
                payment = Payment(
                    booking_id=booking.id,
                    amount_cents=status_info.amount_cents,
                    currency=status_info.currency,
                    status="completed",
                    stripe_checkout_session_id=session_id,
                    stripe_payment_intent_id=status_info.payment_intent_id,
                    paid_at=datetime.now(UTC),
                )
                db.add(payment)
            else:
                payment.status = "completed"
                payment.stripe_payment_intent_id = status_info.payment_intent_id
                payment.paid_at = datetime.now(UTC)

            # Update booking state if needed
            if booking.session_state == "REQUESTED":
                booking.session_state = "SCHEDULED"
                booking.updated_at = datetime.now(UTC)

            db.commit()
            synced = True

            logger.info(
                f"Synced payment status for booking {booking_id} from Stripe poll: "
                f"status={status_info.status}, paid={status_info.paid}"
            )

    return PollPaymentStatusResponse(
        booking_id=booking_id,
        checkout_session_id=session_id,
        payment_intent_id=status_info.payment_intent_id,
        stripe_status=status_info.status,
        paid=status_info.paid,
        refunded=status_info.refunded,
        amount_cents=status_info.amount_cents,
        currency=status_info.currency,
        last_checked=status_info.last_checked,
        synced_with_db=synced,
        error=status_info.error,
    )


# ============================================================================
# Payment Reliability Monitoring (Admin Only)
# ============================================================================


@router.get(
    "/reliability/status",
    summary="Get payment reliability status (admin only)",
    description="""
**Get payment system reliability status**

Returns:
- Circuit breaker state and metrics
- Webhook retry statistics
- Overall system health

Useful for monitoring and debugging payment issues.
    """,
)
async def get_reliability_status(
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Get payment reliability status for monitoring."""
    from core.config import Roles

    # Admin only
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return get_payment_reliability_status()


@router.get(
    "/reliability/problematic-webhooks",
    summary="Get problematic webhooks (admin only)",
    description="""
**Get webhooks that have been retried multiple times**

Returns events that Stripe has delivered multiple times, which may
indicate processing failures or issues.
    """,
)
async def get_problematic_webhooks(
    current_user: CurrentUser,
    min_attempts: Annotated[int, Query(ge=2, le=10)] = 3,
) -> list[dict[str, Any]]:
    """Get webhooks that have been retried multiple times."""
    from core.config import Roles

    # Admin only
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    problematic = webhook_retry_tracker.get_problematic_events(min_attempts)

    return [
        {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "first_received_at": e.first_received_at.isoformat(),
            "last_received_at": e.last_received_at.isoformat(),
            "attempt_count": e.attempt_count,
            "processed": e.processed,
            "error_message": e.error_message,
        }
        for e in problematic
    ]
