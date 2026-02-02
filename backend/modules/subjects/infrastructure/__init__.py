"""Infrastructure layer for subjects module.

Contains SQLAlchemy repository implementations and other infrastructure concerns.
"""

from modules.subjects.infrastructure.repositories import SubjectRepositoryImpl

__all__ = ["SubjectRepositoryImpl"]
