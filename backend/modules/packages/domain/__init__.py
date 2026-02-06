"""
Package domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the packages module. This layer is independent of infrastructure concerns.
"""

from modules.packages.domain.entities import (
    PackageUsageRecord,
    PricingOptionEntity,
    StudentPackageEntity,
)
from modules.packages.domain.exceptions import (
    InsufficientSessionsError,
    InvalidPackageConfigError,
    PackageAlreadyActiveError,
    PackageError,
    PackageExpiredError,
    PackageNotFoundError,
    PackageNotOwnedError,
    PricingOptionNotActiveError,
    PricingOptionNotFoundError,
)
from modules.packages.domain.repositories import (
    PricingOptionRepository,
    StudentPackageRepository,
)
from modules.packages.domain.value_objects import (
    TERMINAL_PACKAGE_STATUSES,
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

__all__ = [
    # Entities
    "PricingOptionEntity",
    "StudentPackageEntity",
    "PackageUsageRecord",
    # Value Objects
    "PackageId",
    "PricingOptionId",
    "TutorProfileId",
    "StudentId",
    "PackageStatus",
    "TERMINAL_PACKAGE_STATUSES",
    "SessionCount",
    "ValidityPeriod",
    "PackagePrice",
    "DurationMinutes",
    # Exceptions
    "PackageError",
    "PackageNotFoundError",
    "PackageExpiredError",
    "InsufficientSessionsError",
    "PackageAlreadyActiveError",
    "InvalidPackageConfigError",
    "PackageNotOwnedError",
    "PricingOptionNotFoundError",
    "PricingOptionNotActiveError",
    # Repository Protocols
    "PricingOptionRepository",
    "StudentPackageRepository",
]
