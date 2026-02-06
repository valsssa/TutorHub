"""
Value objects for profiles domain.

Immutable objects that represent domain concepts with validation.
"""

import re
from dataclasses import dataclass
from typing import NewType
from zoneinfo import available_timezones

ProfileId = NewType("ProfileId", int)
UserId = NewType("UserId", int)

VALID_TIMEZONES: frozenset[str] = frozenset(available_timezones())

BIO_MAX_LENGTH = 1000
PHONE_E164_PATTERN = re.compile(r"^\+\d{7,15}$")


@dataclass(frozen=True)
class Timezone:
    """
    Validated IANA timezone identifier.

    Ensures timezone strings are valid IANA timezone identifiers
    (e.g., 'America/New_York', 'UTC', 'Europe/London').
    """

    value: str

    def __post_init__(self) -> None:
        if self.value not in VALID_TIMEZONES:
            raise ValueError(
                f"Invalid IANA timezone: '{self.value}'. "
                "Must be a valid timezone identifier."
            )

    def __str__(self) -> str:
        return self.value

    @classmethod
    def utc(cls) -> "Timezone":
        """Return UTC timezone."""
        return cls("UTC")

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a timezone string is valid without raising."""
        return value in VALID_TIMEZONES


@dataclass(frozen=True)
class PhoneNumber:
    """
    Validated phone number in E.164 format.

    E.164 format: + followed by country code and subscriber number (7-15 digits total).
    Example: +12025551234
    """

    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"[\s\-\(\)]", "", self.value)
        if not PHONE_E164_PATTERN.match(normalized):
            raise ValueError(
                f"Invalid phone number format: '{self.value}'. "
                "Must be in E.164 format (e.g., +12025551234)"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a phone number is valid without raising."""
        normalized = re.sub(r"[\s\-\(\)]", "", value)
        return bool(PHONE_E164_PATTERN.match(normalized))

    @property
    def country_code(self) -> str:
        """
        Extract country code from phone number.

        Note: This is a simplified extraction. In production,
        consider using a library like phonenumbers for accurate parsing.
        """
        if len(self.value) <= 1:
            return ""
        if self.value[1] == "1":
            return "+1"
        if len(self.value) >= 3:
            return self.value[:3]
        return self.value[:2]


@dataclass(frozen=True)
class Bio:
    """
    Validated bio text with max length constraint.

    Bio is limited to 1000 characters to prevent abuse and ensure
    reasonable display in UI components.
    """

    value: str
    max_length: int = BIO_MAX_LENGTH

    def __post_init__(self) -> None:
        if len(self.value) > self.max_length:
            raise ValueError(
                f"Bio exceeds maximum length of {self.max_length} characters. "
                f"Current length: {len(self.value)}"
            )

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    @classmethod
    def is_valid(cls, value: str, max_length: int = BIO_MAX_LENGTH) -> bool:
        """Check if bio text is valid without raising."""
        return len(value) <= max_length

    @property
    def truncated(self) -> str:
        """Return truncated bio for display (max 200 chars with ellipsis)."""
        if len(self.value) <= 200:
            return self.value
        return self.value[:197] + "..."
