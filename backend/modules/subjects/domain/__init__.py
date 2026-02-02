"""
Subjects domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the subjects management system.
"""

from modules.subjects.domain.entities import SubjectEntity
from modules.subjects.domain.exceptions import (
    DuplicateSubjectError,
    InvalidSubjectDataError,
    SubjectError,
    SubjectInUseError,
    SubjectNotFoundError,
)
from modules.subjects.domain.repositories import SubjectRepository
from modules.subjects.domain.value_objects import (
    SubjectCategory,
    SubjectId,
    SubjectLevel,
    SubjectName,
)

__all__ = [
    # Entities
    "SubjectEntity",
    # Value Objects
    "SubjectId",
    "SubjectName",
    "SubjectLevel",
    "SubjectCategory",
    # Exceptions
    "SubjectError",
    "SubjectNotFoundError",
    "DuplicateSubjectError",
    "SubjectInUseError",
    "InvalidSubjectDataError",
    # Repository Protocol
    "SubjectRepository",
]
