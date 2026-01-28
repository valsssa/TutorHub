"""Payment, refund, and payout models."""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


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
    student_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    provider = Column(String(20), default="stripe", nullable=False)
    provider_payment_id = Column(Text)
    status = Column(String(30), default="pending", nullable=False)
    payment_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
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

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_payment_amount"),
        CheckConstraint(
            "provider IN ('stripe', 'adyen', 'paypal', 'test')",
            name="valid_payment_provider",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'refunded', 'partially_refunded', "
            "'REQUIRES_ACTION', 'AUTHORIZED', 'CAPTURED', 'REFUNDED', 'FAILED')",
            name="valid_payment_status",
        ),
    )


class Refund(Base):
    """Refund transactions linked to payments."""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    reason = Column(String(30), nullable=False)
    provider_refund_id = Column(Text)
    refund_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

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
    tutor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    transfer_reference = Column(Text)
    payout_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

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
