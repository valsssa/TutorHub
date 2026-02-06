"""
Value objects for subjects module.

Immutable objects that represent domain concepts with validation.
"""

from enum import Enum
from typing import NewType

from modules.subjects.domain.exceptions import InvalidSubjectDataError

# Subject ID as a NewType wrapper for type safety
SubjectId = NewType("SubjectId", int)


class SubjectLevel(str, Enum):
    """
    Education level for a subject.

    Represents the academic level at which a subject is taught.
    """

    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    PROFESSIONAL = "professional"

    @classmethod
    def from_string(cls, value: str) -> "SubjectLevel":
        """
        Convert a string to SubjectLevel.

        Args:
            value: String representation of the level

        Returns:
            SubjectLevel enum value

        Raises:
            InvalidSubjectDataError: If value is not a valid level
        """
        value_lower = value.lower().replace(" ", "_").replace("-", "_")
        for level in cls:
            if level.value == value_lower:
                return level
        valid_levels = [level.value for level in cls]
        raise InvalidSubjectDataError(
            "level",
            f"Invalid level '{value}'. Valid levels: {', '.join(valid_levels)}",
        )


class SubjectCategory(str, Enum):
    """
    Category for grouping subjects.

    Used for organizing subjects into logical groups for browsing and filtering.
    """

    MATH = "math"
    SCIENCE = "science"
    LANGUAGE = "language"
    HUMANITIES = "humanities"
    ARTS = "arts"
    TECHNOLOGY = "technology"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str) -> "SubjectCategory":
        """
        Convert a string to SubjectCategory.

        Args:
            value: String representation of the category

        Returns:
            SubjectCategory enum value

        Raises:
            InvalidSubjectDataError: If value is not a valid category
        """
        value_lower = value.lower().replace(" ", "_").replace("-", "_")
        for category in cls:
            if category.value == value_lower:
                return category
        valid_categories = [c.value for c in cls]
        raise InvalidSubjectDataError(
            "category",
            f"Invalid category '{value}'. Valid categories: {', '.join(valid_categories)}",
        )


class SubjectName:
    """
    Value object for subject name with validation.

    Subject names must be between 2 and 100 characters.
    """

    MIN_LENGTH = 2
    MAX_LENGTH = 100

    def __init__(self, value: str):
        """
        Create a validated subject name.

        Args:
            value: The subject name string

        Raises:
            InvalidSubjectDataError: If the name is invalid
        """
        self._validate(value)
        self._value = value.strip()

    def _validate(self, value: str) -> None:
        """Validate the subject name."""
        if not value or not value.strip():
            raise InvalidSubjectDataError("name", "Subject name is required")

        stripped = value.strip()
        if len(stripped) < self.MIN_LENGTH:
            raise InvalidSubjectDataError(
                "name",
                f"Subject name must be at least {self.MIN_LENGTH} characters",
            )
        if len(stripped) > self.MAX_LENGTH:
            raise InvalidSubjectDataError(
                "name",
                f"Subject name must be at most {self.MAX_LENGTH} characters",
            )

    @property
    def value(self) -> str:
        """Get the validated name value."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"SubjectName({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SubjectName):
            return self._value.lower() == other._value.lower()
        if isinstance(other, str):
            return self._value.lower() == other.lower()
        return False

    def __hash__(self) -> int:
        return hash(self._value.lower())
