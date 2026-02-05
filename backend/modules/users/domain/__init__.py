"""
Users domain layer.

Contains domain entities, value objects, exceptions, events, handlers,
and repository interfaces for the users module.
This layer is independent of infrastructure concerns.
"""

from modules.users.domain.entities import UserEntity, UserPreferences
from modules.users.domain.events import RoleType, UserRoleChanged
from modules.users.domain.exceptions import (
    AvatarError,
    AvatarUploadError,
    DuplicateEmailError,
    InvalidAvatarError,
    InvalidCurrencyError,
    InvalidTimezoneError,
    InvalidUserStateError,
    UserDeactivatedError,
    UserError,
    UserNotFoundError,
)
from modules.users.domain.handlers import RoleChangeEventHandler
from modules.users.domain.repositories import UserRepository
from modules.users.domain.value_objects import (
    AvatarKey,
    Currency,
    Language,
    Timezone,
    UserId,
)

__all__ = [
    # Entities
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
    # Repository Protocols
    "UserRepository",
]
