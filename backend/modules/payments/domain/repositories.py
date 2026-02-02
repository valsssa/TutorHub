"""
Repository interfaces for payments module.

Defines the contracts for payment persistence operations.
"""

from datetime import datetime
from typing import Protocol

from modules.payments.domain.entities import (
    PaymentEntity,
    PayoutEntity,
    TransactionEntity,
    WalletEntity,
)
from modules.payments.domain.value_objects import (
    PayoutStatus,
    TransactionStatus,
    TransactionType,
)


class WalletRepository(Protocol):
    """
    Protocol for wallet repository operations.

    Implementations should handle:
    - Wallet CRUD operations
    - Balance updates with concurrency safety
    - User lookups
    """

    def get_by_id(self, wallet_id: int) -> WalletEntity | None:
        """
        Get a wallet by its ID.

        Args:
            wallet_id: Wallet's unique identifier

        Returns:
            WalletEntity if found, None otherwise
        """
        ...

    def get_by_user(self, user_id: int) -> WalletEntity | None:
        """
        Get a wallet by user ID.

        Args:
            user_id: User's unique identifier

        Returns:
            WalletEntity if found, None otherwise
        """
        ...

    def create(self, wallet: WalletEntity) -> WalletEntity:
        """
        Create a new wallet.

        Args:
            wallet: Wallet entity to create

        Returns:
            Created wallet with populated ID
        """
        ...

    def update_balance(
        self,
        wallet_id: int,
        amount_cents: int,
        *,
        is_pending: bool = False,
    ) -> WalletEntity:
        """
        Update wallet balance atomically.

        This should use database-level atomic operations to prevent
        race conditions (e.g., SQL UPDATE with increment).

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
        ...

    def get_or_create(
        self,
        user_id: int,
        currency: str = "USD",
    ) -> WalletEntity:
        """
        Get existing wallet or create new one for user.

        Args:
            user_id: User's unique identifier
            currency: Currency for new wallet if created

        Returns:
            Existing or newly created wallet
        """
        ...

    def lock_for_update(self, wallet_id: int) -> WalletEntity | None:
        """
        Get wallet with row-level lock for update.

        Use this when performing balance updates that require
        reading and writing in a transaction.

        Args:
            wallet_id: Wallet ID to lock

        Returns:
            WalletEntity if found, None otherwise
        """
        ...


class TransactionRepository(Protocol):
    """
    Protocol for transaction repository operations.

    Implementations should handle:
    - Transaction CRUD operations
    - Wallet transaction history
    - Reference lookups for idempotency
    """

    def get_by_id(self, transaction_id: int) -> TransactionEntity | None:
        """
        Get a transaction by its ID.

        Args:
            transaction_id: Transaction's unique identifier

        Returns:
            TransactionEntity if found, None otherwise
        """
        ...

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
        """
        Get transactions for a wallet with optional filtering.

        Args:
            wallet_id: Wallet's unique identifier
            types: Filter by transaction types
            statuses: Filter by transaction statuses
            from_date: Filter by created date (inclusive)
            to_date: Filter by created date (inclusive)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching transactions, ordered by created_at desc
        """
        ...

    def create(self, transaction: TransactionEntity) -> TransactionEntity:
        """
        Create a new transaction.

        Args:
            transaction: Transaction entity to create

        Returns:
            Created transaction with populated ID
        """
        ...

    def get_by_reference(self, reference_id: str) -> TransactionEntity | None:
        """
        Get a transaction by its reference ID.

        Used for idempotency checks to prevent duplicate transactions.

        Args:
            reference_id: External reference identifier

        Returns:
            TransactionEntity if found, None otherwise
        """
        ...

    def update_status(
        self,
        transaction_id: int,
        status: TransactionStatus,
        *,
        completed_at: datetime | None = None,
    ) -> TransactionEntity | None:
        """
        Update transaction status.

        Args:
            transaction_id: Transaction ID to update
            status: New status
            completed_at: Completion timestamp (if completing)

        Returns:
            Updated transaction, or None if not found
        """
        ...

    def count_by_wallet(
        self,
        wallet_id: int,
        *,
        types: list[TransactionType] | None = None,
        statuses: list[TransactionStatus] | None = None,
    ) -> int:
        """
        Count transactions for a wallet.

        Args:
            wallet_id: Wallet's unique identifier
            types: Filter by transaction types
            statuses: Filter by transaction statuses

        Returns:
            Count of matching transactions
        """
        ...

    def get_pending_transactions(
        self,
        *,
        older_than_minutes: int = 30,
    ) -> list[TransactionEntity]:
        """
        Get pending transactions that may need cleanup.

        Args:
            older_than_minutes: Only return transactions older than this

        Returns:
            List of stale pending transactions
        """
        ...


class PayoutRepository(Protocol):
    """
    Protocol for payout repository operations.

    Implementations should handle:
    - Payout CRUD operations
    - Tutor payout history
    - Status tracking
    """

    def get_by_id(self, payout_id: int) -> PayoutEntity | None:
        """
        Get a payout by its ID.

        Args:
            payout_id: Payout's unique identifier

        Returns:
            PayoutEntity if found, None otherwise
        """
        ...

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
        """
        Get payouts for a tutor with optional filtering.

        Args:
            tutor_id: Tutor's user ID
            statuses: Filter by payout statuses
            from_date: Filter by created date (inclusive)
            to_date: Filter by created date (inclusive)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching payouts, ordered by created_at desc
        """
        ...

    def create(self, payout: PayoutEntity) -> PayoutEntity:
        """
        Create a new payout.

        Args:
            payout: Payout entity to create

        Returns:
            Created payout with populated ID
        """
        ...

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
        """
        Update payout status.

        Args:
            payout_id: Payout ID to update
            status: New status
            stripe_payout_id: Stripe payout ID (if available)
            stripe_transfer_id: Stripe transfer ID (if available)
            failure_reason: Reason for failure (if failed)
            completed_at: Completion timestamp (if completing)

        Returns:
            Updated payout, or None if not found
        """
        ...

    def get_pending(
        self,
        *,
        older_than_hours: int | None = None,
    ) -> list[PayoutEntity]:
        """
        Get pending payouts.

        Args:
            older_than_hours: Only return payouts older than this

        Returns:
            List of pending payouts
        """
        ...

    def get_by_stripe_payout_id(self, stripe_payout_id: str) -> PayoutEntity | None:
        """
        Get a payout by Stripe payout ID.

        Args:
            stripe_payout_id: Stripe's payout identifier

        Returns:
            PayoutEntity if found, None otherwise
        """
        ...

    def count_by_tutor(
        self,
        tutor_id: int,
        *,
        statuses: list[PayoutStatus] | None = None,
    ) -> int:
        """
        Count payouts for a tutor.

        Args:
            tutor_id: Tutor's user ID
            statuses: Filter by payout statuses

        Returns:
            Count of matching payouts
        """
        ...

    def get_total_paid_to_tutor(
        self,
        tutor_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """
        Get total amount paid to a tutor (in cents).

        Args:
            tutor_id: Tutor's user ID
            from_date: Start date for range (inclusive)
            to_date: End date for range (inclusive)

        Returns:
            Total paid amount in cents
        """
        ...


class PaymentRepository(Protocol):
    """
    Protocol for payment repository operations.

    Implementations should handle:
    - Payment CRUD operations
    - Booking payment lookups
    - Stripe reference lookups
    """

    def get_by_id(self, payment_id: int) -> PaymentEntity | None:
        """
        Get a payment by its ID.

        Args:
            payment_id: Payment's unique identifier

        Returns:
            PaymentEntity if found, None otherwise
        """
        ...

    def get_by_booking(self, booking_id: int) -> PaymentEntity | None:
        """
        Get the payment for a booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            PaymentEntity if found, None otherwise
        """
        ...

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
        """
        Get payments for a student with optional filtering.

        Args:
            student_id: Student's user ID
            statuses: Filter by payment statuses
            from_date: Filter by created date (inclusive)
            to_date: Filter by created date (inclusive)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching payments, ordered by created_at desc
        """
        ...

    def create(self, payment: PaymentEntity) -> PaymentEntity:
        """
        Create a new payment.

        Args:
            payment: Payment entity to create

        Returns:
            Created payment with populated ID
        """
        ...

    def update(self, payment: PaymentEntity) -> PaymentEntity:
        """
        Update an existing payment.

        Args:
            payment: Payment entity with updated fields

        Returns:
            Updated payment entity
        """
        ...

    def get_by_stripe_session(self, session_id: str) -> PaymentEntity | None:
        """
        Get a payment by Stripe checkout session ID.

        Args:
            session_id: Stripe checkout session identifier

        Returns:
            PaymentEntity if found, None otherwise
        """
        ...

    def get_by_stripe_payment_intent(
        self,
        payment_intent_id: str,
    ) -> PaymentEntity | None:
        """
        Get a payment by Stripe payment intent ID.

        Args:
            payment_intent_id: Stripe payment intent identifier

        Returns:
            PaymentEntity if found, None otherwise
        """
        ...
