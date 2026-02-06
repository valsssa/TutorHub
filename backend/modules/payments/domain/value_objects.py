"""
Value objects for payments module.

Immutable objects representing payment concepts with no identity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NewType

PaymentId = NewType("PaymentId", int)
TransactionId = NewType("TransactionId", int)
WalletId = NewType("WalletId", int)
PayoutId = NewType("PayoutId", int)


class PaymentMethod(str, Enum):
    """Available payment methods."""

    CARD = "CARD"
    WALLET = "WALLET"
    BANK_TRANSFER = "BANK_TRANSFER"


class TransactionType(str, Enum):
    """Types of wallet transactions."""

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    REFUND = "REFUND"
    PAYOUT = "PAYOUT"
    PAYMENT = "PAYMENT"
    FEE = "FEE"


class TransactionStatus(str, Enum):
    """Status of a transaction."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PayoutStatus(str, Enum):
    """Status of a payout to a tutor."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Money:
    """
    Immutable value object representing a monetary amount.

    Amounts are stored in cents to avoid floating-point precision issues.
    """

    amount_cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate money fields."""
        if not isinstance(self.amount_cents, int):
            object.__setattr__(self, "amount_cents", int(self.amount_cents))
        if len(self.currency) != 3:
            raise ValueError(f"Currency must be 3-character ISO code: {self.currency}")
        object.__setattr__(self, "currency", self.currency.upper())

    @property
    def amount_decimal(self) -> float:
        """Get amount as decimal (for display purposes)."""
        return self.amount_cents / 100

    @property
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount_cents == 0

    @property
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount_cents > 0

    @property
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount_cents < 0

    def __add__(self, other: "Money") -> "Money":
        """Add two Money objects."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money to {type(other)}")
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
        return Money(
            amount_cents=self.amount_cents + other.amount_cents,
            currency=self.currency,
        )

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money objects."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other)} from Money")
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )
        return Money(
            amount_cents=self.amount_cents - other.amount_cents,
            currency=self.currency,
        )

    def __mul__(self, multiplier: int | float) -> "Money":
        """Multiply Money by a scalar."""
        if not isinstance(multiplier, (int, float)):
            raise TypeError(f"Cannot multiply Money by {type(multiplier)}")
        return Money(
            amount_cents=int(self.amount_cents * multiplier),
            currency=self.currency,
        )

    def __rmul__(self, multiplier: int | float) -> "Money":
        """Right multiplication (scalar * Money)."""
        return self.__mul__(multiplier)

    def __neg__(self) -> "Money":
        """Negate the amount."""
        return Money(amount_cents=-self.amount_cents, currency=self.currency)

    def __abs__(self) -> "Money":
        """Get absolute value."""
        return Money(amount_cents=abs(self.amount_cents), currency=self.currency)

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._check_currency_match(other)
        return self.amount_cents < other.amount_cents

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._check_currency_match(other)
        return self.amount_cents <= other.amount_cents

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._check_currency_match(other)
        return self.amount_cents > other.amount_cents

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._check_currency_match(other)
        return self.amount_cents >= other.amount_cents

    def _check_currency_match(self, other: "Money") -> None:
        """Verify currencies match for comparison."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )

    def format_display(self) -> str:
        """Format for user display (e.g., '$10.50')."""
        currency_symbols = {
            "USD": "$",
            "EUR": "\u20ac",
            "GBP": "\u00a3",
            "JPY": "\u00a5",
            "CAD": "CA$",
            "AUD": "A$",
        }
        symbol = currency_symbols.get(self.currency, f"{self.currency} ")
        if self.currency == "JPY":
            return f"{symbol}{self.amount_cents}"
        return f"{symbol}{self.amount_decimal:.2f}"

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create a zero amount."""
        return cls(amount_cents=0, currency=currency)

    @classmethod
    def from_decimal(cls, amount: float, currency: str = "USD") -> "Money":
        """Create Money from a decimal amount."""
        return cls(amount_cents=int(round(amount * 100)), currency=currency)
