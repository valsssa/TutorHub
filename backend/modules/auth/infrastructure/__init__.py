"""Auth infrastructure layer.

Provides SQLAlchemy implementations of auth domain repository protocols.
"""

from modules.auth.domain.repositories import UserRepository
from .repository import UserRepositoryImpl

__all__ = ["UserRepository", "UserRepositoryImpl"]
