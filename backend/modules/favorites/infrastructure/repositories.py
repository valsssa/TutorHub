"""SQLAlchemy repository implementation for favorites module.

Provides concrete implementation of the FavoriteRepository protocol
defined in the domain layer.
"""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import FavoriteTutor

from modules.favorites.domain.entities import FavoriteEntity
from modules.favorites.domain.exceptions import DuplicateFavoriteError
from modules.favorites.domain.value_objects import (
    FavoriteId,
    TutorProfileId,
    UserId,
)

logger = logging.getLogger(__name__)


class FavoriteRepositoryImpl:
    """SQLAlchemy implementation of FavoriteRepository.

    Handles persistence of favorite relationships between students and tutors.
    Uses hard delete (no soft delete) for removing favorites.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, favorite_id: FavoriteId) -> FavoriteEntity | None:
        """Get a favorite by its ID.

        Args:
            favorite_id: Favorite's unique identifier

        Returns:
            FavoriteEntity if found, None otherwise
        """
        model = (
            self.db.query(FavoriteTutor)
            .filter(FavoriteTutor.id == favorite_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_student(
        self,
        student_id: UserId,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[FavoriteEntity]:
        """Get all favorites for a student with pagination.

        Args:
            student_id: Student's user ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of favorite entities for the student
        """
        query = (
            self.db.query(FavoriteTutor)
            .filter(FavoriteTutor.student_id == student_id)
            .order_by(FavoriteTutor.created_at.desc())
        )

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def is_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> bool:
        """Check if a tutor is favorited by a student.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            True if the tutor is favorited, False otherwise
        """
        exists = (
            self.db.query(FavoriteTutor.id)
            .filter(
                FavoriteTutor.student_id == student_id,
                FavoriteTutor.tutor_profile_id == tutor_profile_id,
            )
            .first()
        )
        return exists is not None

    def get_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> FavoriteEntity | None:
        """Get a specific favorite by student and tutor profile.

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            FavoriteEntity if found, None otherwise
        """
        model = (
            self.db.query(FavoriteTutor)
            .filter(
                FavoriteTutor.student_id == student_id,
                FavoriteTutor.tutor_profile_id == tutor_profile_id,
            )
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def add_favorite(self, favorite: FavoriteEntity) -> FavoriteEntity:
        """Add a new favorite.

        Args:
            favorite: Favorite entity to create

        Returns:
            Created favorite with populated ID

        Raises:
            DuplicateFavoriteError: If the favorite already exists
        """
        model = self._to_model(favorite)

        try:
            self.db.add(model)
            self.db.flush()
            logger.info(
                f"Added favorite: student {favorite.student_id} "
                f"favorited tutor profile {favorite.tutor_profile_id}"
            )
            return self._to_entity(model)
        except IntegrityError:
            self.db.rollback()
            logger.warning(
                f"Duplicate favorite: student {favorite.student_id} "
                f"already favorited tutor profile {favorite.tutor_profile_id}"
            )
            raise DuplicateFavoriteError(
                student_id=int(favorite.student_id),
                tutor_profile_id=int(favorite.tutor_profile_id),
            )

    def remove_favorite(
        self,
        student_id: UserId,
        tutor_profile_id: TutorProfileId,
    ) -> bool:
        """Remove a favorite by student and tutor profile.

        Uses hard delete (no soft delete).

        Args:
            student_id: Student's user ID
            tutor_profile_id: Tutor's profile ID

        Returns:
            True if removed, False if not found
        """
        result = (
            self.db.query(FavoriteTutor)
            .filter(
                FavoriteTutor.student_id == student_id,
                FavoriteTutor.tutor_profile_id == tutor_profile_id,
            )
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(
                f"Removed favorite: student {student_id} "
                f"unfavorited tutor profile {tutor_profile_id}"
            )
        return result > 0

    def remove_by_id(self, favorite_id: FavoriteId) -> bool:
        """Remove a favorite by its ID.

        Uses hard delete (no soft delete).

        Args:
            favorite_id: Favorite's unique identifier

        Returns:
            True if removed, False if not found
        """
        result = (
            self.db.query(FavoriteTutor)
            .filter(FavoriteTutor.id == favorite_id)
            .delete()
        )
        self.db.flush()

        if result > 0:
            logger.info(f"Removed favorite by ID: {favorite_id}")
        return result > 0

    def count_by_student(self, student_id: UserId) -> int:
        """Count favorites for a student.

        Args:
            student_id: Student's user ID

        Returns:
            Total count of favorites for the student
        """
        count = (
            self.db.query(func.count(FavoriteTutor.id))
            .filter(FavoriteTutor.student_id == student_id)
            .scalar()
        )
        return count or 0

    def count_by_tutor(self, tutor_profile_id: TutorProfileId) -> int:
        """Count how many students have favorited a tutor.

        This can be useful for analytics or showing popularity.

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            Total count of students who favorited this tutor
        """
        count = (
            self.db.query(func.count(FavoriteTutor.id))
            .filter(FavoriteTutor.tutor_profile_id == tutor_profile_id)
            .scalar()
        )
        return count or 0

    def get_tutor_profile_ids_for_student(
        self,
        student_id: UserId,
    ) -> list[TutorProfileId]:
        """Get all favorited tutor profile IDs for a student.

        This is a convenience method for checking multiple tutors
        against a student's favorites list efficiently.

        Args:
            student_id: Student's user ID

        Returns:
            List of tutor profile IDs the student has favorited
        """
        rows = (
            self.db.query(FavoriteTutor.tutor_profile_id)
            .filter(FavoriteTutor.student_id == student_id)
            .all()
        )
        return [TutorProfileId(row[0]) for row in rows]

    def _to_entity(self, model: FavoriteTutor) -> FavoriteEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: FavoriteTutor SQLAlchemy model

        Returns:
            FavoriteEntity domain entity
        """
        return FavoriteEntity(
            id=FavoriteId(model.id) if model.id else None,
            student_id=UserId(model.student_id),
            tutor_profile_id=TutorProfileId(model.tutor_profile_id),
            created_at=model.created_at,
        )

    def _to_model(self, entity: FavoriteEntity) -> FavoriteTutor:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: FavoriteEntity domain entity

        Returns:
            FavoriteTutor SQLAlchemy model
        """
        return FavoriteTutor(
            id=entity.id,
            student_id=entity.student_id,
            tutor_profile_id=entity.tutor_profile_id,
        )
