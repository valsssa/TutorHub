"""
Value objects for the tutors domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from dataclasses import dataclass
from datetime import time
from enum import Enum
from typing import NewType

from modules.tutors.domain.exceptions import InvalidAvailabilityError

# Type aliases for IDs - provides type safety without runtime overhead
TutorId = NewType("TutorId", int)
TutorProfileId = NewType("TutorProfileId", int)
StudentNoteId = NewType("StudentNoteId", int)
UserId = NewType("UserId", int)
AvailabilityId = NewType("AvailabilityId", int)


class VideoProvider(str, Enum):
    """
    Video meeting provider options.

    Supported providers for video conferencing during tutoring sessions.
    """

    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    CUSTOM = "custom"
    MANUAL = "manual"

    @classmethod
    def get_all(cls) -> list[str]:
        """Get all valid provider values."""
        return [provider.value for provider in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid video provider."""
        return value in cls.get_all()


@dataclass(frozen=True)
class TimeSlot:
    """
    Value object representing a time slot within a day.

    Immutable and validates that start_time is before end_time.
    """

    start_time: time
    end_time: time
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Validate time slot configuration."""
        if self.start_time >= self.end_time:
            raise InvalidAvailabilityError(
                reason=f"Start time {self.start_time} must be before end time {self.end_time}",
                start_time=str(self.start_time),
                end_time=str(self.end_time),
            )

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """
        Check if this time slot overlaps with another.

        Two time slots overlap if: start1 < end2 AND end1 > start2
        """
        return self.start_time < other.end_time and self.end_time > other.start_time

    def contains(self, other: "TimeSlot") -> bool:
        """Check if this time slot fully contains another."""
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def __str__(self) -> str:
        """Format as HH:MM-HH:MM."""
        return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


@dataclass(frozen=True)
class WeeklySchedule:
    """
    Value object representing a weekly schedule entry.

    Combines day of week with time slot information.
    """

    day_of_week: int  # 0=Sunday, 1=Monday, ..., 6=Saturday
    slot: TimeSlot

    def __post_init__(self) -> None:
        """Validate day of week."""
        if not 0 <= self.day_of_week <= 6:
            raise InvalidAvailabilityError(
                reason=f"Day of week must be between 0 and 6, got {self.day_of_week}",
                day_of_week=self.day_of_week,
            )

    @property
    def start_time(self) -> time:
        """Get start time from slot."""
        return self.slot.start_time

    @property
    def end_time(self) -> time:
        """Get end time from slot."""
        return self.slot.end_time

    @property
    def timezone(self) -> str:
        """Get timezone from slot."""
        return self.slot.timezone

    @property
    def day_name(self) -> str:
        """Get human-readable day name."""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]

    def overlaps_with(self, other: "WeeklySchedule") -> bool:
        """
        Check if this schedule overlaps with another.

        Overlaps only if on the same day and time slots overlap.
        """
        if self.day_of_week != other.day_of_week:
            return False
        return self.slot.overlaps_with(other.slot)

    def __str__(self) -> str:
        """Format as 'Day HH:MM-HH:MM'."""
        return f"{self.day_name} {self.slot}"


@dataclass(frozen=True)
class DayOfWeek:
    """Value object representing a day of the week."""

    value: int  # 0=Sunday, 1=Monday, ..., 6=Saturday

    def __post_init__(self) -> None:
        """Validate day of week value."""
        if not 0 <= self.value <= 6:
            raise InvalidAvailabilityError(
                reason=f"Day of week must be between 0 and 6, got {self.value}",
                day_of_week=self.value,
            )

    @property
    def name(self) -> str:
        """Get human-readable day name."""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.value]

    @property
    def short_name(self) -> str:
        """Get short day name (3 letters)."""
        return self.name[:3]

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __str__(self) -> str:
        """String representation."""
        return self.name
