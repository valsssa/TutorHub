"""
Tutors domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the tutors module. This layer is independent of infrastructure concerns.
"""

from modules.tutors.domain.entities import (
    AvailabilityEntity,
    StudentNoteEntity,
    VideoSettingsEntity,
)
from modules.tutors.domain.exceptions import (
    AvailabilityConflictError,
    InvalidAvailabilityError,
    StudentNoteNotFoundError,
    TutorError,
    TutorNotFoundError,
    VideoSettingsError,
)
from modules.tutors.domain.repositories import (
    AvailabilityRepository,
    StudentNoteRepository,
    VideoSettingsRepository,
)
from modules.tutors.domain.value_objects import (
    AvailabilityId,
    DayOfWeek,
    StudentNoteId,
    TimeSlot,
    TutorId,
    TutorProfileId,
    UserId,
    VideoProvider,
    WeeklySchedule,
)

__all__ = [
    # Entities
    "StudentNoteEntity",
    "VideoSettingsEntity",
    "AvailabilityEntity",
    # Value Objects
    "TutorId",
    "TutorProfileId",
    "StudentNoteId",
    "UserId",
    "AvailabilityId",
    "VideoProvider",
    "TimeSlot",
    "WeeklySchedule",
    "DayOfWeek",
    # Exceptions
    "TutorError",
    "TutorNotFoundError",
    "StudentNoteNotFoundError",
    "AvailabilityConflictError",
    "VideoSettingsError",
    "InvalidAvailabilityError",
    # Repository Protocols
    "StudentNoteRepository",
    "VideoSettingsRepository",
    "AvailabilityRepository",
]
