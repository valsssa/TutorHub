"""Infrastructure layer for favorites module.

Contains SQLAlchemy repository implementations for favorite persistence.
"""

from modules.favorites.infrastructure.repositories import FavoriteRepositoryImpl

__all__ = [
    "FavoriteRepositoryImpl",
]
