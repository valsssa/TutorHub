"""
Stripe Payment Integration Module

Handles all Stripe API interactions including:
- Checkout sessions for booking payments
- Connect account management for tutor payouts
- Webhook event processing
- Refund processing

Features:
- Circuit breaker pattern for resilience
- Idempotency keys for double-payment prevention
- Timeout handling and recovery
- Payout delay for refund protection

SECURITY: Tutor Payout Timing
=============================
This module implements destination charges for Stripe Connect, which means funds
transfer to the tutor's Connect account immediately upon successful payment.

To protect against scenarios where a session is cancelled after payment but the
tutor has already withdrawn funds (leaving the platform to cover the refund), we
configure a payout delay on all tutor Connect accounts.

Configuration: STRIPE_PAYOUT_DELAY_DAYS (default: 7 days)

This delay:
- Holds funds in the tutor's Stripe balance before bank payout
- Gives time for cancellations and refund processing
- Does NOT affect when tutors see earnings (they see it immediately)
- Only affects when they can withdraw to their bank account

The delay is applied:
1. When creating new Connect accounts (create_connect_account)
2. Can be updated for existing accounts (update_connect_account_payout_settings)

Admin endpoints in connect_router.py allow batch migration of existing accounts.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import stripe
from fastapi import HTTPException, status

from core.config import settings
from core.payment_reliability import (
    CircuitOpenError,
    generate_idempotency_key,
    handle_stripe_error,
    stripe_circuit_breaker,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Stripe Client Initialization
# ============================================================================


def _ensure_stripe_configured() -> None:
    """Ensure Stripe is properly configured."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not configured. Please contact support.",
        )


def get_stripe_client() -> stripe:
    """Get configured Stripe client."""
    _ensure_stripe_configured()
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


# ============================================================================
# Checkout Session Management
# ============================================================================


