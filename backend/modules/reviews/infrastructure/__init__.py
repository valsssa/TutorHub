"""Infrastructure layer for reviews module.

Contains SQLAlchemy repository implementations and other infrastructure concerns.
"""

from modules.reviews.infrastructure.repositories import ReviewRepositoryImpl

__all__ = ["ReviewRepositoryImpl"]
