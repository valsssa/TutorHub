"""
Repository interfaces for utils module.

Defines the contracts for health check and system monitoring operations.
"""

from typing import Protocol

from modules.utils.domain.entities import HealthCheckEntity, SystemHealthEntity


class HealthCheckRepository(Protocol):
    """
    Protocol for health check repository operations.

    Implementations should handle:
    - Individual service health checks
    - Aggregate system health status
    - Service availability monitoring
    """

    def check_database(self) -> HealthCheckEntity:
        """
        Check database connectivity and health.

        Returns:
            HealthCheckEntity with database status and latency

        Raises:
            HealthCheckFailedError: If the check cannot be performed
        """
        ...

    def check_redis(self) -> HealthCheckEntity:
        """
        Check Redis connectivity and health.

        Returns:
            HealthCheckEntity with Redis status and latency

        Raises:
            HealthCheckFailedError: If the check cannot be performed
        """
        ...

    def check_storage(self) -> HealthCheckEntity:
        """
        Check object storage (MinIO) connectivity and health.

        Returns:
            HealthCheckEntity with storage status and latency

        Raises:
            HealthCheckFailedError: If the check cannot be performed
        """
        ...

    def get_system_health(self) -> SystemHealthEntity:
        """
        Get aggregate health status of all services.

        Performs health checks on all configured services and returns
        an aggregate system health status.

        Returns:
            SystemHealthEntity with overall status and individual service checks

        Raises:
            ServiceUnavailableError: If critical services cannot be reached
        """
        ...


class AsyncHealthCheckRepository(Protocol):
    """
    Async protocol for health check repository operations.

    For use with async database and service connections.
    """

    async def check_database(self) -> HealthCheckEntity:
        """
        Check database connectivity and health asynchronously.

        Returns:
            HealthCheckEntity with database status and latency
        """
        ...

    async def check_redis(self) -> HealthCheckEntity:
        """
        Check Redis connectivity and health asynchronously.

        Returns:
            HealthCheckEntity with Redis status and latency
        """
        ...

    async def check_storage(self) -> HealthCheckEntity:
        """
        Check object storage (MinIO) connectivity and health asynchronously.

        Returns:
            HealthCheckEntity with storage status and latency
        """
        ...

    async def get_system_health(self) -> SystemHealthEntity:
        """
        Get aggregate health status of all services asynchronously.

        Returns:
            SystemHealthEntity with overall status and individual service checks
        """
        ...
