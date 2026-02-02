"""
Value objects for the packages domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NewType

from modules.packages.domain.exceptions import InvalidPackageConfigError

# Type alias for package IDs - provides type safety without runtime overhead
PackageId = NewType("PackageId", int)
PricingOptionId = NewType("PricingOptionId", int)
TutorProfileId = NewType("TutorProfileId", int)
StudentId = NewType("StudentId", int)


class PackageStatus(str, Enum):
    """
    Package lifecycle status.

    Status transitions:
        ACTIVE -> EXHAUSTED (all sessions used)
        ACTIVE -> EXPIRED (validity period ended)
        ACTIVE -> REFUNDED (payment refunded)
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    REFUNDED = "refunded"


# Terminal package statuses (no further transitions allowed)
TERMINAL_PACKAGE_STATUSES = {PackageStatus.EXPIRED, PackageStatus.EXHAUSTED, PackageStatus.REFUNDED}


@dataclass(frozen=True)
class SessionCount:
    """
    Value object representing a non-negative session count.

    Immutable and validates that the count is non-negative.
    """

    value: int

    def __post_init__(self) -> None:
        """Validate session count is non-negative."""
        if self.value < 0:
            raise InvalidPackageConfigError(f"Session count cannot be negative: {self.value}")

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __add__(self, other: "SessionCount | int") -> "SessionCount":
        """Add session counts."""
        if isinstance(other, SessionCount):
            return SessionCount(self.value + other.value)
        return SessionCount(self.value + other)

    def __sub__(self, other: "SessionCount | int") -> "SessionCount":
        """Subtract session counts."""
        if isinstance(other, SessionCount):
            new_value = self.value - other.value
        else:
            new_value = self.value - other
        if new_value < 0:
            raise InvalidPackageConfigError(
                f"Cannot subtract {other} from {self.value}: result would be negative"
            )
        return SessionCount(new_value)

    def __lt__(self, other: "SessionCount | int") -> bool:
        """Compare less than."""
        if isinstance(other, SessionCount):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: "SessionCount | int") -> bool:
        """Compare less than or equal."""
        if isinstance(other, SessionCount):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: "SessionCount | int") -> bool:
        """Compare greater than."""
        if isinstance(other, SessionCount):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: "SessionCount | int") -> bool:
        """Compare greater than or equal."""
        if isinstance(other, SessionCount):
            return self.value >= other.value
        return self.value >= other

    def __eq__(self, other: object) -> bool:
        """Compare equality."""
        if isinstance(other, SessionCount):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)

    @property
    def is_zero(self) -> bool:
        """Check if count is zero."""
        return self.value == 0

    @property
    def is_positive(self) -> bool:
        """Check if count is positive (greater than zero)."""
        return self.value > 0


@dataclass(frozen=True)
class ValidityPeriod:
    """
    Value object representing a package validity period.

    Includes optional rolling expiry (extend_on_use) which extends
    the validity period each time a session is used.
    """

    days: int | None
    extend_on_use: bool = False

    def __post_init__(self) -> None:
        """Validate validity period configuration."""
        if self.days is not None and self.days <= 0:
            raise InvalidPackageConfigError(f"Validity days must be positive: {self.days}")
        if self.extend_on_use and self.days is None:
            raise InvalidPackageConfigError("extend_on_use requires validity_days to be set")

    @property
    def has_expiration(self) -> bool:
        """Check if this validity period expires."""
        return self.days is not None

    @property
    def is_rolling(self) -> bool:
        """Check if validity extends on each use."""
        return self.extend_on_use and self.days is not None

    @classmethod
    def no_expiration(cls) -> "ValidityPeriod":
        """Create a validity period with no expiration."""
        return cls(days=None, extend_on_use=False)

    @classmethod
    def fixed(cls, days: int) -> "ValidityPeriod":
        """Create a fixed validity period."""
        return cls(days=days, extend_on_use=False)

    @classmethod
    def rolling(cls, days: int) -> "ValidityPeriod":
        """Create a rolling validity period that extends on use."""
        return cls(days=days, extend_on_use=True)


@dataclass(frozen=True)
class PackagePrice:
    """
    Value object representing package pricing.

    Stores amount in cents to avoid floating point issues.
    """

    amount_cents: int
    currency: str
    sessions_included: int

    def __post_init__(self) -> None:
        """Validate price configuration."""
        if self.amount_cents <= 0:
            raise InvalidPackageConfigError(f"Price must be positive: {self.amount_cents}")
        if self.sessions_included <= 0:
            raise InvalidPackageConfigError(
                f"Sessions included must be positive: {self.sessions_included}"
            )
        if len(self.currency) != 3:
            raise InvalidPackageConfigError(f"Currency must be 3-letter ISO code: {self.currency}")

    @property
    def amount_decimal(self) -> float:
        """Get price as decimal (for display purposes)."""
        return self.amount_cents / 100.0

    @property
    def price_per_session_cents(self) -> int:
        """Calculate price per session in cents."""
        return self.amount_cents // self.sessions_included

    @property
    def price_per_session_decimal(self) -> float:
        """Calculate price per session as decimal."""
        return self.price_per_session_cents / 100.0

    def format_amount(self) -> str:
        """Format the amount for display."""
        return f"{self.currency} {self.amount_decimal:.2f}"

    @classmethod
    def from_decimal(cls, amount: float, currency: str, sessions_included: int) -> "PackagePrice":
        """Create PackagePrice from decimal amount."""
        return cls(
            amount_cents=int(amount * 100),
            currency=currency.upper(),
            sessions_included=sessions_included,
        )


@dataclass(frozen=True)
class DurationMinutes:
    """Value object representing session duration in minutes."""

    value: int

    def __post_init__(self) -> None:
        """Validate duration is positive."""
        if self.value <= 0:
            raise InvalidPackageConfigError(f"Duration must be positive: {self.value}")

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    @property
    def hours(self) -> float:
        """Get duration in hours."""
        return self.value / 60.0

    @property
    def display(self) -> str:
        """Format duration for display."""
        if self.value >= 60:
            hours = self.value // 60
            minutes = self.value % 60
            if minutes == 0:
                return f"{hours}h"
            return f"{hours}h {minutes}m"
        return f"{self.value}m"
