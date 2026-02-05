"""User module with avatar management, preferences, and currency functionality.

This module follows clean architecture principles with:
- domain/ - Entities, value objects, exceptions, events, handlers, and repository protocols
- infrastructure/ - SQLAlchemy repository implementations
- avatar/ - Avatar management sub-module (router, service, schemas)
- currency/ - Currency management sub-module (router)
- preferences/ - User preferences sub-module (router)
"""

from modules.users.domain import (
    AvatarError,
    AvatarKey,
    AvatarUploadError,
    Currency,
    DuplicateEmailError,
    InvalidAvatarError,
    InvalidCurrencyError,
    InvalidTimezoneError,
    InvalidUserStateError,
    Language,
    RoleChangeEventHandler,
    RoleType,
    Timezone,
    UserDeactivatedError,
    UserEntity,
    UserError,
    UserId,
    UserNotFoundError,
    UserPreferences,
    UserRepository,
    UserRoleChanged,
)
from modules.users.infrastructure import UserRepositoryImpl

__all__ = [
    # Domain Entities
    "UserEntity",
    "UserPreferences",
    # Value Objects
    "UserId",
    "Currency",
    "Timezone",
    "Language",
    "AvatarKey",
    # Events
    "UserRoleChanged",
    "RoleType",
    # Handlers
    "RoleChangeEventHandler",
    # Exceptions
    "UserError",
    "UserNotFoundError",
    "DuplicateEmailError",
    "InvalidUserStateError",
    "UserDeactivatedError",
    "InvalidCurrencyError",
    "InvalidTimezoneError",
    "AvatarError",
    "AvatarUploadError",
    "InvalidAvatarError",
    # Repository Protocol
    "UserRepository",
    # Repository Implementation
    "UserRepositoryImpl",
]
