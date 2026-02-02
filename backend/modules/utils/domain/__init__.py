"""
Utils domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the utils module. This layer is independent of infrastructure concerns.
"""

from modules.utils.domain.entities import HealthCheckEntity, SystemHealthEntity
from modules.utils.domain.exceptions import (
    HealthCheckFailedError,
    ServiceUnavailableError,
    UtilsError,
)
from modules.utils.domain.repositories import (
    AsyncHealthCheckRepository,
    HealthCheckRepository,
)
from modules.utils.domain.value_objects import (
    ServiceName,
    ServiceStatus,
    VersionInfo,
)

__all__ = [
    # Entities
    "HealthCheckEntity",
    "SystemHealthEntity",
    # Value Objects
    "ServiceName",
    "ServiceStatus",
    "VersionInfo",
    # Exceptions
    "UtilsError",
    "HealthCheckFailedError",
    "ServiceUnavailableError",
    # Repository Protocols
    "HealthCheckRepository",
    "AsyncHealthCheckRepository",
]
