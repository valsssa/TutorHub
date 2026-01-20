"""Auth domain entities."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserEntity:
    """User domain entity."""

    id: int | None
    email: str
    hashed_password: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool = True
    is_verified: bool = False
    timezone: str = "UTC"
    currency: str = "USD"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "admin"

    def is_tutor(self) -> bool:
        """Check if user is tutor."""
        return self.role == "tutor"

    def is_student(self) -> bool:
        """Check if user is student."""
        return self.role == "student"

    def can_access_admin(self) -> bool:
        """Check if user can access admin resources."""
        return self.is_admin()

    def can_create_bookings(self) -> bool:
        """Check if user can create bookings."""
        return self.is_student()

    def can_accept_bookings(self) -> bool:
        """Check if user can accept bookings."""
        return self.is_tutor()