def create_checkout_session(
    booking_id: int | None,
    amount_cents: int,
    currency: str,
    tutor_name: str | None,
    subject_name: str | None,
    student_email: str | None = None,
    session_date: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
    customer_email: str | None = None,
    tutor_connect_account_id: str | None = None,
    platform_fee_cents: int = 0,
    metadata: dict[str, Any] | None = None,
    user_id: int | None = None,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout session for a booking payment or wallet top-up.

    Uses circuit breaker pattern and idempotency keys to prevent:
    - Double charges from retries
    - Cascading failures when Stripe is having issues

    Args:
        booking_id: Internal booking ID (None for wallet top-ups)
        amount_cents: Total amount in cents
        currency: Currency code (e.g., 'usd')
        tutor_name: Tutor display name for receipt (None for wallet top-ups)
        subject_name: Subject being taught or description
        student_email: Student email for receipt (deprecated, use customer_email)
        session_date: Human-readable session date
        success_url: Custom success redirect URL
        cancel_url: Custom cancel redirect URL
        customer_email: Customer email for receipt
        tutor_connect_account_id: Tutor's Stripe Connect account ID (optional)
        platform_fee_cents: Platform fee in cents (for Connect)
        metadata: Additional metadata to store
        user_id: User ID for idempotency key generation

    Returns:
        Stripe Checkout Session object

    Raises:
        HTTPException: If Stripe call fails or circuit breaker is open
    """
    client = get_stripe_client()

    # Support both student_email and customer_email for backwards compatibility
    email = customer_email or student_email

    # Build line item description
    if tutor_name:
        description = f"Tutoring session with {tutor_name}"
        if subject_name:
            description += f" - {subject_name}"
        if session_date:
            description += f" on {session_date}"
        product_name = f"Tutoring Session - {tutor_name}"
    else:
        description = subject_name or "Payment"
        product_name = subject_name or "Payment"

    # Determine URLs
    if booking_id is not None:
        final_success_url = success_url or settings.STRIPE_SUCCESS_URL.format(booking_id=booking_id)
        final_cancel_url = cancel_url or settings.STRIPE_CANCEL_URL.format(booking_id=booking_id)
    else:
        final_success_url = success_url or f"{settings.FRONTEND_URL}/wallet?payment=success"
        final_cancel_url = cancel_url or f"{settings.FRONTEND_URL}/wallet?payment=cancelled"

    # Build session parameters
    session_params: dict[str, Any] = {
        "payment_method_types": ["card"],
        "mode": "payment",
        "line_items": [
            {
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": product_name,
                        "description": description,
                    },
                },
                "quantity": 1,
            }
        ],
        "success_url": final_success_url,
        "cancel_url": final_cancel_url,
        "metadata": {
            **({"booking_id": str(booking_id)} if booking_id else {}),
            "type": "booking_payment" if booking_id else "wallet_topup",
            **(metadata or {}),
        },
    }

    if email:
        session_params["customer_email"] = email

    # If tutor has Connect account, use destination charges
    if tutor_connect_account_id and booking_id:
        session_params["payment_intent_data"] = {
            "transfer_data": {
                "destination": tutor_connect_account_id,
                "amount": amount_cents - platform_fee_cents,  # Tutor receives this
            },
            "metadata": {
                "booking_id": str(booking_id),
                "platform_fee_cents": str(platform_fee_cents),
            },
        }

    # Generate idempotency key to prevent double charges
    # Key is based on booking/user + amount + date to allow legitimate retries
    idempotency_key = generate_idempotency_key(
        "checkout_session",
        amount_cents,
        currency,
        datetime.now(UTC).date().isoformat(),
        booking_id=booking_id,
        user_id=user_id,
    )

    try:
        with stripe_circuit_breaker.call():
            session = client.checkout.Session.create(
                **session_params,
                idempotency_key=idempotency_key,
            )

        logger.info(
            f"Created checkout session {session.id} "
            f"{'for booking ' + str(booking_id) if booking_id else 'for wallet top-up'}, "
            f"amount: {amount_cents} cents"
        )
        return session

    except CircuitOpenError:
        logger.error("Circuit breaker open for Stripe checkout session creation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    except stripe.error.IdempotencyError as e:
        # This means a checkout session with same key exists - retrieve and return it
        logger.warning(f"Idempotency key conflict for checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A checkout session is already being created. Please wait and try again.",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise handle_stripe_error(e)


def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
    """Retrieve a checkout session by ID with circuit breaker protection."""
    client = get_stripe_client()
    try:
        with stripe_circuit_breaker.call():
            return client.checkout.Session.retrieve(session_id)
    except CircuitOpenError:
        logger.error(f"Circuit breaker open when retrieving session {session_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable.",
        )
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving checkout session {session_id}: {e}")
        raise handle_stripe_error(e)


# ============================================================================
# Stripe Connect - Tutor Onboarding
# ============================================================================


def create_connect_account(
    tutor_user_id: int,
    tutor_email: str,
    country: str = "US",
) -> stripe.Account:
    """
    Create a Stripe Connect Express account for a tutor.

    Uses idempotency key based on tutor_user_id to prevent duplicate accounts.

    SECURITY: Payout Delay for Refund Protection
    --------------------------------------------
    With destination charges, funds transfer to the tutor's Connect account immediately
    upon payment. If a session is later cancelled or refunded, the tutor may have already
    withdrawn those funds, leaving the platform to cover the refund from its own balance.

    To mitigate this risk, we configure a payout delay (default: 7 days) which holds funds
    in the tutor's Stripe balance before they can be paid out to their bank account. This
    ensures funds remain available for potential refunds within the cancellation window.

    The delay is configured via STRIPE_PAYOUT_DELAY_DAYS setting.

    Args:
        tutor_user_id: Internal tutor user ID
        tutor_email: Tutor's email address
        country: Two-letter country code

    Returns:
        Stripe Account object
    """
    client = get_stripe_client()

    # Idempotency key ensures we don't create duplicate accounts
    idempotency_key = generate_idempotency_key(
        "connect_account",
        country,
        user_id=tutor_user_id,
    )

    # Get payout delay from settings (default 7 days for refund protection)
    payout_delay_days = settings.STRIPE_PAYOUT_DELAY_DAYS

    try:
        with stripe_circuit_breaker.call():
            account = client.Account.create(
                type="express",
                email=tutor_email,
                country=country,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={
                    "tutor_user_id": str(tutor_user_id),
                    "platform": "edustream",
                },
                settings={
                    "payouts": {
                        "schedule": {
                            "interval": "weekly",
                            "weekly_anchor": "friday",
                            "delay_days": payout_delay_days,
                        },
                    },
                },
                idempotency_key=idempotency_key,
            )

        logger.info(
            f"Created Connect account {account.id} for tutor {tutor_user_id} "
            f"with {payout_delay_days}-day payout delay"
        )
        return account

    except CircuitOpenError:
        logger.error("Circuit breaker open for Connect account creation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Connect account: {e}")
        raise handle_stripe_error(e)


def create_connect_account_link(
    account_id: str,
    refresh_url: str | None = None,
    return_url: str | None = None,
) -> stripe.AccountLink:
    """
    Create an account link for Connect onboarding.

    Args:
        account_id: Stripe Connect account ID
        refresh_url: URL if link expires
        return_url: URL after completion

    Returns:
        Account link with URL for onboarding
    """
    client = get_stripe_client()

    try:
        with stripe_circuit_breaker.call():
            account_link = client.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url or settings.STRIPE_CONNECT_REFRESH_URL,
                return_url=return_url or settings.STRIPE_CONNECT_RETURN_URL,
                type="account_onboarding",
            )

        logger.info(f"Created account link for {account_id}")
        return account_link

    except CircuitOpenError:
        logger.error("Circuit breaker open for account link creation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error creating account link: {e}")
        raise handle_stripe_error(e)


def get_connect_account(account_id: str) -> stripe.Account:
    """Retrieve a Connect account with circuit breaker protection."""
    client = get_stripe_client()

    try:
        with stripe_circuit_breaker.call():
            return client.Account.retrieve(account_id)
    except CircuitOpenError:
        logger.error(f"Circuit breaker open when retrieving account {account_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable.",
        )
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving Connect account {account_id}: {e}")
        raise handle_stripe_error(e)


def update_connect_account_payout_settings(
    account_id: str,
    delay_days: int | None = None,
    interval: str = "weekly",
    weekly_anchor: str = "friday",
) -> stripe.Account:
    """
    Update payout settings for an existing Connect account.

    SECURITY: This function can be used to add payout delays to existing tutor
    accounts that were created before the delay protection was implemented.

    Args:
        account_id: Stripe Connect account ID
        delay_days: Number of days to delay payouts (None uses settings default)
        interval: Payout interval ('daily', 'weekly', 'monthly', 'manual')
        weekly_anchor: Day of week for weekly payouts

    Returns:
        Updated Stripe Account object

    Raises:
        HTTPException: If Stripe call fails
    """
    client = get_stripe_client()

    # Use configured delay if not specified
    if delay_days is None:
        delay_days = settings.STRIPE_PAYOUT_DELAY_DAYS

    try:
        with stripe_circuit_breaker.call():
            account = client.Account.modify(
                account_id,
                settings={
                    "payouts": {
                        "schedule": {
                            "interval": interval,
                            "weekly_anchor": weekly_anchor,
                            "delay_days": delay_days,
                        },
                    },
                },
            )

        logger.info(
            f"Updated Connect account {account_id} payout settings: "
            f"{delay_days}-day delay, {interval} payouts"
        )
        return account

    except CircuitOpenError:
        logger.error(f"Circuit breaker open when updating account {account_id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable.",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error updating Connect account {account_id}: {e}")
        raise handle_stripe_error(e)


def is_connect_account_ready(account_id: str) -> tuple[bool, str]:
    """
    Check if a Connect account is ready to receive payouts.

    Returns:
        (is_ready, status_message)
    """
    try:
        account = get_connect_account(account_id)

        # Check if charges and payouts are enabled
        charges_enabled = account.charges_enabled
        payouts_enabled = account.payouts_enabled
        details_submitted = account.details_submitted

        if charges_enabled and payouts_enabled:
            return True, "Account ready for payouts"

        if not details_submitted:
            return False, "Account onboarding incomplete"

        if not charges_enabled:
            return False, "Account verification pending"

        if not payouts_enabled:
            return False, "Payout setup incomplete"

        return False, "Account setup in progress"

    except HTTPException:
        return False, "Account not found"


# ============================================================================
# Transfers and Payouts
# ============================================================================


def create_transfer_to_tutor(
    amount_cents: int,
    currency: str,
    tutor_connect_account_id: str,
    booking_id: int,
    description: str | None = None,
) -> stripe.Transfer:
    """
    Create a transfer to a tutor's Connect account.

    Used for manual payouts (not destination charges).
    Uses idempotency key to prevent duplicate transfers.

    Args:
        amount_cents: Amount to transfer in cents
        currency: Currency code
        tutor_connect_account_id: Destination Connect account
        booking_id: Associated booking ID
        description: Transfer description

    Returns:
        Stripe Transfer object
    """
    client = get_stripe_client()

    # Idempotency key prevents duplicate transfers for the same booking
    idempotency_key = generate_idempotency_key(
        "transfer",
        amount_cents,
        currency,
        booking_id=booking_id,
    )

    try:
        with stripe_circuit_breaker.call():
            transfer = client.Transfer.create(
                amount=amount_cents,
                currency=currency.lower(),
                destination=tutor_connect_account_id,
                description=description or f"Payout for booking #{booking_id}",
                metadata={
                    "booking_id": str(booking_id),
                    "type": "tutor_payout",
                },
                idempotency_key=idempotency_key,
            )

        logger.info(
            f"Created transfer {transfer.id} of {amount_cents} cents "
            f"to {tutor_connect_account_id} for booking {booking_id}"
        )
        return transfer

    except CircuitOpenError:
        logger.error("Circuit breaker open for transfer creation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Error creating transfer: {e}")
        raise handle_stripe_error(e)


# ============================================================================
# Refunds
# ============================================================================


class RefundResult:
    """Result of a refund operation with additional context."""

    def __init__(
        self,
        refund: stripe.Refund,
        was_existing: bool = False,
    ):
        self.refund = refund
        self.was_existing = was_existing
        self.id = refund.id
        self.amount = refund.amount
        self.status = refund.status


def create_refund(
    payment_intent_id: str,
    booking_id: int | None = None,
    amount_cents: int | None = None,
    reason: str = "requested_by_customer",
    metadata: dict[str, Any] | None = None,
) -> RefundResult:
    """
    Create a refund for a payment with idempotency, circuit breaker, and timeout handling.

    Uses an idempotency key based on booking_id and date to prevent double-refunds.
    If a timeout occurs, checks for existing refunds before raising an error.

    Args:
        payment_intent_id: Stripe PaymentIntent ID
        booking_id: Internal booking ID (used for idempotency key, optional)
        amount_cents: Amount to refund (None for full refund)
        reason: Refund reason code
        metadata: Additional metadata

    Returns:
        RefundResult object containing refund and context

    Raises:
        HTTPException: If refund fails and no existing refund found
    """
    client = get_stripe_client()

    # Generate idempotency key to prevent double-refunds
    # Using booking_id + date ensures same-day retries are safe
    if booking_id:
        idempotency_key = generate_idempotency_key(
            "refund",
            datetime.now(UTC).date().isoformat(),
            booking_id=booking_id,
        )
    else:
        # Fallback for refunds without booking_id
        idempotency_key = generate_idempotency_key(
            "refund",
            payment_intent_id,
            datetime.now(UTC).date().isoformat(),
        )

    refund_params: dict[str, Any] = {
        "payment_intent": payment_intent_id,
        "reason": reason,
        "metadata": metadata or {},
    }

    if amount_cents is not None:
        refund_params["amount"] = amount_cents

    try:
        with stripe_circuit_breaker.call():
            refund = client.Refund.create(
                **refund_params,
                idempotency_key=idempotency_key,
            )

        logger.info(
            f"Created refund {refund.id} for payment {payment_intent_id}, "
            f"booking {booking_id}, amount: {amount_cents or 'full'}"
        )
        return RefundResult(refund=refund, was_existing=False)

    except CircuitOpenError:
        logger.error("Circuit breaker open for refund creation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    except (stripe.error.APIConnectionError, stripe.error.Timeout) as e:
        # Timeout or connection error - refund may or may not have been created
        logger.warning(
            f"Stripe timeout/connection error during refund for booking {booking_id}: {e}"
        )

        # Check if refund was actually created before the timeout
        existing_refund = _find_existing_refund(client, payment_intent_id)
        if existing_refund:
            logger.info(
                f"Found existing refund {existing_refund.id} after timeout "
                f"for booking {booking_id}"
            )
            return RefundResult(refund=existing_refund, was_existing=True)

        # Record failure for circuit breaker
        stripe_circuit_breaker.record_failure(e)

        # No existing refund found - safe to tell user to retry
        logger.error(
            f"Refund timeout for booking {booking_id}, no existing refund found"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please retry in a moment.",
        )

    except stripe.error.IdempotencyError as e:
        # Idempotency conflict - a refund with this key already exists
        logger.warning(
            f"Idempotency conflict for booking {booking_id}: {e}"
        )

        # Retrieve the existing refund
        existing_refund = _find_existing_refund(client, payment_intent_id)
        if existing_refund:
            logger.info(
                f"Returning existing refund {existing_refund.id} "
                f"(idempotency) for booking {booking_id}"
            )
            return RefundResult(refund=existing_refund, was_existing=True)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A refund request is already being processed for this booking.",
        )

    except stripe.error.InvalidRequestError as e:
        # Check if it's because a refund already exists
        if "has already been refunded" in str(e).lower():
            existing_refund = _find_existing_refund(client, payment_intent_id)
            if existing_refund:
                logger.info(
                    f"Payment already refunded, returning existing refund "
                    f"{existing_refund.id} for booking {booking_id}"
                )
                return RefundResult(refund=existing_refund, was_existing=True)

        logger.error(f"Invalid refund request for booking {booking_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund request invalid: {getattr(e, 'user_message', str(e))}",
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating refund for booking {booking_id}: {e}")
        raise handle_stripe_error(e)


def _find_existing_refund(
    client: stripe,
    payment_intent_id: str,
) -> stripe.Refund | None:
    """
    Find an existing refund for a payment intent.

    Args:
        client: Configured Stripe client
        payment_intent_id: Stripe PaymentIntent ID

    Returns:
        Most recent refund if found, None otherwise
    """
    try:
        refunds = client.Refund.list(
            payment_intent=payment_intent_id,
            limit=1,
        )
        if refunds.data:
            return refunds.data[0]
        return None
    except stripe.error.StripeError as e:
        logger.error(f"Error checking for existing refunds: {e}")
        return None


# ============================================================================
# Webhook Signature Verification
# ============================================================================


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify and parse a Stripe webhook event.

    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header value

    Returns:
        Verified Stripe Event object

    Raises:
        HTTPException if verification fails
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook not configured",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
        return event

    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    except ValueError as e:
        logger.warning(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )


# ============================================================================
# Utility Functions
# ============================================================================


def format_amount_for_display(amount_cents: int, currency: str = "usd") -> str:
    """Format cents amount for display."""
    amount = Decimal(amount_cents) / 100
    currency_symbols = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
    }
    symbol = currency_symbols.get(currency.lower(), currency.upper() + " ")
    return f"{symbol}{amount:.2f}"
