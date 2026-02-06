"""Payment, refund, payout, wallet and transaction models."""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, JSONType


class WebhookEvent(Base):
    """Track processed Stripe webhook events for idempotency.

    Stripe may deliver webhooks multiple times. This table ensures we only
    process each event once, preventing duplicate payments/credits.
    """

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True)
    stripe_event_id = Column(String(255), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class SupportedCurrency(Base):
    """Currency options supported by the platform."""

    __tablename__ = "supported_currencies"

    currency_code = Column(String(3), primary_key=True)
    currency_name = Column(String(50), nullable=False)
    currency_symbol = Column(String(10), nullable=False)
    decimal_places = Column(Integer, default=2)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Payment(Base):
    """Payment transactions for bookings and packages."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    archived_student_id = Column(Integer, nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    provider = Column(String(20), default="stripe", nullable=False)
    provider_payment_id = Column(Text)
    status = Column(String(30), default="REQUIRES_ACTION", nullable=False)
    payment_metadata = Column("metadata", JSONType)
    # Stripe-specific fields
    stripe_checkout_session_id = Column(String(255), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    paid_at = Column(TIMESTAMP(timezone=True), nullable=True)
    refunded_at = Column(TIMESTAMP(timezone=True), nullable=True)
    refund_amount_cents = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    # Relationships
    booking = relationship("Booking", back_populates="payments")
    student = relationship("User", foreign_keys=[student_id])
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_payment_amount"),
        CheckConstraint(
            "provider IN ('stripe', 'adyen', 'paypal', 'test')",
            name="valid_payment_provider",
        ),
        CheckConstraint(
            "status IN ('REQUIRES_ACTION', 'AUTHORIZED', 'CAPTURED', 'REFUNDED', 'FAILED')",
            name="valid_payment_status",
        ),
    )


class Refund(Base):
    """Refund transactions linked to payments."""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    reason = Column(String(30), nullable=False)
    provider_refund_id = Column(Text)
    refund_metadata = Column("metadata", JSONType)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    booking = relationship("Booking", foreign_keys=[booking_id])

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_refund_amount"),
        CheckConstraint(
            "reason IN ('STUDENT_CANCEL', 'TUTOR_CANCEL', 'NO_SHOW_TUTOR', 'GOODWILL', 'OTHER')",
            name="valid_refund_reason",
        ),
    )


class Payout(Base):
    """Tutor earnings payout batches."""

    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    archived_tutor_id = Column(Integer, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    transfer_reference = Column(Text)
    payout_metadata = Column("metadata", JSONType)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tutor = relationship("User", foreign_keys=[tutor_id])

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_payout_amount"),
        CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'PAID', 'FAILED')",
            name="valid_payout_status",
        ),
        CheckConstraint("period_start <= period_end", name="valid_payout_period"),
    )


class Wallet(Base):
    """User wallet for storing credits and making payments.

    Each user can have one wallet per currency. The wallet tracks
    available balance and pending balance (funds in transit).
    """

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    balance_cents = Column(Integer, default=0, nullable=False)
    pending_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="unique_user_wallet_per_currency"),
        CheckConstraint("balance_cents >= 0", name="non_negative_wallet_balance"),
        CheckConstraint("pending_cents >= 0", name="non_negative_pending_balance"),
        Index("ix_wallets_user_id", "user_id"),
    )


class WalletTransaction(Base):
    """Transaction record for wallet operations.

    Tracks all deposits, withdrawals, transfers, refunds, payouts,
    payments, and fees applied to a wallet.
    """

    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True)
    wallet_id = Column(
        Integer,
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(String(20), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(255), nullable=True, unique=True)
    transaction_metadata = Column(JSONType, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")

    __table_args__ = (
        CheckConstraint(
            "type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'REFUND', 'PAYOUT', 'PAYMENT', 'FEE')",
            name="valid_transaction_type",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name="valid_transaction_status",
        ),
        Index("ix_wallet_transactions_wallet_id", "wallet_id"),
        Index("ix_wallet_transactions_created_at", "created_at"),
        Index("ix_wallet_transactions_reference_id", "reference_id"),
    )
