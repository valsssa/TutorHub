"""
Favorites domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the favorites module. This layer is independent of infrastructure concerns.
"""

from modules.favorites.domain.entities import FavoriteEntity
from modules.favorites.domain.exceptions import (
    DuplicateFavoriteError,
    FavoriteError,
    FavoriteNotFoundError,
    InvalidFavoriteTargetError,
    SelfFavoriteNotAllowedError,
)
from modules.favorites.domain.repositories import FavoriteRepository
from modules.favorites.domain.value_objects import (
    FavoriteId,
    TutorProfileId,
    UserId,
)

__all__ = [
    # Entities
    "FavoriteEntity",
    # Value Objects
    "FavoriteId",
    "UserId",
    "TutorProfileId",
    # Exceptions
    "FavoriteError",
    "FavoriteNotFoundError",
    "DuplicateFavoriteError",
    "InvalidFavoriteTargetError",
    "SelfFavoriteNotAllowedError",
    # Repository Protocols
    "FavoriteRepository",
]
