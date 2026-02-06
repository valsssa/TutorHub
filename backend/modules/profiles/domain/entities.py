"""
Domain entities for profiles module.

These are pure data classes representing the core profile domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from modules.profiles.domain.value_objects import (
    Bio,
    PhoneNumber,
    ProfileId,
    Timezone,
    UserId,
)


@dataclass
class UserProfileEntity:
    """
    Core user profile domain entity.

    Represents extended profile information beyond basic user auth data.
    The User entity (auth module) contains first_name, last_name, and avatar_key.
    This entity contains additional profile details.
    """

    id: ProfileId | None
    user_id: UserId

    bio: str | None = None
    timezone: str = "UTC"
    phone: str | None = None

    country_of_birth: str | None = None
    phone_country_code: str | None = None
    date_of_birth: date | None = None
    age_confirmed: bool = False

    created_at: datetime | None = None
    updated_at: datetime | None = None

    first_name: str | None = field(default=None, repr=False)
    last_name: str | None = field(default=None, repr=False)
    avatar_url: str | None = field(default=None, repr=False)

    @property
    def full_name(self) -> str | None:
        """Get user's full name if both names are available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name

    @property
    def has_complete_profile(self) -> bool:
        """Check if profile has minimum required information."""
        return bool(self.first_name and self.last_name)

    @property
    def timezone_object(self) -> Timezone:
        """Get timezone as a validated value object."""
        return Timezone(self.timezone)

    @property
    def phone_object(self) -> PhoneNumber | None:
        """Get phone as a validated value object."""
        if self.phone:
            return PhoneNumber(self.phone)
        return None

    @property
    def bio_object(self) -> Bio | None:
        """Get bio as a validated value object."""
        if self.bio:
            return Bio(self.bio)
        return None

    @property
    def is_adult_confirmed(self) -> bool:
        """Check if user has confirmed they are 18+."""
        return self.age_confirmed

    def validate_timezone(self) -> bool:
        """Validate the timezone field."""
        return Timezone.is_valid(self.timezone)

    def validate_phone(self) -> bool:
        """Validate the phone field."""
        if self.phone is None:
            return True
        return PhoneNumber.is_valid(self.phone)

    def validate_bio(self) -> bool:
        """Validate the bio field."""
        if self.bio is None:
            return True
        return Bio.is_valid(self.bio)

    def validate(self) -> list[str]:
        """
        Validate all profile fields.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if not self.validate_timezone():
            errors.append(f"Invalid timezone: {self.timezone}")

        if not self.validate_phone():
            errors.append(f"Invalid phone format: {self.phone}")

        if not self.validate_bio():
            errors.append(f"Bio exceeds maximum length of {Bio.max_length} characters")

        if self.country_of_birth and len(self.country_of_birth) != 2:
            errors.append("Country of birth must be ISO 3166-1 alpha-2 code")

        if self.phone_country_code and not self.phone_country_code.startswith("+"):
            errors.append("Phone country code must start with +")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert entity to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "timezone": self.timezone,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "country_of_birth": self.country_of_birth,
            "phone_country_code": self.phone_country_code,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age_confirmed": self.age_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_empty(cls, user_id: UserId) -> "UserProfileEntity":
        """Create an empty profile for a new user."""
        return cls(
            id=None,
            user_id=user_id,
            timezone="UTC",
        )
