"""SQLAlchemy repository implementations for packages module.

Provides concrete implementations of the PricingOptionRepository and
StudentPackageRepository protocols defined in the domain layer.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, update
from sqlalchemy.orm import Session, joinedload

from models import Booking, StudentPackage, TutorPricingOption
from modules.packages.domain.entities import PricingOptionEntity, StudentPackageEntity
from modules.packages.domain.value_objects import (
    PackageId,
    PackageStatus,
    PricingOptionId,
    StudentId,
    TutorProfileId,
)

logger = logging.getLogger(__name__)


class PricingOptionRepositoryImpl:
    """SQLAlchemy implementation of PricingOptionRepository."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, pricing_option_id: PricingOptionId) -> PricingOptionEntity | None:
        """Get a pricing option by its ID.

        Args:
            pricing_option_id: Pricing option's unique identifier

        Returns:
            PricingOptionEntity if found, None otherwise
        """
        model = (
            self.db.query(TutorPricingOption)
            .filter(TutorPricingOption.id == pricing_option_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        include_inactive: bool = False,
    ) -> list[PricingOptionEntity]:
        """Get all pricing options for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            include_inactive: Whether to include inactive options

        Returns:
            List of pricing option entities
        """
        query = self.db.query(TutorPricingOption).filter(
            TutorPricingOption.tutor_profile_id == tutor_profile_id
        )

        # Note: TutorPricingOption doesn't have is_active column in the model,
        # so include_inactive is currently a no-op. This is kept for future use.
        # If filtering by active status is needed, add an is_active column to the model.

        query = query.order_by(TutorPricingOption.created_at.desc())
        models = query.all()
        return [self._to_entity(m) for m in models]

    def get_active_for_tutor(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> list[PricingOptionEntity]:
        """Get active pricing options for a tutor.

        Convenience method equivalent to get_by_tutor(tutor_profile_id, include_inactive=False).

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            List of active pricing option entities
        """
        return self.get_by_tutor(tutor_profile_id, include_inactive=False)

    def create(self, pricing_option: PricingOptionEntity) -> PricingOptionEntity:
        """Create a new pricing option.

        Args:
            pricing_option: Pricing option entity to create

        Returns:
            Created pricing option with populated ID
        """
        model = self._to_model(pricing_option)
        self.db.add(model)
        self.db.flush()
        return self._to_entity(model)

    def update(self, pricing_option: PricingOptionEntity) -> PricingOptionEntity:
        """Update an existing pricing option.

        Args:
            pricing_option: Pricing option entity with updated fields

        Returns:
            Updated pricing option entity

        Raises:
            ValueError: If pricing option ID is None or not found
        """
        if pricing_option.id is None:
            raise ValueError("Cannot update pricing option without ID")

        model = (
            self.db.query(TutorPricingOption)
            .filter(TutorPricingOption.id == pricing_option.id)
            .first()
        )
        if not model:
            raise ValueError(f"Pricing option {pricing_option.id} not found")

        # Update fields
        model.title = pricing_option.title
        model.description = pricing_option.description
        model.duration_minutes = pricing_option.duration_minutes
        model.price = Decimal(pricing_option.price_cents) / 100
        model.validity_days = pricing_option.validity_days
        model.extend_on_use = pricing_option.extend_on_use
        model.updated_at = utc_now()

        self.db.flush()
        return self._to_entity(model)

    def delete(self, pricing_option_id: PricingOptionId) -> bool:
        """Delete a pricing option.

        Note: This is a hard delete. Pricing options with associated packages
        should not be deleted - use has_packages() to check first.

        Args:
            pricing_option_id: ID of the pricing option to delete

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.db.query(TutorPricingOption)
            .filter(TutorPricingOption.id == pricing_option_id)
            .delete()
        )
        self.db.flush()
        return result > 0

    def has_packages(self, pricing_option_id: PricingOptionId) -> bool:
        """Check if a pricing option has associated packages.

        Used to prevent deletion of pricing options that are in use.

        Args:
            pricing_option_id: ID of the pricing option

        Returns:
            True if packages exist, False otherwise
        """
        count = (
            self.db.query(func.count(StudentPackage.id))
            .filter(StudentPackage.pricing_option_id == pricing_option_id)
            .scalar()
        )
        return count > 0

    def _to_entity(self, model: TutorPricingOption) -> PricingOptionEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: TutorPricingOption SQLAlchemy model

        Returns:
            PricingOptionEntity domain entity
        """
        # Get currency from tutor profile
        currency = "USD"
        if model.tutor_profile:
            currency = model.tutor_profile.currency or "USD"

        # Convert price from Decimal to cents
        price_cents = int(model.price * 100) if model.price else 0

        return PricingOptionEntity(
            id=PricingOptionId(model.id) if model.id else None,
            tutor_profile_id=TutorProfileId(model.tutor_profile_id),
            title=model.title,
            description=model.description,
            duration_minutes=model.duration_minutes,
            price_cents=price_cents,
            currency=currency,
            validity_days=model.validity_days,
            extend_on_use=model.extend_on_use or False,
            is_active=True,  # TutorPricingOption doesn't have is_active column
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: PricingOptionEntity) -> TutorPricingOption:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: PricingOptionEntity domain entity

        Returns:
            TutorPricingOption SQLAlchemy model
        """
        now = utc_now()
        return TutorPricingOption(
            id=entity.id,
            tutor_profile_id=entity.tutor_profile_id,
            title=entity.title,
            description=entity.description,
            duration_minutes=entity.duration_minutes,
            price=Decimal(entity.price_cents) / 100,
            validity_days=entity.validity_days,
            extend_on_use=entity.extend_on_use,
            created_at=entity.created_at or now,
            updated_at=entity.updated_at or now,
        )


class StudentPackageRepositoryImpl:
    """SQLAlchemy implementation of StudentPackageRepository."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(
        self,
        package_id: PackageId,
        *,
        with_pricing_option: bool = False,
    ) -> StudentPackageEntity | None:
        """Get a package by its ID.

        Args:
            package_id: Package's unique identifier
            with_pricing_option: Whether to load related pricing option

        Returns:
            StudentPackageEntity if found, None otherwise
        """
        query = self.db.query(StudentPackage).filter(StudentPackage.id == package_id)

        if with_pricing_option:
            query = query.options(joinedload(StudentPackage.pricing_option))

        model = query.first()
        if not model:
            return None
        return self._to_entity(model, include_pricing_option=with_pricing_option)

    def get_by_student(
        self,
        student_id: StudentId,
        *,
        status: PackageStatus | None = None,
        tutor_profile_id: TutorProfileId | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentPackageEntity]:
        """Get packages for a student with optional filtering.

        Args:
            student_id: Student's user ID
            status: Filter by package status
            tutor_profile_id: Filter by tutor
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching packages
        """
        query = self.db.query(StudentPackage).filter(
            StudentPackage.student_id == student_id
        )

        if status is not None:
            query = query.filter(StudentPackage.status == status.value)

        if tutor_profile_id is not None:
            query = query.filter(StudentPackage.tutor_profile_id == tutor_profile_id)

        # Order by most recent first
        query = query.order_by(StudentPackage.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        status: PackageStatus | None = None,
        student_id: StudentId | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentPackageEntity]:
        """Get packages for a tutor with optional filtering.

        Args:
            tutor_profile_id: Tutor's profile ID
            status: Filter by package status
            student_id: Filter by student
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching packages
        """
        query = self.db.query(StudentPackage).filter(
            StudentPackage.tutor_profile_id == tutor_profile_id
        )

        if status is not None:
            query = query.filter(StudentPackage.status == status.value)

        if student_id is not None:
            query = query.filter(StudentPackage.student_id == student_id)

        # Order by most recent first
        query = query.order_by(StudentPackage.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def get_active_for_student(
        self,
        student_id: StudentId,
        *,
        tutor_profile_id: TutorProfileId | None = None,
    ) -> list[StudentPackageEntity]:
        """Get active, non-expired packages for a student.

        Only returns packages that:
        - Have status = ACTIVE
        - Have sessions_remaining > 0
        - Are not expired (expires_at is NULL or > now)

        Args:
            student_id: Student's user ID
            tutor_profile_id: Optional filter by tutor

        Returns:
            List of usable packages, ordered by expiration (soonest first)
        """
        now = utc_now()

        query = self.db.query(StudentPackage).filter(
            and_(
                StudentPackage.student_id == student_id,
                StudentPackage.status == PackageStatus.ACTIVE.value,
                StudentPackage.sessions_remaining > 0,
                # Not expired: expires_at is NULL or in the future
                (StudentPackage.expires_at.is_(None)) | (StudentPackage.expires_at > now),
            )
        )

        if tutor_profile_id is not None:
            query = query.filter(StudentPackage.tutor_profile_id == tutor_profile_id)

        # Order by expiration (soonest first), then by ID for consistency
        # NULL expires_at comes last (no expiration)
        query = query.order_by(
            StudentPackage.expires_at.asc().nullslast(),
            StudentPackage.id.asc(),
        )

        models = query.all()
        return [self._to_entity(m) for m in models]

    def create(self, package: StudentPackageEntity) -> StudentPackageEntity:
        """Create a new student package.

        Args:
            package: Package entity to create

        Returns:
            Created package with populated ID
        """
        model = self._to_model(package)
        self.db.add(model)
        self.db.flush()
        return self._to_entity(model)

    def update(self, package: StudentPackageEntity) -> StudentPackageEntity:
        """Update an existing package.

        Args:
            package: Package entity with updated fields

        Returns:
            Updated package entity

        Raises:
            ValueError: If package ID is None or not found
        """
        if package.id is None:
            raise ValueError("Cannot update package without ID")

        model = (
            self.db.query(StudentPackage)
            .filter(StudentPackage.id == package.id)
            .first()
        )
        if not model:
            raise ValueError(f"Package {package.id} not found")

        # Update mutable fields
        model.sessions_remaining = package.sessions_remaining
        model.sessions_used = package.sessions_used
        model.status = package.status.value
        model.expires_at = package.expires_at
        model.expiry_warning_sent = package.expiry_warning_sent
        model.updated_at = utc_now()

        self.db.flush()
        return self._to_entity(model)

    def use_session(
        self,
        package_id: PackageId,
        student_id: StudentId,
    ) -> StudentPackageEntity | None:
        """Atomically use a session from a package.

        This method:
        1. Locks the package row (SELECT FOR UPDATE)
        2. Verifies package is usable and belongs to student
        3. Decrements sessions_remaining
        4. Increments sessions_used
        5. Handles rolling expiry if applicable
        6. Updates status to EXHAUSTED if no sessions left

        Args:
            package_id: Package ID to use session from
            student_id: Student ID (for ownership verification)

        Returns:
            Updated package entity, or None if operation failed
        """
        # Lock the row for update to prevent race conditions
        model = (
            self.db.query(StudentPackage)
            .filter(
                and_(
                    StudentPackage.id == package_id,
                    StudentPackage.student_id == student_id,
                )
            )
            .with_for_update()
            .first()
        )

        if not model:
            logger.warning(
                f"Package {package_id} not found or doesn't belong to student {student_id}"
            )
            return None

        # Verify package is usable
        if model.status != PackageStatus.ACTIVE.value:
            logger.warning(f"Package {package_id} is not active (status: {model.status})")
            return None

        if model.sessions_remaining <= 0:
            logger.warning(f"Package {package_id} has no remaining sessions")
            return None

        now = utc_now()
        if model.expires_at and model.expires_at < now:
            logger.warning(f"Package {package_id} has expired")
            return None

        # Decrement sessions and increment used count
        model.sessions_remaining -= 1
        model.sessions_used += 1
        model.updated_at = now

        # Handle rolling expiry
        if model.pricing_option and model.pricing_option.extend_on_use:
            validity_days = model.pricing_option.validity_days
            if validity_days:
                model.expires_at = now + timedelta(days=validity_days)
                model.expiry_warning_sent = False  # Reset warning flag

        # Update status to EXHAUSTED if no sessions left
        if model.sessions_remaining == 0:
            model.status = PackageStatus.EXHAUSTED.value

        self.db.flush()
        return self._to_entity(model)

    def get_expiring_soon(
        self,
        days_until_expiry: int = 7,
        *,
        warning_sent: bool | None = False,
    ) -> list[StudentPackageEntity]:
        """Get packages that will expire within the specified number of days.

        Args:
            days_until_expiry: Number of days to look ahead
            warning_sent: Filter by expiry_warning_sent flag
                         (None = no filter, False = not sent, True = sent)

        Returns:
            List of packages expiring soon
        """
        now = utc_now()
        expiry_threshold = now + timedelta(days=days_until_expiry)

        query = self.db.query(StudentPackage).filter(
            and_(
                StudentPackage.status == PackageStatus.ACTIVE.value,
                StudentPackage.expires_at.isnot(None),
                StudentPackage.expires_at > now,
                StudentPackage.expires_at <= expiry_threshold,
                StudentPackage.sessions_remaining > 0,
            )
        )

        if warning_sent is not None:
            query = query.filter(StudentPackage.expiry_warning_sent == warning_sent)

        query = query.order_by(StudentPackage.expires_at.asc())
        models = query.all()
        return [self._to_entity(m) for m in models]

    def get_expired(self, *, only_active_status: bool = True) -> list[StudentPackageEntity]:
        """Get packages that have passed their expiration date.

        Args:
            only_active_status: Only return packages with status = ACTIVE
                               (to avoid re-processing already expired packages)

        Returns:
            List of expired packages
        """
        now = utc_now()

        query = self.db.query(StudentPackage).filter(
            and_(
                StudentPackage.expires_at.isnot(None),
                StudentPackage.expires_at < now,
            )
        )

        if only_active_status:
            query = query.filter(StudentPackage.status == PackageStatus.ACTIVE.value)

        query = query.order_by(StudentPackage.expires_at.asc())
        models = query.all()
        return [self._to_entity(m) for m in models]

    def mark_expired(self, package_ids: list[PackageId]) -> int:
        """Bulk mark packages as expired.

        Args:
            package_ids: List of package IDs to mark as expired

        Returns:
            Number of packages updated
        """
        if not package_ids:
            return 0

        now = utc_now()
        result = (
            self.db.execute(
                update(StudentPackage)
                .where(StudentPackage.id.in_(package_ids))
                .values(status=PackageStatus.EXPIRED.value, updated_at=now)
            )
        )
        self.db.flush()
        return result.rowcount

    def mark_warning_sent(self, package_ids: list[PackageId]) -> int:
        """Bulk mark packages as having had expiry warning sent.

        Args:
            package_ids: List of package IDs to update

        Returns:
            Number of packages updated
        """
        if not package_ids:
            return 0

        now = utc_now()
        result = (
            self.db.execute(
                update(StudentPackage)
                .where(StudentPackage.id.in_(package_ids))
                .values(expiry_warning_sent=True, updated_at=now)
            )
        )
        self.db.flush()
        return result.rowcount

    def count_by_student(
        self,
        student_id: StudentId,
        *,
        status: PackageStatus | None = None,
    ) -> int:
        """Count packages for a student.

        Args:
            student_id: Student's user ID
            status: Filter by package status

        Returns:
            Count of matching packages
        """
        query = self.db.query(func.count(StudentPackage.id)).filter(
            StudentPackage.student_id == student_id
        )

        if status is not None:
            query = query.filter(StudentPackage.status == status.value)

        return query.scalar() or 0

    def count_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        status: PackageStatus | None = None,
    ) -> int:
        """Count packages for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            status: Filter by package status

        Returns:
            Count of matching packages
        """
        query = self.db.query(func.count(StudentPackage.id)).filter(
            StudentPackage.tutor_profile_id == tutor_profile_id
        )

        if status is not None:
            query = query.filter(StudentPackage.status == status.value)

        return query.scalar() or 0

    def get_usage_history(
        self,
        package_id: PackageId,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get usage history for a package.

        Returns records of session usage from the package,
        linked to booking records.

        Args:
            package_id: Package ID
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of usage records with booking details
        """
        query = self.db.query(Booking).filter(
            Booking.package_id == package_id,
            Booking.deleted_at.is_(None),
        )

        if from_date:
            query = query.filter(Booking.created_at >= from_date)

        if to_date:
            query = query.filter(Booking.created_at <= to_date)

        query = query.order_by(Booking.created_at.desc())

        bookings = query.all()

        return [
            {
                "booking_id": b.id,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "session_state": b.session_state,
                "session_outcome": b.session_outcome,
                "subject_name": b.subject_name,
                "created_at": b.created_at,
            }
            for b in bookings
        ]

    def _to_entity(
        self,
        model: StudentPackage,
        *,
        include_pricing_option: bool = False,
    ) -> StudentPackageEntity:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: StudentPackage SQLAlchemy model
            include_pricing_option: Whether to include pricing option entity

        Returns:
            StudentPackageEntity domain entity
        """
        # Get currency from tutor profile
        currency = "USD"
        if model.tutor_profile:
            currency = model.tutor_profile.currency or "USD"

        # Convert price from Decimal to cents
        purchase_price_cents = int(model.purchase_price * 100) if model.purchase_price else 0

        # Parse status
        status = PackageStatus(model.status) if model.status else PackageStatus.ACTIVE

        # Build pricing option entity if requested and available
        pricing_option_entity = None
        if include_pricing_option and model.pricing_option:
            pricing_option_entity = PricingOptionEntity(
                id=PricingOptionId(model.pricing_option.id),
                tutor_profile_id=TutorProfileId(model.pricing_option.tutor_profile_id),
                title=model.pricing_option.title,
                description=model.pricing_option.description,
                duration_minutes=model.pricing_option.duration_minutes,
                price_cents=int(model.pricing_option.price * 100) if model.pricing_option.price else 0,
                currency=currency,
                validity_days=model.pricing_option.validity_days,
                extend_on_use=model.pricing_option.extend_on_use or False,
                is_active=True,
                created_at=model.pricing_option.created_at,
                updated_at=model.pricing_option.updated_at,
            )

        return StudentPackageEntity(
            id=PackageId(model.id) if model.id else None,
            student_id=StudentId(model.student_id),
            tutor_profile_id=TutorProfileId(model.tutor_profile_id),
            pricing_option_id=PricingOptionId(model.pricing_option_id),
            sessions_purchased=model.sessions_purchased,
            sessions_remaining=model.sessions_remaining,
            sessions_used=model.sessions_used,
            purchase_price_cents=purchase_price_cents,
            currency=currency,
            status=status,
            expires_at=model.expires_at,
            purchased_at=model.purchased_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            payment_intent_id=model.payment_intent_id,
            expiry_warning_sent=model.expiry_warning_sent or False,
            pricing_option=pricing_option_entity,
        )

    def _to_model(self, entity: StudentPackageEntity) -> StudentPackage:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: StudentPackageEntity domain entity

        Returns:
            StudentPackage SQLAlchemy model
        """
        now = utc_now()
        return StudentPackage(
            id=entity.id,
            student_id=entity.student_id,
            tutor_profile_id=entity.tutor_profile_id,
            pricing_option_id=entity.pricing_option_id,
            sessions_purchased=entity.sessions_purchased,
            sessions_remaining=entity.sessions_remaining,
            sessions_used=entity.sessions_used,
            purchase_price=Decimal(entity.purchase_price_cents) / 100,
            purchased_at=entity.purchased_at or now,
            expires_at=entity.expires_at,
            status=entity.status.value,
            payment_intent_id=entity.payment_intent_id,
            expiry_warning_sent=entity.expiry_warning_sent,
            created_at=entity.created_at or now,
            updated_at=entity.updated_at or now,
        )
