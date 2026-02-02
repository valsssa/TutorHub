"""
Infrastructure repository implementations for the utils module.

Contains concrete implementations of the health check repository protocols.
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.adapters.minio_adapter import MinIOAdapter
from core.adapters.redis_adapter import RedisAdapter
from core.config import settings
from modules.utils.domain.entities import HealthCheckEntity, SystemHealthEntity
from modules.utils.domain.value_objects import ServiceName, ServiceStatus

logger = logging.getLogger(__name__)

# Latency thresholds in milliseconds
LATENCY_THRESHOLD_DEGRADED = 500.0  # > 500ms = degraded
LATENCY_THRESHOLD_HIGH = 1000.0  # > 1000ms = concerning (logged)


def _determine_status_from_latency(latency_ms: float) -> ServiceStatus:
    """
    Determine service status based on latency.

    Args:
        latency_ms: Response latency in milliseconds

    Returns:
        ServiceStatus based on latency thresholds
    """
    if latency_ms > LATENCY_THRESHOLD_DEGRADED:
        return ServiceStatus.DEGRADED
    return ServiceStatus.HEALTHY


class HealthCheckRepositoryImpl:
    """
    Async implementation of health check repository operations.

    Performs health checks on database, Redis, and MinIO storage services.
    Uses try/except to catch connection errors and measures latency using
    time.perf_counter() for accurate timing.
    """

    def __init__(
        self,
        db: Session | None = None,
        redis_adapter: RedisAdapter | None = None,
        minio_adapter: MinIOAdapter | None = None,
    ) -> None:
        """
        Initialize the health check repository.

        Args:
            db: SQLAlchemy database session (optional, can be set later)
            redis_adapter: Redis adapter instance (optional, creates default)
            minio_adapter: MinIO adapter instance (optional, creates default)
        """
        self._db = db
        self._redis = redis_adapter or RedisAdapter()
        self._minio = minio_adapter or MinIOAdapter()

    def set_db_session(self, db: Session) -> None:
        """Set the database session for health checks."""
        self._db = db

    async def check_database(self) -> HealthCheckEntity:
        """
        Check database connectivity and health.

        Executes a simple SELECT 1 query and measures latency.

        Returns:
            HealthCheckEntity with database status and latency
        """
        service_name = ServiceName("database")
        start_time = time.perf_counter()

        try:
            if self._db is None:
                return HealthCheckEntity(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    message="Database session not configured",
                    checked_at=datetime.now(timezone.utc),
                )

            # Execute simple query to verify connectivity
            self._db.execute(text("SELECT 1"))

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            status = _determine_status_from_latency(elapsed_ms)

            if elapsed_ms > LATENCY_THRESHOLD_HIGH:
                logger.warning(
                    "Database health check latency is high: %.2fms", elapsed_ms
                )

            message = "Connected" if status == ServiceStatus.HEALTHY else "High latency"

            return HealthCheckEntity(
                service_name=service_name,
                status=status,
                latency_ms=round(elapsed_ms, 2),
                message=message,
                checked_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Database health check failed: %s", e)

            return HealthCheckEntity(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                latency_ms=round(elapsed_ms, 2),
                message=f"Connection failed: {type(e).__name__}",
                checked_at=datetime.now(timezone.utc),
            )

    async def check_redis(self) -> HealthCheckEntity:
        """
        Check Redis connectivity and health.

        Pings Redis and measures latency.

        Returns:
            HealthCheckEntity with Redis status and latency
        """
        service_name = ServiceName("redis")
        start_time = time.perf_counter()

        try:
            # Use the Redis adapter's ping method
            is_healthy = await self._redis.ping()

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if not is_healthy:
                return HealthCheckEntity(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    latency_ms=round(elapsed_ms, 2),
                    message="Ping returned false",
                    checked_at=datetime.now(timezone.utc),
                )

            status = _determine_status_from_latency(elapsed_ms)

            if elapsed_ms > LATENCY_THRESHOLD_HIGH:
                logger.warning(
                    "Redis health check latency is high: %.2fms", elapsed_ms
                )

            message = "Connected" if status == ServiceStatus.HEALTHY else "High latency"

            return HealthCheckEntity(
                service_name=service_name,
                status=status,
                latency_ms=round(elapsed_ms, 2),
                message=message,
                checked_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Redis health check failed: %s", e)

            return HealthCheckEntity(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                latency_ms=round(elapsed_ms, 2),
                message=f"Connection failed: {type(e).__name__}",
                checked_at=datetime.now(timezone.utc),
            )

    async def check_storage(self) -> HealthCheckEntity:
        """
        Check object storage (MinIO) connectivity and health.

        Verifies bucket accessibility by calling ensure_bucket_exists.

        Returns:
            HealthCheckEntity with storage status and latency
        """
        service_name = ServiceName("storage")
        start_time = time.perf_counter()

        try:
            # Check if we can access the default bucket
            bucket_name = settings.AVATAR_STORAGE_BUCKET
            result = await self._minio.ensure_bucket_exists(bucket_name)

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if not result.success:
                return HealthCheckEntity(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    latency_ms=round(elapsed_ms, 2),
                    message=result.error_message or "Bucket check failed",
                    checked_at=datetime.now(timezone.utc),
                )

            status = _determine_status_from_latency(elapsed_ms)

            if elapsed_ms > LATENCY_THRESHOLD_HIGH:
                logger.warning(
                    "Storage health check latency is high: %.2fms", elapsed_ms
                )

            message = "Connected" if status == ServiceStatus.HEALTHY else "High latency"

            return HealthCheckEntity(
                service_name=service_name,
                status=status,
                latency_ms=round(elapsed_ms, 2),
                message=message,
                checked_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Storage health check failed: %s", e)

            return HealthCheckEntity(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                latency_ms=round(elapsed_ms, 2),
                message=f"Connection failed: {type(e).__name__}",
                checked_at=datetime.now(timezone.utc),
            )

    async def get_system_health(self) -> SystemHealthEntity:
        """
        Get aggregate health status of all services.

        Performs health checks on database, Redis, and storage,
        then returns an aggregate system health status.

        Returns:
            SystemHealthEntity with overall status and individual service checks
        """
        # Perform all health checks
        db_health = await self.check_database()
        redis_health = await self.check_redis()
        storage_health = await self.check_storage()

        # Create system health entity from individual checks
        health_checks = [db_health, redis_health, storage_health]
        system_health = SystemHealthEntity.from_checks(
            health_checks=health_checks,
            timestamp=datetime.now(timezone.utc),
        )

        # Log overall health status
        if system_health.overall_status == ServiceStatus.UNHEALTHY:
            unhealthy_services = [
                s.service_name for s in system_health.unhealthy_services
            ]
            logger.error(
                "System health check: UNHEALTHY. Affected services: %s",
                unhealthy_services,
            )
        elif system_health.overall_status == ServiceStatus.DEGRADED:
            degraded_services = [
                s.service_name for s in system_health.degraded_services
            ]
            logger.warning(
                "System health check: DEGRADED. Affected services: %s",
                degraded_services,
            )
        else:
            logger.debug("System health check: HEALTHY")

        return system_health
