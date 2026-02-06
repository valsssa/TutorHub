"""
Domain entities for students module.

These are pure data classes representing the core student domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StudentProfileEntity:
    """
    Core student profile domain entity.

    Represents a student's profile information and learning preferences.
    """

    id: int | None
    user_id: int

    # Profile information
    phone: str | None = None
    bio: str | None = None
    grade_level: str | None = None
    school_name: str | None = None

    # Learning preferences
    learning_goals: str | None = None
    interests: str | None = None
    preferred_subjects: list[int] = field(default_factory=list)
    preferred_language: str | None = None

    # Statistics
    total_sessions: int = 0
    credit_balance_cents: int = 0

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def has_learning_goals(self) -> bool:
        """Check if student has defined learning goals."""
        return bool(self.learning_goals and self.learning_goals.strip())

    @property
    def has_bio(self) -> bool:
        """Check if student has a bio."""
        return bool(self.bio and self.bio.strip())

    @property
    def is_profile_complete(self) -> bool:
        """
        Check if the profile has essential information filled out.

        A complete profile has at least learning goals or bio.
        """
        return self.has_learning_goals or self.has_bio

    @property
    def credit_balance_decimal(self) -> float:
        """Get credit balance as decimal dollars."""
        return self.credit_balance_cents / 100.0

    def add_credits(self, amount_cents: int) -> None:
        """
        Add credits to the student's balance.

        Args:
            amount_cents: Amount to add in cents

        Raises:
            ValueError: If amount is negative
        """
        if amount_cents < 0:
            raise ValueError("Cannot add negative credits")
        self.credit_balance_cents += amount_cents

    def deduct_credits(self, amount_cents: int) -> bool:
        """
        Deduct credits from the student's balance.

        Args:
            amount_cents: Amount to deduct in cents

        Returns:
            True if successful, False if insufficient balance

        Raises:
            ValueError: If amount is negative
        """
        if amount_cents < 0:
            raise ValueError("Cannot deduct negative credits")
        if self.credit_balance_cents < amount_cents:
            return False
        self.credit_balance_cents -= amount_cents
        return True

    def increment_session_count(self) -> None:
        """Increment the total sessions counter."""
        self.total_sessions += 1
