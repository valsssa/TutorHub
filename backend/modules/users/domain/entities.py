"""
Domain entities for users module.

These are pure data classes representing the core user domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from modules.users.domain.value_objects import (
    AvatarKey,
    Currency,
    Language,
    Timezone,
    UserId,
)

RoleType = Literal["student", "tutor", "admin", "owner"]


@dataclass
class UserEntity:
    """
    Domain entity representing a user in the system.

    A user represents an authenticated account with profile information,
    preferences, and role-based access control.
    """

    id: UserId | None
    email: str
    first_name: str | None
    last_name: str | None
    role: RoleType
    is_active: bool = True
    is_verified: bool = False
    profile_incomplete: bool = False
    avatar_key: AvatarKey | None = None
    currency: Currency = field(default_factory=lambda: Currency("USD"))
    timezone: Timezone = field(default_factory=lambda: Timezone("UTC"))
    preferred_language: Language = field(default_factory=lambda: Language("en"))
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_persisted(self) -> bool:
        """Check if the user has been persisted (has an ID)."""
        return self.id is not None

    @property
    def full_name(self) -> str | None:
        """Get user's full name if both parts are available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name

    @property
    def is_tutor(self) -> bool:
        """Check if user has tutor role."""
        return self.role == "tutor"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"

    @property
    def is_owner(self) -> bool:
        """Check if user has owner role."""
        return self.role == "owner"

    @property
    def is_student(self) -> bool:
        """Check if user has student role."""
        return self.role == "student"

    def __eq__(self, other: object) -> bool:
        """
        Compare users by their ID if both are persisted.

        Two users are considered equal if they have the same ID.
        """
        if not isinstance(other, UserEntity):
            return NotImplemented
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on user ID."""
        return hash(self.id) if self.id else hash(id(self))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"UserEntity(id={self.id}, email={self.email}, "
            f"role={self.role}, is_active={self.is_active})"
        )


@dataclass
class UserPreferences:
    """
    Domain entity representing a user's preferences.

    This is a subset of user data focused on configurable preferences
    like timezone, currency, and language.
    """

    user_id: UserId
    currency: Currency
    timezone: Timezone
    preferred_language: Language

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"UserPreferences(user_id={self.user_id}, "
            f"currency={self.currency}, timezone={self.timezone})"
        )
