"""Infrastructure layer for profiles module.

Contains SQLAlchemy repository implementations for user profile persistence.
"""

from modules.profiles.infrastructure.repositories import UserProfileRepositoryImpl

__all__ = [
    "UserProfileRepositoryImpl",
]
