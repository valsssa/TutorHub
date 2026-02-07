"""
SQLAlchemy repository implementations for tutors module.

Provides concrete implementations of the repository protocols defined
in the domain layer for student notes, video settings, and availability.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from core.datetime_utils import utc_now

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.students import StudentNote
from models.tutors import TutorAvailability, TutorProfile
from modules.tutors.domain.entities import (
    AvailabilityEntity,
    StudentNoteEntity,
    VideoSettingsEntity,
)
from modules.tutors.domain.exceptions import AvailabilityConflictError
from modules.tutors.domain.value_objects import (
    AvailabilityId,
    StudentNoteId,
    TutorId,
    TutorProfileId,
    UserId,
    VideoProvider,
)

logger = logging.getLogger(__name__)


class StudentNoteRepositoryImpl:
    """
    SQLAlchemy implementation of StudentNoteRepository.

    Handles persistence of tutor's private notes about students.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, note_id: StudentNoteId) -> StudentNoteEntity | None:
        """
        Get a student note by its ID.

        Args:
            note_id: Note's unique identifier

        Returns:
            StudentNoteEntity if found, None otherwise
        """
        note = self.db.query(StudentNote).filter(StudentNote.id == note_id).first()
        if not note:
            return None
        return self._to_entity(note)

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
        note = (
            self.db.query(StudentNote)
            .filter(
                StudentNote.tutor_id == tutor_id,
                StudentNote.student_id == student_id,
            )
            .first()
        )
        if not note:
            return None
        return self._to_entity(note)

    def create(self, entity: StudentNoteEntity) -> StudentNoteEntity:
        """
        Create a new student note.

        Args:
            entity: Note entity to create

        Returns:
            Created note with populated ID
        """
        now = utc_now()
        model = StudentNote(
            tutor_id=entity.tutor_id,
            student_id=entity.student_id,
            notes=entity.content,
            created_at=now,
            updated_at=now,
        )

        self.db.add(model)
        self.db.flush()

        logger.info(
            "Created student note for tutor %d and student %d",
            entity.tutor_id,
            entity.student_id,
        )

        return self._to_entity(model)

    def update(self, entity: StudentNoteEntity) -> StudentNoteEntity:
        """
        Update an existing student note.

        Args:
            entity: Note entity with updated fields

        Returns:
            Updated note entity

        Raises:
            ValueError: If note ID is not provided or note not found
        """
        if entity.id is None:
            raise ValueError("Cannot update note without ID")

        model = self.db.query(StudentNote).filter(StudentNote.id == entity.id).first()
        if not model:
            raise ValueError(f"Student note with ID {entity.id} not found")

        model.notes = entity.content
        model.updated_at = utc_now()

        self.db.flush()

        logger.info("Updated student note %d", entity.id)

        return self._to_entity(model)

    def delete(self, note_id: StudentNoteId) -> bool:
        """
        Delete a student note by its ID.

        Args:
            note_id: Note's unique identifier

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.db.query(StudentNote)
            .filter(StudentNote.id == note_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info("Deleted student note %d", note_id)
        return result > 0

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
        result = (
            self.db.query(StudentNote)
            .filter(
                StudentNote.tutor_id == tutor_id,
                StudentNote.student_id == student_id,
            )
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(
                "Deleted student note for tutor %d and student %d",
                tutor_id,
                student_id,
            )
        return result > 0

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
        offset = (page - 1) * page_size
        notes = (
            self.db.query(StudentNote)
            .filter(StudentNote.student_id == student_id)
            .order_by(StudentNote.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return [self._to_entity(note) for note in notes]

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
        offset = (page - 1) * page_size
        notes = (
            self.db.query(StudentNote)
            .filter(StudentNote.tutor_id == tutor_id)
            .order_by(StudentNote.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return [self._to_entity(note) for note in notes]

    def count_for_tutor(self, tutor_id: TutorId) -> int:
        """
        Count notes created by a tutor.

        Args:
            tutor_id: Tutor's user ID

        Returns:
            Total count of notes
        """
        return (
            self.db.query(StudentNote)
            .filter(StudentNote.tutor_id == tutor_id)
            .count()
        )

    def _to_entity(self, model: StudentNote) -> StudentNoteEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: StudentNote SQLAlchemy model

        Returns:
            StudentNoteEntity domain object
        """
        return StudentNoteEntity(
            id=StudentNoteId(model.id) if model.id else None,
            tutor_id=TutorId(model.tutor_id),
            student_id=UserId(model.student_id),
            content=model.notes,
            is_private=True,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class VideoSettingsRepositoryImpl:
    """
    SQLAlchemy implementation of VideoSettingsRepository.

    Video settings are stored as fields on the TutorProfile model:
    - preferred_video_provider
    - custom_meeting_url_template
    - video_provider_configured
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_tutor(self, tutor_id: TutorProfileId) -> VideoSettingsEntity | None:
        """
        Get video settings for a tutor.

        Args:
            tutor_id: Tutor's profile ID

        Returns:
            VideoSettingsEntity if found, None otherwise
        """
        profile = (
            self.db.query(TutorProfile)
            .filter(
                TutorProfile.id == tutor_id,
                TutorProfile.deleted_at.is_(None),
            )
            .first()
        )
        if not profile:
            return None
        return self._to_entity(profile)

    def create(self, entity: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Create new video settings.

        Since video settings are stored on TutorProfile, this updates
        an existing profile's video fields.

        Args:
            entity: Settings entity to create

        Returns:
            Created settings with populated ID

        Raises:
            ValueError: If tutor profile not found
        """
        profile = (
            self.db.query(TutorProfile)
            .filter(
                TutorProfile.id == entity.tutor_id,
                TutorProfile.deleted_at.is_(None),
            )
            .first()
        )
        if not profile:
            raise ValueError(f"Tutor profile with ID {entity.tutor_id} not found")

        profile.preferred_video_provider = entity.preferred_provider.value
        profile.custom_meeting_url_template = entity.custom_meeting_url
        profile.video_provider_configured = entity.is_configured
        profile.updated_at = utc_now()

        self.db.flush()

        logger.info(
            "Created video settings for tutor profile %d: provider=%s",
            entity.tutor_id,
            entity.preferred_provider.value,
        )

        return self._to_entity(profile)

    def update(self, entity: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Update existing video settings.

        Args:
            entity: Settings entity with updated fields

        Returns:
            Updated settings entity

        Raises:
            ValueError: If tutor profile not found
        """
        profile = (
            self.db.query(TutorProfile)
            .filter(
                TutorProfile.id == entity.tutor_id,
                TutorProfile.deleted_at.is_(None),
            )
            .first()
        )
        if not profile:
            raise ValueError(f"Tutor profile with ID {entity.tutor_id} not found")

        profile.preferred_video_provider = entity.preferred_provider.value
        profile.custom_meeting_url_template = entity.custom_meeting_url
        profile.video_provider_configured = entity.is_configured
        profile.updated_at = utc_now()

        self.db.flush()

        logger.info(
            "Updated video settings for tutor profile %d: provider=%s",
            entity.tutor_id,
            entity.preferred_provider.value,
        )

        return self._to_entity(profile)

    def upsert(self, entity: VideoSettingsEntity) -> VideoSettingsEntity:
        """
        Create or update video settings.

        If settings exist for the tutor, update them; otherwise create new.

        Args:
            entity: Settings entity to create or update

        Returns:
            Created or updated settings entity
        """
        existing = self.get_by_tutor(entity.tutor_id)
        if existing:
            return self.update(entity)
        return self.create(entity)

    def _to_entity(self, profile: TutorProfile) -> VideoSettingsEntity:
        """
        Convert TutorProfile model to VideoSettingsEntity.

        Args:
            profile: TutorProfile SQLAlchemy model

        Returns:
            VideoSettingsEntity domain object
        """
        provider_value = profile.preferred_video_provider or "zoom"
        try:
            provider = VideoProvider(provider_value)
        except ValueError:
            provider = VideoProvider.ZOOM

        return VideoSettingsEntity(
            id=profile.id,
            tutor_id=TutorProfileId(profile.id),
            preferred_provider=provider,
            custom_meeting_url=profile.custom_meeting_url_template,
            auto_create_meeting=True,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class AvailabilityRepositoryImpl:
    """
    SQLAlchemy implementation of AvailabilityRepository.

    Handles persistence of tutor availability slots.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, availability_id: AvailabilityId) -> AvailabilityEntity | None:
        """
        Get an availability slot by its ID.

        Args:
            availability_id: Availability's unique identifier

        Returns:
            AvailabilityEntity if found, None otherwise
        """
        availability = (
            self.db.query(TutorAvailability)
            .filter(TutorAvailability.id == availability_id)
            .first()
        )
        if not availability:
            return None
        return self._to_entity(availability)

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
        query = self.db.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile_id
        )

        if day_of_week is not None:
            query = query.filter(TutorAvailability.day_of_week == day_of_week)

        availabilities = (
            query.order_by(
                TutorAvailability.day_of_week,
                TutorAvailability.start_time,
            )
            .all()
        )
        return [self._to_entity(a) for a in availabilities]

    def create(self, entity: AvailabilityEntity) -> AvailabilityEntity:
        """
        Create a new availability slot.

        Args:
            entity: Availability entity to create

        Returns:
            Created availability with populated ID

        Raises:
            AvailabilityConflictError: If the slot conflicts with existing ones
        """
        conflicts = self.check_conflicts(entity.tutor_profile_id, entity)
        if conflicts:
            conflict = conflicts[0]
            raise AvailabilityConflictError(
                day_of_week=entity.day_of_week,
                start_time=str(entity.start_time),
                end_time=str(entity.end_time),
                conflicting_start=str(conflict.start_time),
                conflicting_end=str(conflict.end_time),
            )

        now = utc_now()
        model = TutorAvailability(
            tutor_profile_id=entity.tutor_profile_id,
            day_of_week=entity.day_of_week,
            start_time=entity.start_time,
            end_time=entity.end_time,
            timezone=entity.timezone,
            is_recurring=entity.is_recurring,
            created_at=now,
        )

        self.db.add(model)
        self.db.flush()

        logger.info(
            "Created availability for tutor profile %d: %s %s-%s",
            entity.tutor_profile_id,
            entity.day_name,
            entity.start_time,
            entity.end_time,
        )

        return self._to_entity(model)

    def update(self, entity: AvailabilityEntity) -> AvailabilityEntity:
        """
        Update an existing availability slot.

        Args:
            entity: Availability entity with updated fields

        Returns:
            Updated availability entity

        Raises:
            ValueError: If availability ID not provided or not found
            AvailabilityConflictError: If the update would cause conflicts
        """
        if entity.id is None:
            raise ValueError("Cannot update availability without ID")

        model = (
            self.db.query(TutorAvailability)
            .filter(TutorAvailability.id == entity.id)
            .first()
        )
        if not model:
            raise ValueError(f"Availability with ID {entity.id} not found")

        conflicts = self.check_conflicts(
            entity.tutor_profile_id,
            entity,
            exclude_id=entity.id,
        )
        if conflicts:
            conflict = conflicts[0]
            raise AvailabilityConflictError(
                day_of_week=entity.day_of_week,
                start_time=str(entity.start_time),
                end_time=str(entity.end_time),
                conflicting_start=str(conflict.start_time),
                conflicting_end=str(conflict.end_time),
            )

        model.day_of_week = entity.day_of_week
        model.start_time = entity.start_time
        model.end_time = entity.end_time
        model.timezone = entity.timezone
        model.is_recurring = entity.is_recurring

        self.db.flush()

        logger.info(
            "Updated availability %d: %s %s-%s",
            entity.id,
            entity.day_name,
            entity.start_time,
            entity.end_time,
        )

        return self._to_entity(model)

    def delete(self, availability_id: AvailabilityId) -> bool:
        """
        Delete an availability slot by its ID.

        Args:
            availability_id: Availability's unique identifier

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.db.query(TutorAvailability)
            .filter(TutorAvailability.id == availability_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info("Deleted availability %d", availability_id)
        return result > 0

    def set_availability(
        self,
        tutor_profile_id: TutorProfileId,
        availabilities: list[AvailabilityEntity],
    ) -> list[AvailabilityEntity]:
        """
        Replace all availability for a tutor with new slots.

        This is a bulk operation that:
        1. Validates no internal conflicts in the new slots
        2. Deletes all existing availability for the tutor
        3. Creates the new availability slots

        Args:
            tutor_profile_id: Tutor's profile ID
            availabilities: List of new availability entities

        Returns:
            List of created availability entities

        Raises:
            AvailabilityConflictError: If the new slots conflict with each other
        """
        self._validate_no_internal_conflicts(availabilities)

        self.clear_availability(tutor_profile_id)

        created: list[AvailabilityEntity] = []
        now = utc_now()

        for entity in availabilities:
            model = TutorAvailability(
                tutor_profile_id=tutor_profile_id,
                day_of_week=entity.day_of_week,
                start_time=entity.start_time,
                end_time=entity.end_time,
                timezone=entity.timezone,
                is_recurring=entity.is_recurring,
                created_at=now,
            )
            self.db.add(model)
            self.db.flush()
            created.append(self._to_entity(model))

        logger.info(
            "Set %d availability slots for tutor profile %d",
            len(created),
            tutor_profile_id,
        )

        return created

    def clear_availability(self, tutor_profile_id: TutorProfileId) -> int:
        """
        Delete all availability for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Number of availability slots deleted
        """
        result = (
            self.db.query(TutorAvailability)
            .filter(TutorAvailability.tutor_profile_id == tutor_profile_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(
                "Cleared %d availability slots for tutor profile %d",
                result,
                tutor_profile_id,
            )
        return result

    def check_conflicts(
        self,
        tutor_profile_id: TutorProfileId,
        availability: AvailabilityEntity,
        *,
        exclude_id: AvailabilityId | None = None,
    ) -> list[AvailabilityEntity]:
        """
        Check for conflicts with existing availability.

        Two slots conflict if they are on the same day and their times overlap.

        Args:
            tutor_profile_id: Tutor's profile ID
            availability: Availability to check for conflicts
            exclude_id: Optional ID to exclude from conflict check (for updates)

        Returns:
            List of conflicting availability entities (empty if no conflicts)
        """
        query = self.db.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile_id,
            TutorAvailability.day_of_week == availability.day_of_week,
            and_(
                TutorAvailability.start_time < availability.end_time,
                TutorAvailability.end_time > availability.start_time,
            ),
        )

        if exclude_id is not None:
            query = query.filter(TutorAvailability.id != exclude_id)

        conflicts = query.all()
        return [self._to_entity(c) for c in conflicts]

    def count_by_tutor(self, tutor_profile_id: TutorProfileId) -> int:
        """
        Count availability slots for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Total count of availability slots
        """
        return (
            self.db.query(TutorAvailability)
            .filter(TutorAvailability.tutor_profile_id == tutor_profile_id)
            .count()
        )

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
        query = self.db.query(TutorAvailability.tutor_profile_id).distinct()

        if day_of_week is not None:
            query = query.filter(TutorAvailability.day_of_week == day_of_week)

        results = query.all()
        return [TutorProfileId(r[0]) for r in results]

    def _validate_no_internal_conflicts(
        self,
        availabilities: list[AvailabilityEntity],
    ) -> None:
        """
        Validate that a list of availabilities has no internal conflicts.

        Args:
            availabilities: List of availability entities to validate

        Raises:
            AvailabilityConflictError: If any slots conflict with each other
        """
        for i, slot_a in enumerate(availabilities):
            for slot_b in availabilities[i + 1:]:
                if slot_a.overlaps_with(slot_b):
                    raise AvailabilityConflictError(
                        day_of_week=slot_a.day_of_week,
                        start_time=str(slot_a.start_time),
                        end_time=str(slot_a.end_time),
                        conflicting_start=str(slot_b.start_time),
                        conflicting_end=str(slot_b.end_time),
                    )

    def _to_entity(self, model: TutorAvailability) -> AvailabilityEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: TutorAvailability SQLAlchemy model

        Returns:
            AvailabilityEntity domain object
        """
        return AvailabilityEntity(
            id=AvailabilityId(model.id) if model.id else None,
            tutor_profile_id=TutorProfileId(model.tutor_profile_id),
            day_of_week=model.day_of_week,
            start_time=model.start_time,
            end_time=model.end_time,
            timezone=model.timezone or "UTC",
            is_recurring=model.is_recurring if model.is_recurring is not None else True,
            created_at=model.created_at,
        )
