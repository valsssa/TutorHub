"""
Domain entities for subjects module.

These are pure data classes representing the core subject domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import datetime

from core.datetime_utils import utc_now
from modules.subjects.domain.value_objects import (
    SubjectCategory,
    SubjectId,
    SubjectLevel,
    SubjectName,
)


@dataclass
class SubjectEntity:
    """
    Core subject domain entity.

    Represents a subject that can be taught by tutors and booked by students.
    """

    id: SubjectId | None
    name: str
    description: str | None = None
    category: SubjectCategory | None = None
    level: SubjectLevel | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(
        cls,
        name: str | SubjectName,
        description: str | None = None,
        category: str | SubjectCategory | None = None,
        level: str | SubjectLevel | None = None,
    ) -> "SubjectEntity":
        """
        Factory method to create a new subject with validation.

        Args:
            name: Subject name (will be validated)
            description: Optional description
            category: Optional category (string or enum)
            level: Optional level (string or enum)

        Returns:
            New SubjectEntity instance

        Raises:
            InvalidSubjectDataError: If validation fails
        """
        # Validate name
        validated_name = name if isinstance(name, SubjectName) else SubjectName(name)

        # Convert category if string
        validated_category: SubjectCategory | None = None
        if category is not None:
            validated_category = (
                category
                if isinstance(category, SubjectCategory)
                else SubjectCategory.from_string(category)
            )

        # Convert level if string
        validated_level: SubjectLevel | None = None
        if level is not None:
            validated_level = (
                level
                if isinstance(level, SubjectLevel)
                else SubjectLevel.from_string(level)
            )

        return cls(
            id=None,
            name=validated_name.value,
            description=description,
            category=validated_category,
            level=validated_level,
            is_active=True,
        )

    def update(
        self,
        name: str | SubjectName | None = None,
        description: str | None = None,
        category: str | SubjectCategory | None = None,
        level: str | SubjectLevel | None = None,
        is_active: bool | None = None,
    ) -> "SubjectEntity":
        """
        Create a new entity with updated fields.

        Args:
            name: New name (optional)
            description: New description (optional)
            category: New category (optional)
            level: New level (optional)
            is_active: New active status (optional)

        Returns:
            New SubjectEntity with updated fields

        Raises:
            InvalidSubjectDataError: If validation fails
        """
        # Validate new name if provided
        new_name = self.name
        if name is not None:
            validated_name = name if isinstance(name, SubjectName) else SubjectName(name)
            new_name = validated_name.value

        # Convert category if provided
        new_category = self.category
        if category is not None:
            new_category = (
                category
                if isinstance(category, SubjectCategory)
                else SubjectCategory.from_string(category)
            )

        # Convert level if provided
        new_level = self.level
        if level is not None:
            new_level = (
                level
                if isinstance(level, SubjectLevel)
                else SubjectLevel.from_string(level)
            )

        return SubjectEntity(
            id=self.id,
            name=new_name,
            description=description if description is not None else self.description,
            category=new_category,
            level=new_level,
            is_active=is_active if is_active is not None else self.is_active,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    def deactivate(self) -> "SubjectEntity":
        """
        Create a new entity with is_active set to False.

        Returns:
            New SubjectEntity with is_active=False
        """
        return SubjectEntity(
            id=self.id,
            name=self.name,
            description=self.description,
            category=self.category,
            level=self.level,
            is_active=False,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    def activate(self) -> "SubjectEntity":
        """
        Create a new entity with is_active set to True.

        Returns:
            New SubjectEntity with is_active=True
        """
        return SubjectEntity(
            id=self.id,
            name=self.name,
            description=self.description,
            category=self.category,
            level=self.level,
            is_active=True,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    @property
    def display_name(self) -> str:
        """Get display name with optional level suffix."""
        if self.level:
            return f"{self.name} ({self.level.value.replace('_', ' ').title()})"
        return self.name

    @property
    def is_categorized(self) -> bool:
        """Check if subject has a category assigned."""
        return self.category is not None
