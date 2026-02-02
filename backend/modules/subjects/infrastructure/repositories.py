"""SQLAlchemy repository implementation for subjects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.subjects import Subject
from models.tutors import TutorSubject
from modules.subjects.domain.entities import SubjectEntity
from modules.subjects.domain.exceptions import (
    DuplicateSubjectError,
    SubjectInUseError,
    SubjectNotFoundError,
)
from modules.subjects.domain.repositories import SubjectRepository
from modules.subjects.domain.value_objects import SubjectCategory, SubjectId, SubjectLevel


@dataclass(slots=True)
class SubjectRepositoryImpl(SubjectRepository):
    """Repository backed by SQLAlchemy ORM."""

    db: Session

    def get_by_id(self, subject_id: int) -> SubjectEntity | None:
        """
        Get a subject by its ID.

        Args:
            subject_id: Subject's unique identifier

        Returns:
            SubjectEntity if found, None otherwise
        """
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return None
        return self._to_entity(subject)

    def get_by_name(self, name: str) -> SubjectEntity | None:
        """
        Get a subject by its name (case-insensitive).

        Args:
            name: Subject name to look up

        Returns:
            SubjectEntity if found, None otherwise
        """
        subject = (
            self.db.query(Subject)
            .filter(func.lower(Subject.name) == name.lower())
            .first()
        )
        if not subject:
            return None
        return self._to_entity(subject)

    def get_all(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> list[SubjectEntity]:
        """
        Get all subjects with optional filtering.

        Args:
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching subjects
        """
        query = self.db.query(Subject)

        if not include_inactive:
            query = query.filter(Subject.is_active.is_(True))

        if category is not None:
            query = query.filter(func.lower(Subject.category) == category.value.lower())

        # Note: level filtering is not directly supported by the Subject model
        # The level is a domain concept that may not have a direct DB column
        # If level column exists, add: if level is not None: query = query.filter(...)

        query = query.order_by(Subject.name.asc())

        offset = (page - 1) * page_size
        subjects = query.offset(offset).limit(page_size).all()

        return [self._to_entity(s) for s in subjects]

    def get_active(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
    ) -> list[SubjectEntity]:
        """
        Get all active subjects with optional filtering.

        Convenience method that calls get_all with include_inactive=False.

        Args:
            category: Filter by category
            level: Filter by education level

        Returns:
            List of active subjects
        """
        return self.get_all(
            category=category,
            level=level,
            include_inactive=False,
            page=1,
            page_size=10000,  # Return all active subjects
        )

    def get_by_category(
        self,
        category: SubjectCategory,
        *,
        include_inactive: bool = False,
    ) -> list[SubjectEntity]:
        """
        Get all subjects in a specific category.

        Args:
            category: Category to filter by
            include_inactive: Whether to include inactive subjects

        Returns:
            List of subjects in the category
        """
        query = self.db.query(Subject).filter(
            func.lower(Subject.category) == category.value.lower()
        )

        if not include_inactive:
            query = query.filter(Subject.is_active.is_(True))

        query = query.order_by(Subject.name.asc())
        subjects = query.all()

        return [self._to_entity(s) for s in subjects]

    def create(self, subject: SubjectEntity) -> SubjectEntity:
        """
        Create a new subject.

        Args:
            subject: Subject entity to create

        Returns:
            Created subject with populated ID and timestamps

        Raises:
            DuplicateSubjectError: If a subject with the same name exists
        """
        if self.exists_by_name(subject.name):
            raise DuplicateSubjectError(subject.name)

        now = datetime.now(UTC)
        model = self._to_model(subject)
        model.created_at = now

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def update(self, subject: SubjectEntity) -> SubjectEntity:
        """
        Update an existing subject.

        Args:
            subject: Subject entity with updated fields

        Returns:
            Updated subject entity

        Raises:
            SubjectNotFoundError: If subject doesn't exist
            DuplicateSubjectError: If new name conflicts with existing subject
        """
        if subject.id is None:
            raise ValueError("Cannot update subject without ID")

        model = self.db.query(Subject).filter(Subject.id == int(subject.id)).first()
        if not model:
            raise SubjectNotFoundError(int(subject.id))

        # Check for name conflict with other subjects
        if subject.name.lower() != model.name.lower():
            existing = (
                self.db.query(Subject)
                .filter(
                    func.lower(Subject.name) == subject.name.lower(),
                    Subject.id != int(subject.id),
                )
                .first()
            )
            if existing:
                raise DuplicateSubjectError(subject.name)

        model.name = subject.name
        model.description = subject.description
        model.category = subject.category.value if subject.category else None
        model.is_active = subject.is_active

        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def delete(self, subject_id: int) -> bool:
        """
        Delete a subject (soft delete by setting is_active to False).

        Args:
            subject_id: Subject ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            SubjectInUseError: If subject is still taught by tutors
        """
        model = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not model:
            return False

        # Check if subject is still in use
        tutor_count = self.get_tutor_count(subject_id)
        if tutor_count > 0:
            raise SubjectInUseError(subject_id, tutor_count)

        # Soft delete - set is_active to False
        model.is_active = False
        self.db.commit()

        return True

    def search(
        self,
        query: str,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
        limit: int = 20,
    ) -> list[SubjectEntity]:
        """
        Search subjects by name or description.

        Args:
            query: Search query string
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects
            limit: Maximum number of results

        Returns:
            List of matching subjects
        """
        search_pattern = f"%{query.lower()}%"
        db_query = self.db.query(Subject).filter(
            (func.lower(Subject.name).like(search_pattern))
            | (func.lower(Subject.description).like(search_pattern))
        )

        if not include_inactive:
            db_query = db_query.filter(Subject.is_active.is_(True))

        if category is not None:
            db_query = db_query.filter(
                func.lower(Subject.category) == category.value.lower()
            )

        # Order by name match relevance (exact matches first, then partial)
        db_query = db_query.order_by(
            # Exact name matches come first
            func.lower(Subject.name) != query.lower(),
            # Then by name alphabetically
            Subject.name.asc(),
        )

        subjects = db_query.limit(limit).all()

        return [self._to_entity(s) for s in subjects]

    def count(
        self,
        *,
        category: SubjectCategory | None = None,
        level: SubjectLevel | None = None,
        include_inactive: bool = False,
    ) -> int:
        """
        Count subjects with optional filtering.

        Args:
            category: Filter by category
            level: Filter by education level
            include_inactive: Whether to include inactive subjects

        Returns:
            Total count of matching subjects
        """
        query = self.db.query(func.count(Subject.id))

        if not include_inactive:
            query = query.filter(Subject.is_active.is_(True))

        if category is not None:
            query = query.filter(func.lower(Subject.category) == category.value.lower())

        return query.scalar() or 0

    def exists_by_name(self, name: str) -> bool:
        """
        Check if a subject exists with the given name.

        Args:
            name: Subject name to check (case-insensitive)

        Returns:
            True if subject exists, False otherwise
        """
        return (
            self.db.query(func.count(Subject.id))
            .filter(func.lower(Subject.name) == name.lower())
            .scalar()
            or 0
        ) > 0

    def get_tutor_count(self, subject_id: int) -> int:
        """
        Get the number of tutors teaching this subject.

        Args:
            subject_id: Subject ID

        Returns:
            Number of tutors teaching this subject
        """
        return (
            self.db.query(func.count(TutorSubject.id))
            .filter(TutorSubject.subject_id == subject_id)
            .scalar()
            or 0
        )

    def get_popular(
        self,
        *,
        limit: int = 10,
    ) -> list[SubjectEntity]:
        """
        Get the most popular subjects based on tutor count.

        Args:
            limit: Maximum number of subjects to return

        Returns:
            List of popular subjects sorted by tutor count
        """
        # Subquery to count tutors per subject
        tutor_counts = (
            self.db.query(
                TutorSubject.subject_id,
                func.count(TutorSubject.id).label("tutor_count"),
            )
            .group_by(TutorSubject.subject_id)
            .subquery()
        )

        # Join with subjects and order by tutor count
        subjects = (
            self.db.query(Subject)
            .outerjoin(tutor_counts, Subject.id == tutor_counts.c.subject_id)
            .filter(Subject.is_active.is_(True))
            .order_by(
                func.coalesce(tutor_counts.c.tutor_count, 0).desc(),
                Subject.name.asc(),
            )
            .limit(limit)
            .all()
        )

        return [self._to_entity(s) for s in subjects]

    def _to_entity(self, model: Subject) -> SubjectEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: Subject SQLAlchemy model

        Returns:
            SubjectEntity domain object
        """
        # Parse category if present
        category: SubjectCategory | None = None
        if model.category:
            try:
                category = SubjectCategory.from_string(model.category)
            except Exception:
                # If category doesn't match enum, leave as None
                pass

        return SubjectEntity(
            id=SubjectId(model.id) if model.id else None,
            name=model.name,
            description=model.description,
            category=category,
            level=None,  # Level not stored in DB model
            is_active=model.is_active if model.is_active is not None else True,
            created_at=model.created_at,
            updated_at=None,  # Not tracked in DB model
        )

    def _to_model(self, entity: SubjectEntity) -> Subject:
        """
        Convert domain entity to SQLAlchemy model for creation.

        Args:
            entity: SubjectEntity domain object

        Returns:
            Subject SQLAlchemy model (for insertion)
        """
        model = Subject(
            name=entity.name,
            description=entity.description,
            category=entity.category.value if entity.category else None,
            is_active=entity.is_active,
        )

        if entity.id is not None:
            model.id = int(entity.id)

        return model
