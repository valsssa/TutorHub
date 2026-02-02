"""
Domain entities for tutors module.

These are pure data classes representing the core tutor domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import datetime, time

from modules.tutors.domain.value_objects import (
    AvailabilityId,
    StudentNoteId,
    TimeSlot,
    TutorId,
    TutorProfileId,
    UserId,
    VideoProvider,
)


@dataclass
class StudentNoteEntity:
    """
    Domain entity representing a tutor's private note about a student.

    Tutors can keep private notes about their students to track progress,
    learning styles, and other relevant information.
    """

    id: StudentNoteId | None
    tutor_id: TutorId
    student_id: UserId
    content: str | None
    is_private: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_persisted(self) -> bool:
        """Check if the note has been persisted (has an ID)."""
        return self.id is not None

    @property
    def has_content(self) -> bool:
        """Check if the note has any content."""
        return bool(self.content and self.content.strip())

    def update_content(self, new_content: str | None) -> "StudentNoteEntity":
        """
        Create a new entity with updated content.

        Returns:
            New StudentNoteEntity with updated content and timestamp
        """
        return StudentNoteEntity(
            id=self.id,
            tutor_id=self.tutor_id,
            student_id=self.student_id,
            content=new_content,
            is_private=self.is_private,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def __eq__(self, other: object) -> bool:
        """Compare notes by their tutor and student IDs."""
        if not isinstance(other, StudentNoteEntity):
            return NotImplemented
        return self.tutor_id == other.tutor_id and self.student_id == other.student_id

    def __hash__(self) -> int:
        """Hash based on tutor and student IDs."""
        return hash((self.tutor_id, self.student_id))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StudentNoteEntity(id={self.id}, tutor_id={self.tutor_id}, "
            f"student_id={self.student_id})"
        )


@dataclass
class VideoSettingsEntity:
    """
    Domain entity representing a tutor's video meeting settings.

    Stores the tutor's preferred video conferencing provider and
    any custom meeting URL configuration.
    """

    id: int | None
    tutor_id: TutorProfileId
    preferred_provider: VideoProvider
    custom_meeting_url: str | None = None
    auto_create_meeting: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_persisted(self) -> bool:
        """Check if settings have been persisted (has an ID)."""
        return self.id is not None

    @property
    def is_configured(self) -> bool:
        """Check if video settings are properly configured."""
        if self.preferred_provider == VideoProvider.CUSTOM:
            return bool(self.custom_meeting_url)
        if self.preferred_provider == VideoProvider.TEAMS:
            return bool(self.custom_meeting_url)
        return True

    @property
    def requires_custom_url(self) -> bool:
        """Check if the provider requires a custom meeting URL."""
        return self.preferred_provider in (VideoProvider.CUSTOM, VideoProvider.TEAMS)

    def update_provider(
        self,
        provider: VideoProvider,
        custom_url: str | None = None,
    ) -> "VideoSettingsEntity":
        """
        Create a new entity with updated provider settings.

        Returns:
            New VideoSettingsEntity with updated provider and URL
        """
        return VideoSettingsEntity(
            id=self.id,
            tutor_id=self.tutor_id,
            preferred_provider=provider,
            custom_meeting_url=custom_url,
            auto_create_meeting=self.auto_create_meeting,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def __eq__(self, other: object) -> bool:
        """Compare settings by tutor ID."""
        if not isinstance(other, VideoSettingsEntity):
            return NotImplemented
        return self.tutor_id == other.tutor_id

    def __hash__(self) -> int:
        """Hash based on tutor ID."""
        return hash(self.tutor_id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"VideoSettingsEntity(id={self.id}, tutor_id={self.tutor_id}, "
            f"provider={self.preferred_provider.value})"
        )


@dataclass
class AvailabilityEntity:
    """
    Domain entity representing a tutor's availability slot.

    Defines recurring weekly time slots when a tutor is available
    for tutoring sessions.
    """

    id: AvailabilityId | None
    tutor_profile_id: TutorProfileId
    day_of_week: int  # 0=Sunday, 1=Monday, ..., 6=Saturday
    start_time: time
    end_time: time
    timezone: str = "UTC"
    is_recurring: bool = True
    created_at: datetime | None = None

    @property
    def is_persisted(self) -> bool:
        """Check if the availability has been persisted (has an ID)."""
        return self.id is not None

    @property
    def time_slot(self) -> TimeSlot:
        """Get the time slot as a value object."""
        return TimeSlot(
            start_time=self.start_time,
            end_time=self.end_time,
            timezone=self.timezone,
        )

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return self.time_slot.duration_minutes

    @property
    def day_name(self) -> str:
        """Get human-readable day name."""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]

    def overlaps_with(self, other: "AvailabilityEntity") -> bool:
        """
        Check if this availability overlaps with another.

        Only considers slots on the same day.
        """
        if self.day_of_week != other.day_of_week:
            return False
        return self.time_slot.overlaps_with(other.time_slot)

    def is_valid(self) -> tuple[bool, str | None]:
        """
        Validate the availability entity.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not 0 <= self.day_of_week <= 6:
            return False, f"Invalid day of week: {self.day_of_week}"

        if self.start_time >= self.end_time:
            return False, f"Start time {self.start_time} must be before end time {self.end_time}"

        return True, None

    def __eq__(self, other: object) -> bool:
        """Compare availabilities by profile, day, and times."""
        if not isinstance(other, AvailabilityEntity):
            return NotImplemented
        return (
            self.tutor_profile_id == other.tutor_profile_id
            and self.day_of_week == other.day_of_week
            and self.start_time == other.start_time
            and self.end_time == other.end_time
        )

    def __hash__(self) -> int:
        """Hash based on profile, day, and times."""
        return hash((self.tutor_profile_id, self.day_of_week, self.start_time, self.end_time))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AvailabilityEntity(id={self.id}, tutor_profile_id={self.tutor_profile_id}, "
            f"day={self.day_name}, {self.start_time}-{self.end_time})"
        )
