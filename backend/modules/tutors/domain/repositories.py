"""
Repository interfaces for tutors module.

Defines the contracts for tutor-related persistence operations.
"""

from typing import Protocol

from modules.tutors.domain.entities import (
    AvailabilityEntity,
    StudentNoteEntity,
    VideoSettingsEntity,
)
from modules.tutors.domain.value_objects import (
    AvailabilityId,
    StudentNoteId,
    TutorId,
    TutorProfileId,
    UserId,
)


class StudentNoteRepository(Protocol):
    """
    Protocol for student note repository operations.

    Implementations should handle:
    - Student note CRUD operations
    - Tutor and student-based queries
    """

    def get_by_id(self, note_id: StudentNoteId) -> StudentNoteEntity | None:
        """
        Get a student note by its ID.

        Args:
            note_id: Note's unique identifier

        Returns:
            StudentNoteEntity if found, None otherwise
        """
        ...

    def get_by_tutor_and_student(
        self,
        tutor_id: TutorId,
        student_id: UserId,
    ) -> StudentNoteEntity | None:
        """
        Get a note for a specific tutor-student pair.

        Args:
            tutor_id: Tutor's user ID
            student_id: Student's user ID

        Returns:
            StudentNoteEntity if found, None otherwise
        """
        ...

    def create(self, note: StudentNoteEntity) -> StudentNoteEntity:
        """
        Create a new student note.

        Args:
            note: Note entity to create

        Returns:
            Created note with populated ID
        """
        ...

    def update(self, note: StudentNoteEntity) -> StudentNoteEntity:
        """
        Update an existing student note.

        Args:
            note: Note entity with updated fields

        Returns:
            Updated note entity
        """
        ...

    def delete(self, note_id: StudentNoteId) -> bool:
        """
        Delete a student note by its ID.

        Args:
            note_id: Note's unique identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    def delete_by_tutor_and_student(
        self,
        tutor_id: TutorId,
        student_id: UserId,
    ) -> bool:
        """
        Delete a note by tutor and student IDs.

        Args:
            tutor_id: Tutor's user ID
            student_id: Student's user ID

        Returns:
            True if deleted, False if not found
        """
        ...

    def get_all_for_student(
        self,
        student_id: UserId,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentNoteEntity]:
        """
        Get all notes for a student across all tutors.

        Args:
            student_id: Student's user ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of student note entities
        """
        ...

    def get_all_for_tutor(
        self,
        tutor_id: TutorId,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentNoteEntity]:
        """
        Get all notes created by a tutor.

        Args:
            tutor_id: Tutor's user ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of student note entities
        """
        ...

    def count_for_tutor(self, tutor_id: TutorId) -> int:
        """
        Count notes created by a tutor.

        Args:
            tutor_id: Tutor's user ID

        Returns:
            Total count of notes
        """
        ...


class VideoSettingsRepository(Protocol):
    """
    Protocol for video settings repository operations.

    Implementations should handle:
    - Video settings CRUD operations
    - Tutor-based queries
    """

    def get_by_tutor(self, tutor_id: TutorProfileId) -> VideoSettingsEntity | None:
        """
        Get video settings for a tutor.

        Args:
            tutor_id: Tutor's profile ID

        Returns:
            VideoSettingsEntity if found, None otherwise
        """
        ...

    def create(self, settings: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Create new video settings.

        Args:
            settings: Settings entity to create

        Returns:
            Created settings with populated ID
        """
        ...

    def update(self, settings: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Update existing video settings.

        Args:
            settings: Settings entity with updated fields

        Returns:
            Updated settings entity
        """
        ...

    def upsert(self, settings: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Create or update video settings.

        If settings exist for the tutor, update them; otherwise create new.

        Args:
            settings: Settings entity to create or update

        Returns:
            Created or updated settings entity
        """
        ...


class AvailabilityRepository(Protocol):
    """
    Protocol for availability repository operations.

    Implementations should handle:
    - Availability CRUD operations
    - Bulk operations for setting weekly schedules
    - Conflict detection
    """

    def get_by_id(self, availability_id: AvailabilityId) -> AvailabilityEntity | None:
        """
        Get an availability slot by its ID.

        Args:
            availability_id: Availability's unique identifier

        Returns:
            AvailabilityEntity if found, None otherwise
        """
        ...

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        day_of_week: int | None = None,
    ) -> list[AvailabilityEntity]:
        """
        Get all availability slots for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            day_of_week: Optional filter by day of week (0-6)

        Returns:
            List of availability entities, ordered by day and start time
        """
        ...

    def create(self, availability: AvailabilityEntity) -> AvailabilityEntity:
        """
        Create a new availability slot.

        Args:
            availability: Availability entity to create

        Returns:
            Created availability with populated ID

        Raises:
            AvailabilityConflictError: If the slot conflicts with existing ones
        """
        ...

    def update(self, availability: AvailabilityEntity) -> AvailabilityEntity:
        """
        Update an existing availability slot.

        Args:
            availability: Availability entity with updated fields

        Returns:
            Updated availability entity

        Raises:
            AvailabilityConflictError: If the update would cause conflicts
        """
        ...

    def delete(self, availability_id: AvailabilityId) -> bool:
        """
        Delete an availability slot by its ID.

        Args:
            availability_id: Availability's unique identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    def set_availability(
        self,
        tutor_profile_id: TutorProfileId,
        availabilities: list[AvailabilityEntity],
    ) -> list[AvailabilityEntity]:
        """
        Replace all availability for a tutor with new slots.

        This is a bulk operation that:
        1. Deletes all existing availability for the tutor
        2. Creates the new availability slots
        3. Validates no internal conflicts

        Args:
            tutor_profile_id: Tutor's profile ID
            availabilities: List of new availability entities

        Returns:
            List of created availability entities

        Raises:
            AvailabilityConflictError: If the new slots conflict with each other
        """
        ...

    def clear_availability(self, tutor_profile_id: TutorProfileId) -> int:
        """
        Delete all availability for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Number of availability slots deleted
        """
        ...

    def check_conflicts(
        self,
        tutor_profile_id: TutorProfileId,
        availability: AvailabilityEntity,
        *,
        exclude_id: AvailabilityId | None = None,
    ) -> list[AvailabilityEntity]:
        """
        Check for conflicts with existing availability.

        Args:
            tutor_profile_id: Tutor's profile ID
            availability: Availability to check for conflicts
            exclude_id: Optional ID to exclude from conflict check (for updates)

        Returns:
            List of conflicting availability entities (empty if no conflicts)
        """
        ...

    def count_by_tutor(self, tutor_profile_id: TutorProfileId) -> int:
        """
        Count availability slots for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Total count of availability slots
        """
        ...

    def get_tutors_with_availability(
        self,
        day_of_week: int | None = None,
    ) -> list[TutorProfileId]:
        """
        Get IDs of tutors who have availability set.

        Args:
            day_of_week: Optional filter by day of week

        Returns:
            List of tutor profile IDs with availability
        """
        ...
