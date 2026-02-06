"""
Profiles domain layer.

Contains domain entities, value objects, exceptions, and repository protocols
for the user profiles system.
"""

from modules.profiles.domain.entities import UserProfileEntity
from modules.profiles.domain.exceptions import (
    AvatarUploadError,
    InvalidProfileDataError,
    InvalidTimezoneError,
    ProfileError,
    ProfileNotFoundError,
)
from modules.profiles.domain.repositories import UserProfileRepository
from modules.profiles.domain.value_objects import (
    Bio,
    PhoneNumber,
    ProfileId,
    Timezone,
    UserId,
)

__all__ = [
    "ProfileError",
    "ProfileNotFoundError",
    "InvalidProfileDataError",
    "AvatarUploadError",
    "InvalidTimezoneError",
    "ProfileId",
    "UserId",
    "Timezone",
    "PhoneNumber",
    "Bio",
    "UserProfileEntity",
    "UserProfileRepository",
]
