"""
Value objects for students module.

Immutable objects that represent concepts with no identity, only values.
"""

from enum import Enum
from typing import NewType

# Type-safe ID wrappers
StudentId = NewType("StudentId", int)
StudentProfileId = NewType("StudentProfileId", int)


class StudentLevel(str, Enum):
    """
    Student proficiency level.

    Used to match students with appropriate tutors and content.
    """

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


# Learning goal constraints
LEARNING_GOAL_MAX_LENGTH = 2000


class LearningGoal:
    """
    Value object representing a student's learning goal.

    Immutable and validated at construction time.
    """

    __slots__ = ("_text",)

    def __init__(self, text: str):
        """
        Create a new learning goal.

        Args:
            text: The learning goal text

        Raises:
            ValueError: If text exceeds max length or is empty
        """
        if not text or not text.strip():
            raise ValueError("Learning goal cannot be empty")
        if len(text) > LEARNING_GOAL_MAX_LENGTH:
            raise ValueError(
                f"Learning goal exceeds maximum length of {LEARNING_GOAL_MAX_LENGTH} characters"
            )
        self._text = text.strip()

    @property
    def text(self) -> str:
        """Get the learning goal text."""
        return self._text

    def __str__(self) -> str:
        """Return string representation."""
        return self._text

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"LearningGoal({self._text!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another learning goal."""
        if isinstance(other, LearningGoal):
            return self._text == other._text
        if isinstance(other, str):
            return self._text == other
        return False

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return hash(self._text)

    def __len__(self) -> int:
        """Return length of the learning goal text."""
        return len(self._text)
