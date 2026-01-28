"""
Stripe Payment Integration Module

Handles all Stripe API interactions including:
- Checkout sessions for booking payments
- Connect account management for tutor payouts
- Webhook event processing
- Refund processing
"""

import logging
from decimal import Decimal
from typing import Any

import stripe
from fastapi import HTTPException, status

from core.config import settings

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
    booking_id: int,
    amount_cents: int,
    currency: str,
    tutor_name: str,
    subject_name: str | None,
    session_date: str,
    student_email: str,
    tutor_connect_account_id: str | None = None,
    platform_fee_cents: int = 0,
    metadata: dict[str, Any] | None = None,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout session for a booking payment.

    Args:
        booking_id: Internal booking ID
        amount_cents: Total amount in cents
        currency: Currency code (e.g., 'usd')
        tutor_name: Tutor display name for receipt
        subject_name: Subject being taught
        session_date: Human-readable session date
        student_email: Student email for receipt
        tutor_connect_account_id: Tutor's Stripe Connect account ID (optional)
        platform_fee_cents: Platform fee in cents (for Connect)
        metadata: Additional metadata to store

    Returns:
        Stripe Checkout Session object
    """
    client = get_stripe_client()

    # Build line item description
    description = f"Tutoring session with {tutor_name}"
    if subject_name:
        description += f" - {subject_name}"
    description += f" on {session_date}"

    # Build session parameters
    session_params = {
        "payment_method_types": ["card"],
        "mode": "payment",
        "customer_email": student_email,
        "line_items": [
            {
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Tutoring Session - {tutor_name}",
                        "description": description,
                    },
                },
                "quantity": 1,
            }
        ],
        "success_url": settings.STRIPE_SUCCESS_URL.format(booking_id=booking_id),
        "cancel_url": settings.STRIPE_CANCEL_URL.format(booking_id=booking_id),
        "metadata": {
            "booking_id": str(booking_id),
            "type": "booking_payment",
            **(metadata or {}),
        },
    }

    # If tutor has Connect account, use destination charges
    if tutor_connect_account_id:
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

    try:
        session = client.checkout.Session.create(**session_params)
        logger.info(
            f"Created checkout session {session.id} for booking {booking_id}, "
            f"amount: {amount_cents} cents"
        )
        return session

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service error. Please try again.",
        )


def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
    """Retrieve a checkout session by ID."""
    client = get_stripe_client()
    try:
        return client.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving checkout session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment session not found",
        )


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

    Args:
        tutor_user_id: Internal tutor user ID
        tutor_email: Tutor's email address
        country: Two-letter country code

    Returns:
        Stripe Account object
    """
    client = get_stripe_client()

    try:
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
                    },
                },
            },
        )

        logger.info(f"Created Connect account {account.id} for tutor {tutor_user_id}")
        return account

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Connect account: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create payout account. Please try again.",
        )


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
        account_link = client.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url or settings.STRIPE_CONNECT_REFRESH_URL,
            return_url=return_url or settings.STRIPE_CONNECT_RETURN_URL,
            type="account_onboarding",
        )

        logger.info(f"Created account link for {account_id}")
        return account_link

    except stripe.error.StripeError as e:
        logger.error(f"Error creating account link: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create onboarding link. Please try again.",
        )


def get_connect_account(account_id: str) -> stripe.Account:
    """Retrieve a Connect account."""
    client = get_stripe_client()

    try:
        return client.Account.retrieve(account_id)
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving Connect account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payout account not found",
        )


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

    try:
        transfer = client.Transfer.create(
            amount=amount_cents,
            currency=currency.lower(),
            destination=tutor_connect_account_id,
            description=description or f"Payout for booking #{booking_id}",
            metadata={
                "booking_id": str(booking_id),
                "type": "tutor_payout",
            },
        )

        logger.info(
            f"Created transfer {transfer.id} of {amount_cents} cents "
            f"to {tutor_connect_account_id} for booking {booking_id}"
        )
        return transfer

    except stripe.error.StripeError as e:
        logger.error(f"Error creating transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payout failed. Please contact support.",
        )


# ============================================================================
# Refunds
# ============================================================================


def create_refund(
    payment_intent_id: str,
    amount_cents: int | None = None,
    reason: str = "requested_by_customer",
    metadata: dict[str, Any] | None = None,
) -> stripe.Refund:
    """
    Create a refund for a payment.

    Args:
        payment_intent_id: Stripe PaymentIntent ID
        amount_cents: Amount to refund (None for full refund)
        reason: Refund reason code
        metadata: Additional metadata

    Returns:
        Stripe Refund object
    """
    client = get_stripe_client()

    refund_params = {
        "payment_intent": payment_intent_id,
        "reason": reason,
        "metadata": metadata or {},
    }

    if amount_cents is not None:
        refund_params["amount"] = amount_cents

    try:
        refund = client.Refund.create(**refund_params)
        logger.info(
            f"Created refund {refund.id} for payment {payment_intent_id}, "
            f"amount: {amount_cents or 'full'}"
        )
        return refund

    except stripe.error.StripeError as e:
        logger.error(f"Error creating refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Refund failed. Please contact support.",
        )


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
