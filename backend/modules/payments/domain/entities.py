"""
Domain entities for payments module.

These are pure data classes representing the core payment domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from modules.payments.domain.value_objects import (
    Money,
    PayoutStatus,
    TransactionStatus,
    TransactionType,
)


@dataclass
class WalletEntity:
    """
    Wallet domain entity.

    Represents a user's wallet for storing credits and making payments.
    """

    id: int | None
    user_id: int
    balance_cents: int = 0
    currency: str = "USD"
    pending_cents: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def balance(self) -> Money:
        """Get balance as Money value object."""
        return Money(amount_cents=self.balance_cents, currency=self.currency)

    @property
    def pending_balance(self) -> Money:
        """Get pending balance as Money value object."""
        return Money(amount_cents=self.pending_cents, currency=self.currency)

    @property
    def available_balance(self) -> Money:
        """Get available balance (total minus pending)."""
        return Money(
            amount_cents=self.balance_cents - self.pending_cents,
            currency=self.currency,
        )

    @property
    def balance_decimal(self) -> Decimal:
        """Get balance as decimal."""
        return Decimal(self.balance_cents) / 100

    @property
    def is_empty(self) -> bool:
        """Check if wallet has no balance."""
        return self.balance_cents == 0

    def has_sufficient_funds(self, amount_cents: int) -> bool:
        """Check if wallet has sufficient funds for an amount."""
        return self.available_balance.amount_cents >= amount_cents

    def can_withdraw(self, amount_cents: int) -> bool:
        """Check if the specified amount can be withdrawn."""
        return self.has_sufficient_funds(amount_cents)


@dataclass
class TransactionEntity:
    """
    Transaction domain entity.

    Represents a single transaction in a wallet (deposit, withdrawal, etc.).
    """

    id: int | None
    wallet_id: int
    type: TransactionType
    amount_cents: int
    currency: str = "USD"
    description: str | None = None
    reference_id: str | None = None
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict | None = field(default_factory=dict)

    @property
    def amount(self) -> Money:
        """Get amount as Money value object."""
        return Money(amount_cents=self.amount_cents, currency=self.currency)

    @property
    def amount_decimal(self) -> Decimal:
        """Get amount as decimal."""
        return Decimal(self.amount_cents) / 100

    @property
    def is_credit(self) -> bool:
        """Check if transaction adds to wallet balance."""
        return self.type in (
            TransactionType.DEPOSIT,
            TransactionType.REFUND,
            TransactionType.PAYOUT,
        )

    @property
    def is_debit(self) -> bool:
        """Check if transaction subtracts from wallet balance."""
        return self.type in (
            TransactionType.WITHDRAWAL,
            TransactionType.PAYMENT,
            TransactionType.FEE,
        )

    @property
    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == TransactionStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING

    @property
    def is_failed(self) -> bool:
        """Check if transaction failed."""
        return self.status == TransactionStatus.FAILED

    def get_signed_amount(self) -> int:
        """Get amount with sign based on transaction type."""
        if self.is_debit:
            return -abs(self.amount_cents)
        return abs(self.amount_cents)


@dataclass
class PayoutEntity:
    """
    Payout domain entity.

    Represents a payout from platform to a tutor's bank account.
    """

    id: int | None
    tutor_id: int
    amount_cents: int
    currency: str = "USD"
    status: PayoutStatus = PayoutStatus.PENDING
    stripe_payout_id: str | None = None
    stripe_transfer_id: str | None = None
    booking_ids: list[int] = field(default_factory=list)
    description: str | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict | None = field(default_factory=dict)

    @property
    def amount(self) -> Money:
        """Get amount as Money value object."""
        return Money(amount_cents=self.amount_cents, currency=self.currency)

    @property
    def amount_decimal(self) -> Decimal:
        """Get amount as decimal."""
        return Decimal(self.amount_cents) / 100

    @property
    def is_pending(self) -> bool:
        """Check if payout is pending."""
        return self.status == PayoutStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Check if payout is processing."""
        return self.status == PayoutStatus.PROCESSING

    @property
    def is_completed(self) -> bool:
        """Check if payout is completed."""
        return self.status == PayoutStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if payout failed."""
        return self.status == PayoutStatus.FAILED

    @property
    def can_be_cancelled(self) -> bool:
        """Check if payout can be cancelled."""
        return self.status in (PayoutStatus.PENDING, PayoutStatus.PROCESSING)


@dataclass
class PaymentEntity:
    """
    Payment domain entity.

    Represents a payment for a booking or service.
    """

    id: int | None
    booking_id: int | None
    student_id: int
    amount_cents: int
    currency: str = "USD"
    status: str = "pending"
    stripe_checkout_session_id: str | None = None
    stripe_payment_intent_id: str | None = None
    error_message: str | None = None
    paid_at: datetime | None = None
    refunded_at: datetime | None = None
    refund_amount_cents: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def amount(self) -> Money:
        """Get amount as Money value object."""
        return Money(amount_cents=self.amount_cents, currency=self.currency)

    @property
    def amount_decimal(self) -> Decimal:
        """Get amount as decimal."""
        return Decimal(self.amount_cents) / 100

    @property
    def refund_amount(self) -> Money:
        """Get refund amount as Money value object."""
        return Money(amount_cents=self.refund_amount_cents, currency=self.currency)

    @property
    def remaining_refundable(self) -> Money:
        """Get remaining amount that can be refunded."""
        return Money(
            amount_cents=self.amount_cents - self.refund_amount_cents,
            currency=self.currency,
        )

    @property
    def is_paid(self) -> bool:
        """Check if payment is completed."""
        return self.status == "completed"

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == "pending"

    @property
    def is_refunded(self) -> bool:
        """Check if payment is fully refunded."""
        return self.status == "refunded"

    @property
    def is_partially_refunded(self) -> bool:
        """Check if payment is partially refunded."""
        return self.status == "partially_refunded"

    @property
    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded."""
        return (
            self.status in ("completed", "partially_refunded")
            and self.remaining_refundable.amount_cents > 0
        )
