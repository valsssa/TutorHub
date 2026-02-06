"""
Value objects for tutor_profile domain.

Value objects are immutable and defined by their attributes rather than identity.
They encapsulate validation and business rules for domain primitives.
"""

from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TutorId:
    """Value object representing a tutor's unique identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("Tutor ID must be a positive integer")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class HourlyRate:
    """
    Value object representing a tutor's hourly rate.

    Encapsulates currency and amount validation.
    """

    amount: Decimal
    currency: str

    # Supported currencies with min/max rates in their smallest unit
    CURRENCY_CONSTRAINTS: dict[str, dict[str, Any]] = {
        "USD": {"min": Decimal("5.00"), "max": Decimal("500.00"), "symbol": "$"},
        "EUR": {"min": Decimal("5.00"), "max": Decimal("500.00"), "symbol": "€"},
        "GBP": {"min": Decimal("5.00"), "max": Decimal("500.00"), "symbol": "£"},
        "CAD": {"min": Decimal("5.00"), "max": Decimal("500.00"), "symbol": "C$"},
        "AUD": {"min": Decimal("5.00"), "max": Decimal("500.00"), "symbol": "A$"},
    }

    def __post_init__(self) -> None:
        # Normalize currency
        currency = self.currency.upper()
        object.__setattr__(self, "currency", currency)

        if currency not in self.CURRENCY_CONSTRAINTS:
            raise ValueError(f"Unsupported currency: {currency}")

        constraints = self.CURRENCY_CONSTRAINTS[currency]
        if self.amount < constraints["min"]:
            raise ValueError(
                f"Hourly rate must be at least {constraints['min']} {currency}"
            )
        if self.amount > constraints["max"]:
            raise ValueError(
                f"Hourly rate cannot exceed {constraints['max']} {currency}"
            )

    @classmethod
    def from_cents(cls, cents: int, currency: str) -> "HourlyRate":
        """Create from amount in cents."""
        return cls(amount=Decimal(cents) / 100, currency=currency)

    def to_cents(self) -> int:
        """Convert to cents for payment processing."""
        return int(self.amount * 100)

    @property
    def symbol(self) -> str:
        """Get currency symbol."""
        return self.CURRENCY_CONSTRAINTS.get(self.currency, {}).get("symbol", self.currency)

    def __str__(self) -> str:
        return f"{self.symbol}{self.amount:.2f}"


@dataclass(frozen=True)
class AvailabilitySlot:
    """
    Value object representing a recurring availability slot.

    Represents a time window on a specific day of the week.
    """

    day_of_week: int  # 0=Monday, 6=Sunday (ISO weekday)
    start_time: time
    end_time: time
    timezone: str = "UTC"

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __post_init__(self) -> None:
        if not 0 <= self.day_of_week <= 6:
            raise ValueError("Day of week must be 0-6 (Monday-Sunday)")

        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")

        # Minimum slot duration: 30 minutes
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if end_minutes - start_minutes < 30:
            raise ValueError("Availability slot must be at least 30 minutes")

    @property
    def day_name(self) -> str:
        """Get the name of the day."""
        return self.DAYS[self.day_of_week]

    @property
    def duration_minutes(self) -> int:
        """Get the duration in minutes."""
        start = self.start_time.hour * 60 + self.start_time.minute
        end = self.end_time.hour * 60 + self.end_time.minute
        return end - start

    def overlaps_with(self, other: "AvailabilitySlot") -> bool:
        """Check if this slot overlaps with another on the same day."""
        if self.day_of_week != other.day_of_week:
            return False

        return (
            self.start_time < other.end_time and
            other.start_time < self.end_time
        )

    def __str__(self) -> str:
        return (
            f"{self.day_name} "
            f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} "
            f"({self.timezone})"
        )


@dataclass(frozen=True)
class SubjectExpertise:
    """
    Value object representing a tutor's expertise in a subject.

    Includes proficiency level and optional certification.
    """

    subject_id: int
    subject_name: str
    proficiency_level: str  # "beginner", "intermediate", "advanced", "expert"
    years_experience: int = 0
    is_certified: bool = False

    VALID_LEVELS = ["beginner", "intermediate", "advanced", "expert"]

    def __post_init__(self) -> None:
        if self.proficiency_level not in self.VALID_LEVELS:
            raise ValueError(
                f"Proficiency level must be one of: {', '.join(self.VALID_LEVELS)}"
            )
        if self.years_experience < 0:
            raise ValueError("Years of experience cannot be negative")

    @property
    def level_rank(self) -> int:
        """Get numeric rank of proficiency level."""
        return self.VALID_LEVELS.index(self.proficiency_level)

    def __str__(self) -> str:
        cert = " (Certified)" if self.is_certified else ""
        return f"{self.subject_name}: {self.proficiency_level}{cert}"
