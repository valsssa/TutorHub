"""Infrastructure layer for students module.

Contains SQLAlchemy repository implementations for student profile persistence.
"""

from modules.students.infrastructure.repositories import StudentProfileRepositoryImpl

__all__ = [
    "StudentProfileRepositoryImpl",
]
