"""Domain events for user state changes."""

from dataclasses import dataclass
from typing import Literal

RoleType = Literal["student", "tutor", "admin"]


@dataclass(frozen=True)
class UserRoleChanged:
    """
    Event emitted when a user's role changes.

    This event triggers side effects to maintain consistency between
    users.role and related profile tables (tutor_profiles, student_profiles).

    Attributes:
        user_id: The ID of the user whose role changed
        old_role: The previous role before the change
        new_role: The new role after the change
        changed_by: The ID of the admin user who made the change
    """

    user_id: int
    old_role: RoleType
    new_role: RoleType
    changed_by: int

    def is_becoming_tutor(self) -> bool:
        """Check if this role change transitions to tutor."""
        return self.new_role == "tutor" and self.old_role != "tutor"

    def is_leaving_tutor(self) -> bool:
        """Check if this role change transitions away from tutor."""
        return self.old_role == "tutor" and self.new_role != "tutor"
