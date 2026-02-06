"""
Stripe Adapter - Implementation of PaymentPort for Stripe.

Wraps the existing stripe_client.py functionality with the PaymentPort interface.
Preserves circuit breaker pattern, idempotency keys, and error handling.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import stripe
from fastapi import HTTPException

from core.config import settings
from core.payment_reliability import (
    CircuitOpenError,
    generate_idempotency_key,
    stripe_circuit_breaker,
)
from core.ports.payment import (
    CheckoutSessionResult,
    ConnectAccountResult,
    PaymentResult,
    PaymentStatus,
    RefundResult,
    WebhookVerificationResult,
)

logger = logging.getLogger(__name__)


class StripeAdapter:
    """
    Stripe implementation of PaymentPort.

    Features:
    - Circuit breaker pattern for resilience
    - Idempotency keys for double-payment prevention
    - Timeout handling and recovery
    - Payout delay for refund protection
    """

    def __init__(self) -> None:
        self._configured = False

    def _ensure_configured(self) -> None:
        """Ensure Stripe is properly configured."""
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=503,
                detail="Payment service not configured. Please contact support.",
            )
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._configured = True

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        metadata: dict[str, Any] | None = None,
        booking_id: int | None = None,
        tutor_connect_account_id: str | None = None,
        platform_fee_cents: int = 0,
    ) -> CheckoutSessionResult:
        """Create a Stripe Checkout session."""
        self._ensure_configured()

        session_params: dict[str, Any] = {
            "payment_method_types": ["card"],
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": description,
                        },
                    },
                    "quantity": 1,
                }
            ],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                **({"booking_id": str(booking_id)} if booking_id else {}),
                **(metadata or {}),
            },
        }

        if customer_email:
            session_params["customer_email"] = customer_email

        if tutor_connect_account_id and booking_id:
            session_params["payment_intent_data"] = {
                "transfer_data": {
                    "destination": tutor_connect_account_id,
                    "amount": amount_cents - platform_fee_cents,
                },
                "metadata": {
                    "booking_id": str(booking_id),
                    "platform_fee_cents": str(platform_fee_cents),
                },
            }

        idempotency_key = generate_idempotency_key(
            "checkout_session",
            amount_cents,
            currency,
            datetime.now(UTC).date().isoformat(),
            booking_id=booking_id,
        )

        try:
            with stripe_circuit_breaker.call():
                session = stripe.checkout.Session.create(
                    **session_params,
                    idempotency_key=idempotency_key,
                )

            logger.info(
                "Created checkout session %s for booking %s",
                session.id,
                booking_id,
            )
            return CheckoutSessionResult(
                success=True,
                session_id=session.id,
                checkout_url=session.url,
            )

        except CircuitOpenError:
            logger.error("Circuit breaker open for Stripe checkout")
            return CheckoutSessionResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.StripeError as e:
            logger.error("Stripe error creating checkout: %s", e)
            return CheckoutSessionResult(
                success=False,
                error_message=str(e),
            )

    def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve a checkout session by ID."""
        self._ensure_configured()

        try:
            with stripe_circuit_breaker.call():
                session = stripe.checkout.Session.retrieve(session_id)
                return {
                    "id": session.id,
                    "payment_status": session.payment_status,
                    "status": session.status,
                    "amount_total": session.amount_total,
                    "currency": session.currency,
                    "customer_email": session.customer_email,
                    "metadata": dict(session.metadata) if session.metadata else {},
                    "payment_intent": session.payment_intent,
                }
        except Exception as e:
            logger.error("Error retrieving checkout session %s: %s", session_id, e)
            raise

    def create_refund(
        self,
        *,
        payment_intent_id: str,
        amount_cents: int | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RefundResult:
        """Process a refund for a payment."""
        self._ensure_configured()

        idempotency_key = generate_idempotency_key(
            "refund",
            payment_intent_id,
            datetime.now(UTC).date().isoformat(),
        )

        refund_params: dict[str, Any] = {
            "payment_intent": payment_intent_id,
            "reason": reason or "requested_by_customer",
            "metadata": metadata or {},
        }

        if amount_cents is not None:
            refund_params["amount"] = amount_cents

        try:
            with stripe_circuit_breaker.call():
                refund = stripe.Refund.create(
                    **refund_params,
                    idempotency_key=idempotency_key,
                )

            logger.info(
                "Created refund %s for payment %s",
                refund.id,
                payment_intent_id,
            )
            return RefundResult(
                success=True,
                refund_id=refund.id,
                amount_cents=refund.amount,
                status=refund.status,
            )

        except CircuitOpenError:
            logger.error("Circuit breaker open for refund")
            return RefundResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.InvalidRequestError as e:
            if "has already been refunded" in str(e).lower():
                existing = self._find_existing_refund(payment_intent_id)
                if existing:
                    return RefundResult(
                        success=True,
                        refund_id=existing.id,
                        amount_cents=existing.amount,
                        status=existing.status,
                        was_existing=True,
                    )
            return RefundResult(
                success=False,
                error_message=str(e),
            )

        except stripe.error.StripeError as e:
            logger.error("Stripe error creating refund: %s", e)
            return RefundResult(
                success=False,
                error_message=str(e),
            )

    def _find_existing_refund(self, payment_intent_id: str) -> stripe.Refund | None:
        """Find an existing refund for a payment intent."""
        try:
            refunds = stripe.Refund.list(payment_intent=payment_intent_id, limit=1)
            return refunds.data[0] if refunds.data else None
        except Exception as e:
            logger.error("Error checking for existing refunds: %s", e)
            return None

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> WebhookVerificationResult:
        """Verify webhook signature and parse event."""
        if not settings.STRIPE_WEBHOOK_SECRET:
            return WebhookVerificationResult(
                valid=False,
                error_message="Webhook not configured",
            )

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
            return WebhookVerificationResult(
                valid=True,
                event_type=event.type,
                event_id=event.id,
                payload=dict(event.data.object) if event.data.object else {},
            )

        except stripe.error.SignatureVerificationError as e:
            logger.warning("Webhook signature verification failed: %s", e)
            return WebhookVerificationResult(
                valid=False,
                error_message="Invalid webhook signature",
            )

        except ValueError as e:
            logger.warning("Invalid webhook payload: %s", e)
            return WebhookVerificationResult(
                valid=False,
                error_message="Invalid webhook payload",
            )

    def create_connect_account(
        self,
        *,
        user_id: int,
        email: str,
        country: str = "US",
    ) -> ConnectAccountResult:
        """Create a Stripe Connect Express account for a tutor."""
        self._ensure_configured()

        idempotency_key = generate_idempotency_key(
            "connect_account",
            country,
            user_id=user_id,
        )

        payout_delay_days = settings.STRIPE_PAYOUT_DELAY_DAYS

        try:
            with stripe_circuit_breaker.call():
                account = stripe.Account.create(
                    type="express",
                    email=email,
                    country=country,
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                    metadata={
                        "tutor_user_id": str(user_id),
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
                "Created Connect account %s for user %s",
                account.id,
                user_id,
            )
            return ConnectAccountResult(
                success=True,
                account_id=account.id,
            )

        except CircuitOpenError:
            return ConnectAccountResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.StripeError as e:
            logger.error("Error creating Connect account: %s", e)
            return ConnectAccountResult(
                success=False,
                error_message=str(e),
            )

    def create_connect_onboarding_link(
        self,
        account_id: str,
        *,
        refresh_url: str,
        return_url: str,
    ) -> ConnectAccountResult:
        """Create an onboarding link for Connect account."""
        self._ensure_configured()

        try:
            with stripe_circuit_breaker.call():
                account_link = stripe.AccountLink.create(
                    account=account_id,
                    refresh_url=refresh_url,
                    return_url=return_url,
                    type="account_onboarding",
                )

            return ConnectAccountResult(
                success=True,
                account_id=account_id,
                onboarding_url=account_link.url,
            )

        except CircuitOpenError:
            return ConnectAccountResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.StripeError as e:
            logger.error("Error creating account link: %s", e)
            return ConnectAccountResult(
                success=False,
                error_message=str(e),
            )

    def get_connect_account_status(self, account_id: str) -> ConnectAccountResult:
        """Get the status of a Connect account."""
        self._ensure_configured()

        try:
            with stripe_circuit_breaker.call():
                account = stripe.Account.retrieve(account_id)

            return ConnectAccountResult(
                success=True,
                account_id=account.id,
                is_ready=account.charges_enabled and account.payouts_enabled,
                charges_enabled=account.charges_enabled,
                payouts_enabled=account.payouts_enabled,
            )

        except CircuitOpenError:
            return ConnectAccountResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.StripeError as e:
            logger.error("Error retrieving Connect account: %s", e)
            return ConnectAccountResult(
                success=False,
                error_message=str(e),
            )

    def create_transfer(
        self,
        *,
        amount_cents: int,
        currency: str,
        destination_account_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Transfer funds to a Connect account."""
        self._ensure_configured()

        booking_id = (metadata or {}).get("booking_id")
        idempotency_key = generate_idempotency_key(
            "transfer",
            amount_cents,
            currency,
            booking_id=booking_id,
        )

        try:
            with stripe_circuit_breaker.call():
                transfer = stripe.Transfer.create(
                    amount=amount_cents,
                    currency=currency.lower(),
                    destination=destination_account_id,
                    metadata=metadata or {},
                    idempotency_key=idempotency_key,
                )

            logger.info(
                "Created transfer %s of %s cents to %s",
                transfer.id,
                amount_cents,
                destination_account_id,
            )
            return PaymentResult(
                success=True,
                payment_id=transfer.id,
                status=PaymentStatus.CAPTURED,
                amount_cents=amount_cents,
                currency=currency,
            )

        except CircuitOpenError:
            return PaymentResult(
                success=False,
                error_message="Payment service temporarily unavailable",
            )

        except stripe.error.StripeError as e:
            logger.error("Error creating transfer: %s", e)
            return PaymentResult(
                success=False,
                error_message=str(e),
            )


# Default instance
stripe_adapter = StripeAdapter()
