"""
Admin domain layer.

Contains domain entities, value objects, exceptions, and repository protocols
for the admin module following Clean Architecture/DDD patterns.
"""

from modules.admin.domain.entities import (
    AdminActionLog,
    AdminUserSummary,
    FeatureFlagAuditEntry,
    FeatureFlagEntity,
)
from modules.admin.domain.exceptions import (
    AdminActionNotAllowedError,
    AdminError,
    AdminSelfModificationError,
    FeatureFlagAlreadyExistsError,
    FeatureFlagNotFoundError,
    InvalidFeatureFlagError,
    LastAdminRemovalError,
    UnauthorizedAdminAccessError,
)
from modules.admin.domain.repositories import (
    AdminActionLogRepository,
    FeatureFlagRepository,
)
from modules.admin.domain.value_objects import (
    AdminActionType,
    AdminUserId,
    FeatureFlagId,
    FeatureFlagName,
    FeatureFlagState,
    Percentage,
    PermissionLevel,
    TargetType,
)

__all__ = [
    # Entities
    "AdminActionLog",
    "AdminUserSummary",
    "FeatureFlagAuditEntry",
    "FeatureFlagEntity",
    # Exceptions
    "AdminActionNotAllowedError",
    "AdminError",
    "AdminSelfModificationError",
    "FeatureFlagAlreadyExistsError",
    "FeatureFlagNotFoundError",
    "InvalidFeatureFlagError",
    "LastAdminRemovalError",
    "UnauthorizedAdminAccessError",
    # Repositories
    "AdminActionLogRepository",
    "FeatureFlagRepository",
    # Value Objects
    "AdminActionType",
    "AdminUserId",
    "FeatureFlagId",
    "FeatureFlagName",
    "FeatureFlagState",
    "Percentage",
    "PermissionLevel",
    "TargetType",
]
