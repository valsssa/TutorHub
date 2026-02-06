"""
Payments domain layer.

Contains domain entities, value objects, exceptions, and repository protocols
for the payment system.
"""

from modules.payments.domain.entities import (
    PaymentEntity,
    PayoutEntity,
    TransactionEntity,
    WalletEntity,
)
from modules.payments.domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    PaymentError,
    PaymentNotFoundError,
    PayoutFailedError,
    RefundNotAllowedError,
    TransferFailedError,
    WalletNotFoundError,
)
from modules.payments.domain.repositories import (
    PaymentRepository,
    PayoutRepository,
    TransactionRepository,
    WalletRepository,
)
from modules.payments.domain.value_objects import (
    Money,
    PaymentId,
    PaymentMethod,
    PayoutId,
    PayoutStatus,
    TransactionId,
    TransactionStatus,
    TransactionType,
    WalletId,
)

__all__ = [
    # Entities
    "WalletEntity",
    "TransactionEntity",
    "PayoutEntity",
    "PaymentEntity",
    # Value Objects
    "Money",
    "PaymentId",
    "TransactionId",
    "WalletId",
    "PayoutId",
    "PaymentMethod",
    "TransactionType",
    "TransactionStatus",
    "PayoutStatus",
    # Exceptions
    "PaymentError",
    "PaymentNotFoundError",
    "InsufficientFundsError",
    "InvalidAmountError",
    "RefundNotAllowedError",
    "WalletNotFoundError",
    "TransferFailedError",
    "PayoutFailedError",
    # Repositories
    "WalletRepository",
    "TransactionRepository",
    "PayoutRepository",
    "PaymentRepository",
]
