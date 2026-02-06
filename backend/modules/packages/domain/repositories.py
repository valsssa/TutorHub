"""
Repository interfaces for packages module.

Defines the contracts for package and pricing option persistence operations.
"""

from datetime import datetime
from typing import Protocol

from modules.packages.domain.entities import PricingOptionEntity, StudentPackageEntity
from modules.packages.domain.value_objects import (
    PackageId,
    PackageStatus,
    PricingOptionId,
    StudentId,
    TutorProfileId,
)


class PricingOptionRepository(Protocol):
    """
    Protocol for pricing option repository operations.

    Implementations should handle:
    - Pricing option CRUD operations
    - Tutor-based queries
    - Active/inactive filtering
    """

    def get_by_id(self, pricing_option_id: PricingOptionId) -> PricingOptionEntity | None:
        """
        Get a pricing option by its ID.

        Args:
            pricing_option_id: Pricing option's unique identifier

        Returns:
            PricingOptionEntity if found, None otherwise
        """
        ...

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        include_inactive: bool = False,
    ) -> list[PricingOptionEntity]:
        """
        Get all pricing options for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            include_inactive: Whether to include inactive options

        Returns:
            List of pricing option entities
        """
        ...

    def get_active_for_tutor(
        self,
        tutor_profile_id: TutorProfileId,
    ) -> list[PricingOptionEntity]:
        """
        Get active pricing options for a tutor.

        This is a convenience method equivalent to
        get_by_tutor(tutor_profile_id, include_inactive=False).

        Args:
            tutor_profile_id: Tutor's profile ID

        Returns:
            List of active pricing option entities
        """
        ...

    def create(self, pricing_option: PricingOptionEntity) -> PricingOptionEntity:
        """
        Create a new pricing option.

        Args:
            pricing_option: Pricing option entity to create

        Returns:
            Created pricing option with populated ID
        """
        ...

    def update(self, pricing_option: PricingOptionEntity) -> PricingOptionEntity:
        """
        Update an existing pricing option.

        Args:
            pricing_option: Pricing option entity with updated fields

        Returns:
            Updated pricing option entity
        """
        ...

    def delete(self, pricing_option_id: PricingOptionId) -> bool:
        """
        Delete a pricing option.

        Note: This may be a soft delete depending on implementation.
        Pricing options with associated packages should not be deleted.

        Args:
            pricing_option_id: ID of the pricing option to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def has_packages(self, pricing_option_id: PricingOptionId) -> bool:
        """
        Check if a pricing option has associated packages.

        Used to prevent deletion of pricing options that are in use.

        Args:
            pricing_option_id: ID of the pricing option

        Returns:
            True if packages exist, False otherwise
        """
        ...


class StudentPackageRepository(Protocol):
    """
    Protocol for student package repository operations.

    Implementations should handle:
    - Package CRUD operations
    - Student and tutor-based queries
    - Expiration handling
    - Session usage tracking
    """

    def get_by_id(
        self,
        package_id: PackageId,
        *,
        with_pricing_option: bool = False,
    ) -> StudentPackageEntity | None:
        """
        Get a package by its ID.

        Args:
            package_id: Package's unique identifier
            with_pricing_option: Whether to load related pricing option

        Returns:
            StudentPackageEntity if found, None otherwise
        """
        ...

    def get_by_student(
        self,
        student_id: StudentId,
        *,
        status: PackageStatus | None = None,
        tutor_profile_id: TutorProfileId | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentPackageEntity]:
        """
        Get packages for a student with optional filtering.

        Args:
            student_id: Student's user ID
            status: Filter by package status
            tutor_profile_id: Filter by tutor
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching packages
        """
        ...

    def get_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        status: PackageStatus | None = None,
        student_id: StudentId | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[StudentPackageEntity]:
        """
        Get packages for a tutor with optional filtering.

        Args:
            tutor_profile_id: Tutor's profile ID
            status: Filter by package status
            student_id: Filter by student
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching packages
        """
        ...

    def get_active_for_student(
        self,
        student_id: StudentId,
        *,
        tutor_profile_id: TutorProfileId | None = None,
    ) -> list[StudentPackageEntity]:
        """
        Get active, non-expired packages for a student.

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
        ...

    def create(self, package: StudentPackageEntity) -> StudentPackageEntity:
        """
        Create a new student package.

        Args:
            package: Package entity to create

        Returns:
            Created package with populated ID
        """
        ...

    def update(self, package: StudentPackageEntity) -> StudentPackageEntity:
        """
        Update an existing package.

        Args:
            package: Package entity with updated fields

        Returns:
            Updated package entity
        """
        ...

    def use_session(
        self,
        package_id: PackageId,
        student_id: StudentId,
    ) -> StudentPackageEntity | None:
        """
        Atomically use a session from a package.

        This method should:
        1. Lock the package row
        2. Verify package is usable
        3. Decrement sessions_remaining
        4. Increment sessions_used
        5. Handle rolling expiry if applicable
        6. Update status to EXHAUSTED if no sessions left

        Args:
            package_id: Package ID to use session from
            student_id: Student ID (for ownership verification)

        Returns:
            Updated package entity, or None if operation failed
        """
        ...

    def get_expiring_soon(
        self,
        days_until_expiry: int = 7,
        *,
        warning_sent: bool | None = False,
    ) -> list[StudentPackageEntity]:
        """
        Get packages that will expire within the specified number of days.

        Args:
            days_until_expiry: Number of days to look ahead
            warning_sent: Filter by expiry_warning_sent flag
                         (None = no filter, False = not sent, True = sent)

        Returns:
            List of packages expiring soon
        """
        ...

    def get_expired(self, *, only_active_status: bool = True) -> list[StudentPackageEntity]:
        """
        Get packages that have passed their expiration date.

        Args:
            only_active_status: Only return packages with status = ACTIVE
                               (to avoid re-processing already expired packages)

        Returns:
            List of expired packages
        """
        ...

    def mark_expired(self, package_ids: list[PackageId]) -> int:
        """
        Bulk mark packages as expired.

        Args:
            package_ids: List of package IDs to mark as expired

        Returns:
            Number of packages updated
        """
        ...

    def mark_warning_sent(self, package_ids: list[PackageId]) -> int:
        """
        Bulk mark packages as having had expiry warning sent.

        Args:
            package_ids: List of package IDs to update

        Returns:
            Number of packages updated
        """
        ...

    def count_by_student(
        self,
        student_id: StudentId,
        *,
        status: PackageStatus | None = None,
    ) -> int:
        """
        Count packages for a student.

        Args:
            student_id: Student's user ID
            status: Filter by package status

        Returns:
            Count of matching packages
        """
        ...

    def count_by_tutor(
        self,
        tutor_profile_id: TutorProfileId,
        *,
        status: PackageStatus | None = None,
    ) -> int:
        """
        Count packages for a tutor.

        Args:
            tutor_profile_id: Tutor's profile ID
            status: Filter by package status

        Returns:
            Count of matching packages
        """
        ...

    def get_usage_history(
        self,
        package_id: PackageId,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict]:
        """
        Get usage history for a package.

        Returns records of session usage from the package,
        typically linked to booking records.

        Args:
            package_id: Package ID
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of usage records
        """
        ...
