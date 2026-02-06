"""
Students domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the student management system.
"""

from modules.students.domain.entities import StudentProfileEntity
from modules.students.domain.exceptions import (
    InvalidStudentDataError,
    StudentError,
    StudentNotFoundError,
    StudentProfileNotFoundError,
)
from modules.students.domain.repositories import StudentProfileRepository
from modules.students.domain.value_objects import (
    LEARNING_GOAL_MAX_LENGTH,
    LearningGoal,
    StudentId,
    StudentLevel,
    StudentProfileId,
)

__all__ = [
    # Entities
    "StudentProfileEntity",
    # Exceptions
    "StudentError",
    "StudentNotFoundError",
    "StudentProfileNotFoundError",
    "InvalidStudentDataError",
    # Value Objects
    "StudentId",
    "StudentProfileId",
    "StudentLevel",
    "LearningGoal",
    "LEARNING_GOAL_MAX_LENGTH",
    # Repository Interfaces
    "StudentProfileRepository",
]
