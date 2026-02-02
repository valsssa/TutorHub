"""
Domain entities for packages module.

These are pure data classes representing the core package domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from modules.packages.domain.value_objects import (
    DurationMinutes,
    PackageId,
    PackagePrice,
    PackageStatus,
    PricingOptionId,
    SessionCount,
    StudentId,
    TutorProfileId,
    ValidityPeriod,
)


@dataclass
class PricingOptionEntity:
    """
    Domain entity representing a tutor's pricing option.

    A pricing option defines how a tutor sells their sessions,
    including price, duration, and package validity settings.
    """

    id: PricingOptionId | None
    tutor_profile_id: TutorProfileId
    title: str
    description: str | None
    duration_minutes: int
    price_cents: int
    currency: str
    validity_days: int | None
    extend_on_use: bool
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def price(self) -> PackagePrice:
        """Get price as PackagePrice value object."""
        return PackagePrice(
            amount_cents=self.price_cents,
            currency=self.currency,
            sessions_included=1,  # Per-session pricing
        )

    @property
    def duration(self) -> DurationMinutes:
        """Get duration as DurationMinutes value object."""
        return DurationMinutes(self.duration_minutes)

    @property
    def validity(self) -> ValidityPeriod:
        """Get validity period as ValidityPeriod value object."""
        return ValidityPeriod(days=self.validity_days, extend_on_use=self.extend_on_use)

    @property
    def price_decimal(self) -> Decimal:
        """Get price as decimal."""
        return Decimal(self.price_cents) / 100

    @property
    def has_expiration(self) -> bool:
        """Check if packages using this option will expire."""
        return self.validity_days is not None

    @property
    def is_rolling_expiry(self) -> bool:
        """Check if packages using this option have rolling expiry."""
        return self.extend_on_use and self.validity_days is not None

    def calculate_expiration_date(self, from_date: datetime | None = None) -> datetime | None:
        """
        Calculate expiration date for a package using this pricing option.

        Args:
            from_date: Start date for calculation (defaults to now)

        Returns:
            Expiration datetime or None if no expiration
        """
        if self.validity_days is None:
            return None
        base_date = from_date or datetime.now(UTC)
        return base_date + timedelta(days=self.validity_days)


@dataclass
class StudentPackageEntity:
    """
    Domain entity representing a student's purchased package.

    A student package tracks session credits purchased from a tutor,
    including usage, expiration, and status.
    """

    id: PackageId | None
    student_id: StudentId
    tutor_profile_id: TutorProfileId
    pricing_option_id: PricingOptionId
    sessions_purchased: int
    sessions_remaining: int
    sessions_used: int
    purchase_price_cents: int
    currency: str
    status: PackageStatus
    expires_at: datetime | None = None
    purchased_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    payment_intent_id: str | None = None
    expiry_warning_sent: bool = False

    # Optional relationships (loaded when needed)
    pricing_option: PricingOptionEntity | None = field(default=None, repr=False)

    @property
    def sessions_purchased_vo(self) -> SessionCount:
        """Get sessions purchased as value object."""
        return SessionCount(self.sessions_purchased)

    @property
    def sessions_remaining_vo(self) -> SessionCount:
        """Get sessions remaining as value object."""
        return SessionCount(self.sessions_remaining)

    @property
    def sessions_used_vo(self) -> SessionCount:
        """Get sessions used as value object."""
        return SessionCount(self.sessions_used)

    @property
    def purchase_price_decimal(self) -> Decimal:
        """Get purchase price as decimal."""
        return Decimal(self.purchase_price_cents) / 100

    @property
    def is_active(self) -> bool:
        """Check if package is active."""
        return self.status == PackageStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Check if package has expired."""
        if self.status == PackageStatus.EXPIRED:
            return True
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_exhausted(self) -> bool:
        """Check if package has no remaining sessions."""
        return self.sessions_remaining <= 0 or self.status == PackageStatus.EXHAUSTED

    @property
    def is_usable(self) -> bool:
        """Check if package can be used for a session."""
        return self.is_active and not self.is_expired and self.sessions_remaining > 0

    @property
    def has_expiration(self) -> bool:
        """Check if package has an expiration date."""
        return self.expires_at is not None

    @property
    def days_until_expiry(self) -> int | None:
        """Calculate days until package expires."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now(UTC)
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        """Check if package is expiring within 7 days."""
        days = self.days_until_expiry
        return days is not None and 0 < days <= 7

    def can_use_session(self) -> tuple[bool, str | None]:
        """
        Check if a session can be used from this package.

        Returns:
            tuple: (can_use, error_message)
        """
        if not self.is_active:
            return False, f"Package is {self.status.value}, cannot use credits"

        if self.sessions_remaining <= 0:
            return False, "No credits remaining in package"

        if self.is_expired:
            return False, "Package has expired"

        return True, None

    def use_session(self) -> "StudentPackageEntity":
        """
        Create a new entity with one session used.

        Returns:
            New StudentPackageEntity with updated session counts

        Note:
            Does not modify the current instance (immutable operation pattern)
        """
        can_use, error = self.can_use_session()
        if not can_use:
            raise ValueError(error)

        new_remaining = self.sessions_remaining - 1
        new_used = self.sessions_used + 1
        new_status = PackageStatus.EXHAUSTED if new_remaining == 0 else self.status

        # Handle rolling expiry
        new_expires_at = self.expires_at
        new_expiry_warning_sent = self.expiry_warning_sent
        if self.pricing_option and self.pricing_option.is_rolling_expiry:
            new_expires_at = self.pricing_option.calculate_expiration_date()
            new_expiry_warning_sent = False  # Reset warning flag

        return StudentPackageEntity(
            id=self.id,
            student_id=self.student_id,
            tutor_profile_id=self.tutor_profile_id,
            pricing_option_id=self.pricing_option_id,
            sessions_purchased=self.sessions_purchased,
            sessions_remaining=new_remaining,
            sessions_used=new_used,
            purchase_price_cents=self.purchase_price_cents,
            currency=self.currency,
            status=new_status,
            expires_at=new_expires_at,
            purchased_at=self.purchased_at,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            payment_intent_id=self.payment_intent_id,
            expiry_warning_sent=new_expiry_warning_sent,
            pricing_option=self.pricing_option,
        )

    def mark_expired(self) -> "StudentPackageEntity":
        """
        Create a new entity marked as expired.

        Returns:
            New StudentPackageEntity with expired status
        """
        return StudentPackageEntity(
            id=self.id,
            student_id=self.student_id,
            tutor_profile_id=self.tutor_profile_id,
            pricing_option_id=self.pricing_option_id,
            sessions_purchased=self.sessions_purchased,
            sessions_remaining=self.sessions_remaining,
            sessions_used=self.sessions_used,
            purchase_price_cents=self.purchase_price_cents,
            currency=self.currency,
            status=PackageStatus.EXPIRED,
            expires_at=self.expires_at,
            purchased_at=self.purchased_at,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            payment_intent_id=self.payment_intent_id,
            expiry_warning_sent=self.expiry_warning_sent,
            pricing_option=self.pricing_option,
        )

    def mark_refunded(self) -> "StudentPackageEntity":
        """
        Create a new entity marked as refunded.

        Returns:
            New StudentPackageEntity with refunded status
        """
        return StudentPackageEntity(
            id=self.id,
            student_id=self.student_id,
            tutor_profile_id=self.tutor_profile_id,
            pricing_option_id=self.pricing_option_id,
            sessions_purchased=self.sessions_purchased,
            sessions_remaining=self.sessions_remaining,
            sessions_used=self.sessions_used,
            purchase_price_cents=self.purchase_price_cents,
            currency=self.currency,
            status=PackageStatus.REFUNDED,
            expires_at=self.expires_at,
            purchased_at=self.purchased_at,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            payment_intent_id=self.payment_intent_id,
            expiry_warning_sent=self.expiry_warning_sent,
            pricing_option=self.pricing_option,
        )

    def extend_validity(self, days: int) -> "StudentPackageEntity":
        """
        Create a new entity with extended validity.

        Args:
            days: Number of days to extend validity

        Returns:
            New StudentPackageEntity with updated expiration
        """
        if self.expires_at is None:
            return self

        new_expires_at = datetime.now(UTC) + timedelta(days=days)

        return StudentPackageEntity(
            id=self.id,
            student_id=self.student_id,
            tutor_profile_id=self.tutor_profile_id,
            pricing_option_id=self.pricing_option_id,
            sessions_purchased=self.sessions_purchased,
            sessions_remaining=self.sessions_remaining,
            sessions_used=self.sessions_used,
            purchase_price_cents=self.purchase_price_cents,
            currency=self.currency,
            status=self.status,
            expires_at=new_expires_at,
            purchased_at=self.purchased_at,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            payment_intent_id=self.payment_intent_id,
            expiry_warning_sent=False,  # Reset warning flag
            pricing_option=self.pricing_option,
        )


@dataclass
class PackageUsageRecord:
    """Record of a single package usage event."""

    package_id: PackageId
    booking_id: int | None
    used_at: datetime
    sessions_before: int
    sessions_after: int

    @property
    def sessions_used(self) -> int:
        """Calculate sessions used in this event."""
        return self.sessions_before - self.sessions_after
