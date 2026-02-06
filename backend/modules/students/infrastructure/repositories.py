"""SQLAlchemy repository implementation for students module.

Provides concrete implementation of the StudentProfileRepository protocol
defined in the domain layer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import StudentProfile, User
from modules.students.domain.entities import StudentProfileEntity
from modules.students.domain.exceptions import StudentProfileNotFoundError

logger = logging.getLogger(__name__)


class StudentProfileRepositoryImpl:
    """SQLAlchemy implementation of StudentProfileRepository.

    Handles persistence of student profile data.
    Uses soft delete filtering via the related User model.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, profile_id: int) -> StudentProfileEntity | None:
        """Get a student profile by its ID.

        Excludes profiles whose associated user is soft-deleted.

        Args:
            profile_id: Student profile's unique identifier

        Returns:
            StudentProfileEntity if found, None otherwise
        """
        model = (
            self._query_base()
            .filter(StudentProfile.id == profile_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_user_id(self, user_id: int) -> StudentProfileEntity | None:
        """Get a student profile by the user's ID.

        Excludes profiles whose associated user is soft-deleted.

        Args:
            user_id: User's unique identifier

        Returns:
            StudentProfileEntity if found, None otherwise
        """
        model = (
            self._query_base()
            .filter(StudentProfile.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def create(self, profile: StudentProfileEntity) -> StudentProfileEntity:
        """Create a new student profile.

        Args:
            profile: Student profile entity to create

        Returns:
            Created profile with populated ID

        Raises:
            InvalidStudentDataError: If profile data is invalid
        """
        model = self._to_model(profile)
        self.db.add(model)
        self.db.flush()

        logger.info(f"Created student profile for user {profile.user_id}")
        return self._to_entity(model)

    def update(self, profile: StudentProfileEntity) -> StudentProfileEntity:
        """Update an existing student profile.

        Args:
            profile: Student profile entity with updated fields

        Returns:
            Updated profile entity

        Raises:
            StudentProfileNotFoundError: If profile doesn't exist
        """
        if profile.id is None:
            raise StudentProfileNotFoundError()

        model = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.id == profile.id)
            .first()
        )
        if not model:
            raise StudentProfileNotFoundError(profile.id)

        # Update fields
        model.phone = profile.phone
        model.bio = profile.bio
        model.grade_level = profile.grade_level
        model.school_name = profile.school_name
        model.learning_goals = profile.learning_goals
        model.interests = profile.interests
        model.preferred_language = profile.preferred_language
        model.total_sessions = profile.total_sessions
        model.credit_balance_cents = profile.credit_balance_cents
        model.updated_at = datetime.now(UTC)

        self.db.flush()
        logger.info(f"Updated student profile {profile.id}")
        return self._to_entity(model)

    def delete(self, profile_id: int) -> bool:
        """Delete a student profile (soft delete via user model).

        Note: StudentProfile itself doesn't have soft delete.
        To properly soft-delete, use the User soft delete mechanism.
        This method performs a hard delete on the profile record.

        Args:
            profile_id: Student profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.id == profile_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(f"Deleted student profile {profile_id}")
        return result > 0

    def exists_by_user_id(self, user_id: int) -> bool:
        """Check if a student profile exists for the given user.

        Excludes profiles whose associated user is soft-deleted.

        Args:
            user_id: User ID to check

        Returns:
            True if profile exists, False otherwise
        """
        exists = (
            self._query_base()
            .filter(StudentProfile.user_id == user_id)
            .with_entities(StudentProfile.id)
            .first()
        )
        return exists is not None

    def list_profiles(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentProfileEntity]:
        """List student profiles with pagination.

        Excludes profiles whose associated user is soft-deleted.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of student profiles
        """
        offset = (page - 1) * page_size

        models = (
            self._query_base()
            .order_by(StudentProfile.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def count_profiles(self) -> int:
        """Count total number of student profiles.

        Excludes profiles whose associated user is soft-deleted.

        Returns:
            Total count of profiles
        """
        count = (
            self._query_base()
            .with_entities(func.count(StudentProfile.id))
            .scalar()
        )
        return count or 0

    def update_credit_balance(
        self,
        profile_id: int,
        amount_cents: int,
    ) -> bool:
        """Update a student's credit balance.

        Args:
            profile_id: Student profile ID
            amount_cents: New balance in cents

        Returns:
            True if updated, False if profile not found
        """
        model = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.id == profile_id)
            .first()
        )
        if not model:
            return False

        model.credit_balance_cents = amount_cents
        model.updated_at = datetime.now(UTC)
        self.db.flush()

        logger.info(
            f"Updated credit balance for student profile {profile_id}: "
            f"{amount_cents} cents"
        )
        return True

    def increment_session_count(self, profile_id: int) -> bool:
        """Increment a student's total session count.

        Args:
            profile_id: Student profile ID

        Returns:
            True if updated, False if profile not found
        """
        model = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.id == profile_id)
            .first()
        )
        if not model:
            return False

        model.total_sessions = (model.total_sessions or 0) + 1
        model.updated_at = datetime.now(UTC)
        self.db.flush()

        logger.info(
            f"Incremented session count for student profile {profile_id}: "
            f"{model.total_sessions} sessions"
        )
        return True

    def _query_base(self):
        """Base query for student profiles with soft delete filtering.

        Filters out profiles whose associated user is soft-deleted.
        Uses eager loading for the user relationship.

        Returns:
            SQLAlchemy query with filtering configured
        """
        return (
            self.db.query(StudentProfile)
            .options(joinedload(StudentProfile.user))
            .join(StudentProfile.user)
            .filter(User.deleted_at.is_(None))
        )

    def _to_entity(self, model: StudentProfile) -> StudentProfileEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: StudentProfile SQLAlchemy model

        Returns:
            StudentProfileEntity domain entity
        """
        return StudentProfileEntity(
            id=model.id,
            user_id=model.user_id,
            phone=model.phone,
            bio=model.bio,
            grade_level=model.grade_level,
            school_name=model.school_name,
            learning_goals=model.learning_goals,
            interests=model.interests,
            preferred_subjects=[],  # Not stored in model, would need join
            preferred_language=model.preferred_language,
            total_sessions=model.total_sessions or 0,
            credit_balance_cents=model.credit_balance_cents or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: StudentProfileEntity) -> StudentProfile:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: StudentProfileEntity domain entity

        Returns:
            StudentProfile SQLAlchemy model
        """
        return StudentProfile(
            id=entity.id,
            user_id=entity.user_id,
            phone=entity.phone,
            bio=entity.bio,
            grade_level=entity.grade_level,
            school_name=entity.school_name,
            learning_goals=entity.learning_goals,
            interests=entity.interests,
            preferred_language=entity.preferred_language,
            total_sessions=entity.total_sessions,
            credit_balance_cents=entity.credit_balance_cents,
        )
