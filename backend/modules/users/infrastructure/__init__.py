"""Infrastructure layer for users module.

Contains SQLAlchemy repository implementations for user persistence.
"""

from modules.users.infrastructure.repositories import UserRepositoryImpl

__all__ = [
    "UserRepositoryImpl",
]
