"""
Payment Port - Interface for payment processing.

This port defines the contract for payment operations, abstracting away
the specific payment provider (Stripe, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class PaymentStatus(str, Enum):
    """Status of a payment operation."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PaymentResult:
    """Result of a payment operation."""

    success: bool
    payment_id: str | None = None
    status: PaymentStatus = PaymentStatus.PENDING
    amount_cents: int = 0
    currency: str = "USD"
    error_message: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    was_existing: bool = False  # True if operation found existing record (idempotency)


@dataclass(frozen=True)
class CheckoutSessionResult:
    """Result of creating a checkout session."""

    success: bool
    session_id: str | None = None
    checkout_url: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class RefundResult:
    """Result of a refund operation."""

    success: bool
    refund_id: str | None = None
    amount_cents: int = 0
    status: str = "pending"
    error_message: str | None = None
    was_existing: bool = False  # True if refund already existed (timeout recovery)

    # Alias for backwards compatibility
    @property
    def id(self) -> str | None:
        return self.refund_id

    @property
    def amount(self) -> int:
        return self.amount_cents


@dataclass(frozen=True)
class WebhookVerificationResult:
    """Result of webhook signature verification."""

    valid: bool
    event_type: str | None = None
    event_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass(frozen=True)
class ConnectAccountResult:
    """Result of Connect account operations."""

    success: bool
    account_id: str | None = None
    onboarding_url: str | None = None
    is_ready: bool = False
    charges_enabled: bool = False
    payouts_enabled: bool = False
    error_message: str | None = None


class PaymentPort(Protocol):
    """
    Protocol for payment processing operations.

    Implementations should handle:
    - Idempotency to prevent double charges
    - Error categorization (transient vs permanent)
    - Retry logic for transient failures
    - Timeout handling
    """

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
        """
        Create a checkout session for payment.

        Args:
            amount_cents: Total amount in cents
            currency: Currency code (e.g., "usd")
            description: Description shown to customer
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            customer_email: Customer email for receipt
            metadata: Additional metadata to store
            booking_id: Associated booking ID
            tutor_connect_account_id: Tutor's Connect account for payouts
            platform_fee_cents: Platform fee to collect

        Returns:
            CheckoutSessionResult with session_id and checkout_url
        """
        ...

    def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        """
        Retrieve details of a checkout session.

        Args:
            session_id: The checkout session ID

        Returns:
            Session details including payment status
        """
        ...

    def create_refund(
        self,
        *,
        payment_intent_id: str,
        amount_cents: int | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RefundResult:
        """
        Process a refund for a payment.

        Args:
            payment_intent_id: The original payment intent ID
            amount_cents: Amount to refund (None for full refund)
            reason: Reason for refund
            metadata: Additional metadata

        Returns:
            RefundResult with refund details
        """
        ...

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> WebhookVerificationResult:
        """
        Verify webhook signature and parse event.

        Args:
            payload: Raw webhook payload bytes
            signature: Webhook signature header

        Returns:
            WebhookVerificationResult with event details if valid
        """
        ...

    def create_connect_account(
        self,
        *,
        user_id: int,
        email: str,
        country: str = "US",
    ) -> ConnectAccountResult:
        """
        Create a Connect account for a tutor.

        Args:
            user_id: Internal user ID
            email: Tutor's email
            country: Country code

        Returns:
            ConnectAccountResult with account_id
        """
        ...

    def create_connect_onboarding_link(
        self,
        account_id: str,
        *,
        refresh_url: str,
        return_url: str,
    ) -> ConnectAccountResult:
        """
        Create an onboarding link for Connect account.

        Args:
            account_id: Connect account ID
            refresh_url: URL if link expires
            return_url: URL after completion

        Returns:
            ConnectAccountResult with onboarding_url
        """
        ...

    def get_connect_account_status(self, account_id: str) -> ConnectAccountResult:
        """
        Get the status of a Connect account.

        Args:
            account_id: Connect account ID

        Returns:
            ConnectAccountResult with readiness status
        """
        ...

    def create_transfer(
        self,
        *,
        amount_cents: int,
        currency: str,
        destination_account_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """
        Transfer funds to a Connect account.

        Args:
            amount_cents: Amount to transfer
            currency: Currency code
            destination_account_id: Target Connect account
            metadata: Additional metadata

        Returns:
            PaymentResult with transfer details
        """
        ...
