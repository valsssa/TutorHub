"""SQLAlchemy repository implementations for payments module.

Provides concrete implementations of the payment repository protocols,
using SQLAlchemy for database operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Payment, Payout, Wallet, WalletTransaction

from ..domain.entities import (
    PaymentEntity,
    PayoutEntity,
    TransactionEntity,
    WalletEntity,
)
from ..domain.exceptions import (
    InsufficientFundsError,
    PaymentNotFoundError,
    WalletNotFoundError,
)
from ..domain.value_objects import PayoutStatus, TransactionStatus, TransactionType


@dataclass(slots=True)
class WalletRepositoryImpl:
    """SQLAlchemy implementation of WalletRepository.

    Handles wallet persistence with support for row-level locking
    to prevent race conditions during balance updates.
    """

    db: Session

    def get_by_id(self, wallet_id: int) -> WalletEntity | None:
        """Get a wallet by its ID."""
        model = self.db.query(Wallet).filter(Wallet.id == wallet_id).first()
        return self._to_entity(model) if model else None

    def get_by_user(self, user_id: int) -> WalletEntity | None:
        """Get a wallet by user ID."""
        model = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
        return self._to_entity(model) if model else None

    def create(self, wallet: WalletEntity) -> WalletEntity:
        """Create a new wallet."""
        model = Wallet(
            user_id=wallet.user_id,
            balance_cents=wallet.balance_cents,
            pending_cents=wallet.pending_cents,
            currency=wallet.currency,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def update_balance(
        self,
        wallet_id: int,
        amount_cents: int,
        *,
        is_pending: bool = False,
    ) -> WalletEntity:
        """Update wallet balance atomically.

        Uses SELECT FOR UPDATE to lock the row and prevent concurrent updates.
        For debits (negative amounts), validates sufficient funds.

        Args:
            wallet_id: Wallet ID to update
            amount_cents: Amount to add (positive) or subtract (negative)
            is_pending: If True, update pending_cents instead of balance_cents

        Returns:
            Updated wallet entity

        Raises:
            WalletNotFoundError: If wallet not found
            InsufficientFundsError: If balance would go negative (for debits)
        """
        model = (
            self.db.query(Wallet)
            .filter(Wallet.id == wallet_id)
            .with_for_update()
            .first()
        )
        if not model:
            raise WalletNotFoundError(wallet_id=wallet_id)

        if is_pending:
            new_balance = model.pending_cents + amount_cents
            if new_balance < 0:
                raise InsufficientFundsError(
                    required_cents=abs(amount_cents),
                    available_cents=model.pending_cents,
                    currency=model.currency,
                )
            model.pending_cents = new_balance
        else:
            new_balance = model.balance_cents + amount_cents
            if new_balance < 0:
                raise InsufficientFundsError(
                    required_cents=abs(amount_cents),
                    available_cents=model.balance_cents,
                    currency=model.currency,
                )
            model.balance_cents = new_balance

        model.updated_at = datetime.now(UTC)
        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_or_create(
        self,
        user_id: int,
        currency: str = "USD",
    ) -> WalletEntity:
        """Get existing wallet or create new one for user."""
        model = (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id, Wallet.currency == currency)
            .first()
        )
        if model:
            return self._to_entity(model)

        new_wallet = Wallet(
            user_id=user_id,
            balance_cents=0,
            pending_cents=0,
            currency=currency,
        )
        self.db.add(new_wallet)
        self.db.flush()
        self.db.refresh(new_wallet)
        return self._to_entity(new_wallet)

    def lock_for_update(self, wallet_id: int) -> WalletEntity | None:
        """Get wallet with row-level lock for update.

        Use this when performing balance updates that require
        reading and writing in a transaction.
        """
        model = (
            self.db.query(Wallet)
            .filter(Wallet.id == wallet_id)
            .with_for_update()
            .first()
        )
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: Wallet) -> WalletEntity:
        """Convert SQLAlchemy model to domain entity."""
        return WalletEntity(
            id=model.id,
            user_id=model.user_id,
            balance_cents=model.balance_cents,
            pending_cents=model.pending_cents,
            currency=model.currency,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


@dataclass(slots=True)
class TransactionRepositoryImpl:
    """SQLAlchemy implementation of TransactionRepository.

    Handles transaction persistence with support for filtering,
    pagination, and reference-based lookups for idempotency.
    """

    db: Session

    def get_by_id(self, transaction_id: int) -> TransactionEntity | None:
        """Get a transaction by its ID."""
        model = (
            self.db.query(WalletTransaction)
            .filter(WalletTransaction.id == transaction_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_wallet(
        self,
        wallet_id: int,
        *,
        types: list[TransactionType] | None = None,
        statuses: list[TransactionStatus] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[TransactionEntity]:
        """Get transactions for a wallet with optional filtering."""
        query = self.db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet_id
        )

        if types:
            type_values = [t.value for t in types]
            query = query.filter(WalletTransaction.type.in_(type_values))

        if statuses:
            status_values = [s.value for s in statuses]
            query = query.filter(WalletTransaction.status.in_(status_values))

        if from_date:
            query = query.filter(WalletTransaction.created_at >= from_date)

        if to_date:
            query = query.filter(WalletTransaction.created_at <= to_date)

        query = query.order_by(WalletTransaction.created_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        return [self._to_entity(m) for m in models]

    def create(self, transaction: TransactionEntity) -> TransactionEntity:
        """Create a new transaction."""
        model = WalletTransaction(
            wallet_id=transaction.wallet_id,
            type=transaction.type.value,
            amount_cents=transaction.amount_cents,
            currency=transaction.currency,
            status=transaction.status.value,
            description=transaction.description,
            reference_id=transaction.reference_id,
            transaction_metadata=transaction.metadata,
            completed_at=transaction.completed_at,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_reference(self, reference_id: str) -> TransactionEntity | None:
        """Get a transaction by its reference ID.

        Used for idempotency checks to prevent duplicate transactions.
        """
        model = (
            self.db.query(WalletTransaction)
            .filter(WalletTransaction.reference_id == reference_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def update_status(
        self,
        transaction_id: int,
        status: TransactionStatus,
        *,
        completed_at: datetime | None = None,
    ) -> TransactionEntity | None:
        """Update transaction status."""
        model = (
            self.db.query(WalletTransaction)
            .filter(WalletTransaction.id == transaction_id)
            .first()
        )
        if not model:
            return None

        model.status = status.value
        if completed_at:
            model.completed_at = completed_at
        elif status == TransactionStatus.COMPLETED and not model.completed_at:
            model.completed_at = datetime.now(UTC)

        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def count_by_wallet(
        self,
        wallet_id: int,
        *,
        types: list[TransactionType] | None = None,
        statuses: list[TransactionStatus] | None = None,
    ) -> int:
        """Count transactions for a wallet."""
        query = self.db.query(func.count(WalletTransaction.id)).filter(
            WalletTransaction.wallet_id == wallet_id
        )

        if types:
            type_values = [t.value for t in types]
            query = query.filter(WalletTransaction.type.in_(type_values))

        if statuses:
            status_values = [s.value for s in statuses]
            query = query.filter(WalletTransaction.status.in_(status_values))

        return query.scalar() or 0

    def get_pending_transactions(
        self,
        *,
        older_than_minutes: int = 30,
    ) -> list[TransactionEntity]:
        """Get pending transactions that may need cleanup."""
        cutoff = datetime.now(UTC) - timedelta(minutes=older_than_minutes)
        models = (
            self.db.query(WalletTransaction)
            .filter(
                WalletTransaction.status == TransactionStatus.PENDING.value,
                WalletTransaction.created_at < cutoff,
            )
            .order_by(WalletTransaction.created_at.asc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: WalletTransaction) -> TransactionEntity:
        """Convert SQLAlchemy model to domain entity."""
        return TransactionEntity(
            id=model.id,
            wallet_id=model.wallet_id,
            type=TransactionType(model.type),
            amount_cents=model.amount_cents,
            currency=model.currency,
            status=TransactionStatus(model.status),
            description=model.description,
            reference_id=model.reference_id,
            metadata=model.transaction_metadata,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )


@dataclass(slots=True)
class PayoutRepositoryImpl:
    """SQLAlchemy implementation of PayoutRepository.

    Handles payout persistence with support for tutor-based lookups,
    status tracking, and aggregation queries.
    """

    db: Session

    def get_by_id(self, payout_id: int) -> PayoutEntity | None:
        """Get a payout by its ID."""
        model = self.db.query(Payout).filter(Payout.id == payout_id).first()
        return self._to_entity(model) if model else None

    def get_by_tutor(
        self,
        tutor_id: int,
        *,
        statuses: list[PayoutStatus] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[PayoutEntity]:
        """Get payouts for a tutor with optional filtering."""
        query = self.db.query(Payout).filter(Payout.tutor_id == tutor_id)

        if statuses:
            status_values = [self._payout_status_to_db(s) for s in statuses]
            query = query.filter(Payout.status.in_(status_values))

        if from_date:
            query = query.filter(Payout.created_at >= from_date)

        if to_date:
            query = query.filter(Payout.created_at <= to_date)

        query = query.order_by(Payout.created_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        return [self._to_entity(m) for m in models]

    def create(self, payout: PayoutEntity) -> PayoutEntity:
        """Create a new payout."""
        model = Payout(
            tutor_id=payout.tutor_id,
            amount_cents=payout.amount_cents,
            currency=payout.currency,
            status=self._payout_status_to_db(payout.status),
            period_start=payout.created_at.date() if payout.created_at else datetime.now(UTC).date(),
            period_end=payout.created_at.date() if payout.created_at else datetime.now(UTC).date(),
            transfer_reference=payout.stripe_transfer_id,
            payout_metadata={
                "stripe_payout_id": payout.stripe_payout_id,
                "booking_ids": payout.booking_ids,
                "description": payout.description,
                "failure_reason": payout.failure_reason,
                **(payout.metadata or {}),
            },
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def update_status(
        self,
        payout_id: int,
        status: PayoutStatus,
        *,
        stripe_payout_id: str | None = None,
        stripe_transfer_id: str | None = None,
        failure_reason: str | None = None,
        completed_at: datetime | None = None,
    ) -> PayoutEntity | None:
        """Update payout status."""
        model = self.db.query(Payout).filter(Payout.id == payout_id).first()
        if not model:
            return None

        model.status = self._payout_status_to_db(status)
        model.updated_at = datetime.now(UTC)

        metadata = model.payout_metadata or {}
        if stripe_payout_id:
            metadata["stripe_payout_id"] = stripe_payout_id
        if stripe_transfer_id:
            model.transfer_reference = stripe_transfer_id
            metadata["stripe_transfer_id"] = stripe_transfer_id
        if failure_reason:
            metadata["failure_reason"] = failure_reason
        if completed_at:
            metadata["completed_at"] = completed_at.isoformat()
        model.payout_metadata = metadata

        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_pending(
        self,
        *,
        older_than_hours: int | None = None,
    ) -> list[PayoutEntity]:
        """Get pending payouts."""
        query = self.db.query(Payout).filter(Payout.status == "PENDING")

        if older_than_hours:
            cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
            query = query.filter(Payout.created_at < cutoff)

        models = query.order_by(Payout.created_at.asc()).all()
        return [self._to_entity(m) for m in models]

    def get_by_stripe_payout_id(self, stripe_payout_id: str) -> PayoutEntity | None:
        """Get a payout by Stripe payout ID."""
        models = self.db.query(Payout).all()
        for model in models:
            metadata = model.payout_metadata or {}
            if metadata.get("stripe_payout_id") == stripe_payout_id:
                return self._to_entity(model)
        return None

    def count_by_tutor(
        self,
        tutor_id: int,
        *,
        statuses: list[PayoutStatus] | None = None,
    ) -> int:
        """Count payouts for a tutor."""
        query = self.db.query(func.count(Payout.id)).filter(
            Payout.tutor_id == tutor_id
        )

        if statuses:
            status_values = [self._payout_status_to_db(s) for s in statuses]
            query = query.filter(Payout.status.in_(status_values))

        return query.scalar() or 0

    def get_total_paid_to_tutor(
        self,
        tutor_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """Get total amount paid to a tutor (in cents)."""
        query = self.db.query(func.sum(Payout.amount_cents)).filter(
            Payout.tutor_id == tutor_id,
            Payout.status == "PAID",
        )

        if from_date:
            query = query.filter(Payout.created_at >= from_date)

        if to_date:
            query = query.filter(Payout.created_at <= to_date)

        return query.scalar() or 0

    @staticmethod
    def _payout_status_to_db(status: PayoutStatus) -> str:
        """Convert domain PayoutStatus to database value.

        The database uses different status values than the domain.
        """
        mapping = {
            PayoutStatus.PENDING: "PENDING",
            PayoutStatus.PROCESSING: "SUBMITTED",
            PayoutStatus.COMPLETED: "PAID",
            PayoutStatus.FAILED: "FAILED",
            PayoutStatus.CANCELLED: "FAILED",
        }
        return mapping.get(status, "PENDING")

    @staticmethod
    def _db_status_to_payout_status(db_status: str) -> PayoutStatus:
        """Convert database status to domain PayoutStatus."""
        mapping = {
            "PENDING": PayoutStatus.PENDING,
            "SUBMITTED": PayoutStatus.PROCESSING,
            "PAID": PayoutStatus.COMPLETED,
            "FAILED": PayoutStatus.FAILED,
        }
        return mapping.get(db_status, PayoutStatus.PENDING)

    def _to_entity(self, model: Payout) -> PayoutEntity:
        """Convert SQLAlchemy model to domain entity."""
        metadata = model.payout_metadata or {}

        completed_at = None
        if metadata.get("completed_at"):
            try:
                completed_at = datetime.fromisoformat(metadata["completed_at"])
            except (ValueError, TypeError):
                pass

        return PayoutEntity(
            id=model.id,
            tutor_id=model.tutor_id,
            amount_cents=model.amount_cents,
            currency=model.currency,
            status=self._db_status_to_payout_status(model.status),
            stripe_payout_id=metadata.get("stripe_payout_id"),
            stripe_transfer_id=model.transfer_reference,
            booking_ids=metadata.get("booking_ids", []),
            description=metadata.get("description"),
            failure_reason=metadata.get("failure_reason"),
            created_at=model.created_at,
            completed_at=completed_at,
            metadata={
                k: v
                for k, v in metadata.items()
                if k
                not in (
                    "stripe_payout_id",
                    "stripe_transfer_id",
                    "booking_ids",
                    "description",
                    "failure_reason",
                    "completed_at",
                )
            },
        )


@dataclass(slots=True)
class PaymentRepositoryImpl:
    """SQLAlchemy implementation of PaymentRepository.

    Handles payment persistence with support for booking lookups,
    student payment history, and Stripe reference lookups.
    """

    db: Session

    def get_by_id(self, payment_id: int) -> PaymentEntity | None:
        """Get a payment by its ID."""
        model = self.db.query(Payment).filter(Payment.id == payment_id).first()
        return self._to_entity(model) if model else None

    def get_by_booking(self, booking_id: int) -> PaymentEntity | None:
        """Get the payment for a booking."""
        model = (
            self.db.query(Payment)
            .filter(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.desc())
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_student(
        self,
        student_id: int,
        *,
        statuses: list[str] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[PaymentEntity]:
        """Get payments for a student with optional filtering."""
        query = self.db.query(Payment).filter(Payment.student_id == student_id)

        if statuses:
            query = query.filter(Payment.status.in_(statuses))

        if from_date:
            query = query.filter(Payment.created_at >= from_date)

        if to_date:
            query = query.filter(Payment.created_at <= to_date)

        query = query.order_by(Payment.created_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        return [self._to_entity(m) for m in models]

    def create(self, payment: PaymentEntity) -> PaymentEntity:
        """Create a new payment."""
        model = Payment(
            booking_id=payment.booking_id,
            student_id=payment.student_id,
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            status=payment.status,
            stripe_checkout_session_id=payment.stripe_checkout_session_id,
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
            paid_at=payment.paid_at,
            refunded_at=payment.refunded_at,
            refund_amount_cents=payment.refund_amount_cents,
            error_message=payment.error_message,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, payment: PaymentEntity) -> PaymentEntity:
        """Update an existing payment."""
        if not payment.id:
            raise PaymentNotFoundError("Cannot update payment without ID")

        model = self.db.query(Payment).filter(Payment.id == payment.id).first()
        if not model:
            raise PaymentNotFoundError(payment.id)

        model.status = payment.status
        model.stripe_checkout_session_id = payment.stripe_checkout_session_id
        model.stripe_payment_intent_id = payment.stripe_payment_intent_id
        model.paid_at = payment.paid_at
        model.refunded_at = payment.refunded_at
        model.refund_amount_cents = payment.refund_amount_cents
        model.error_message = payment.error_message
        model.updated_at = datetime.now(UTC)

        self.db.flush()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_stripe_session(self, session_id: str) -> PaymentEntity | None:
        """Get a payment by Stripe checkout session ID."""
        model = (
            self.db.query(Payment)
            .filter(Payment.stripe_checkout_session_id == session_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_stripe_payment_intent(
        self,
        payment_intent_id: str,
    ) -> PaymentEntity | None:
        """Get a payment by Stripe payment intent ID."""
        model = (
            self.db.query(Payment)
            .filter(Payment.stripe_payment_intent_id == payment_intent_id)
            .first()
        )
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: Payment) -> PaymentEntity:
        """Convert SQLAlchemy model to domain entity."""
        return PaymentEntity(
            id=model.id,
            booking_id=model.booking_id,
            student_id=model.student_id,
            amount_cents=model.amount_cents,
            currency=model.currency,
            status=model.status,
            stripe_checkout_session_id=model.stripe_checkout_session_id,
            stripe_payment_intent_id=model.stripe_payment_intent_id,
            paid_at=model.paid_at,
            refunded_at=model.refunded_at,
            refund_amount_cents=model.refund_amount_cents or 0,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
