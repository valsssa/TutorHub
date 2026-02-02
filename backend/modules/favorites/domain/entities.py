"""
Domain entities for favorites module.

These are pure data classes representing the core favorite domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import datetime

from modules.favorites.domain.value_objects import (
    FavoriteId,
    TutorProfileId,
    UserId,
)


@dataclass
class FavoriteEntity:
    """
    Domain entity representing a student's favorite tutor.

    A favorite represents a student saving a tutor profile for
    easy access and reference. It contains no business logic
    beyond the relationship itself.
    """

    id: FavoriteId | None
    student_id: UserId
    tutor_profile_id: TutorProfileId
    created_at: datetime | None = None

    @property
    def is_persisted(self) -> bool:
        """Check if the favorite has been persisted (has an ID)."""
        return self.id is not None

    def __eq__(self, other: object) -> bool:
        """
        Compare favorites by their student and tutor profile IDs.

        Two favorites are considered equal if they represent the same
        student-tutor relationship, regardless of ID or created_at.
        """
        if not isinstance(other, FavoriteEntity):
            return NotImplemented
        return (
            self.student_id == other.student_id
            and self.tutor_profile_id == other.tutor_profile_id
        )

    def __hash__(self) -> int:
        """Hash based on student and tutor profile IDs."""
        return hash((self.student_id, self.tutor_profile_id))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"FavoriteEntity(id={self.id}, student_id={self.student_id}, "
            f"tutor_profile_id={self.tutor_profile_id})"
        )
