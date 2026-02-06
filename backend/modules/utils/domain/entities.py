"""
Domain entities for utils module.

These are pure data classes representing the core utility domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime

from core.datetime_utils import utc_now
from modules.utils.domain.value_objects import (
    ServiceName,
    ServiceStatus,
)


@dataclass
class HealthCheckEntity:
    """
    Domain entity representing a health check result for a single service.

    A health check captures the current operational state of a service
    including its status, response time, and any diagnostic messages.
    """

    service_name: ServiceName
    status: ServiceStatus
    latency_ms: float | None = None
    message: str | None = None
    checked_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set checked_at if not provided."""
        if self.checked_at is None:
            self.checked_at = utc_now()

    @property
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self.status == ServiceStatus.HEALTHY

    @property
    def is_operational(self) -> bool:
        """Check if the service is operational (healthy or degraded)."""
        return self.status.is_operational

    @property
    def has_high_latency(self) -> bool:
        """
        Check if the service has high latency (> 1000ms).

        Returns False if latency is not measured.
        """
        if self.latency_ms is None:
            return False
        return self.latency_ms > 1000.0

    def to_dict(self) -> dict[str, str | float | None]:
        """Convert to dictionary representation."""
        return {
            "service_name": str(self.service_name),
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"HealthCheckEntity(service_name={self.service_name!r}, "
            f"status={self.status.value}, latency_ms={self.latency_ms})"
        )


@dataclass
class SystemHealthEntity:
    """
    Domain entity representing the overall system health status.

    Aggregates health check results from multiple services to provide
    an overall view of system health.
    """

    overall_status: ServiceStatus
    services: list[HealthCheckEntity] = field(default_factory=list)
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = utc_now()

    @property
    def is_healthy(self) -> bool:
        """Check if the overall system is healthy."""
        return self.overall_status == ServiceStatus.HEALTHY

    @property
    def is_operational(self) -> bool:
        """Check if the overall system is operational."""
        return self.overall_status.is_operational

    @property
    def unhealthy_services(self) -> list[HealthCheckEntity]:
        """Get list of unhealthy services."""
        return [s for s in self.services if s.status == ServiceStatus.UNHEALTHY]

    @property
    def degraded_services(self) -> list[HealthCheckEntity]:
        """Get list of degraded services."""
        return [s for s in self.services if s.status == ServiceStatus.DEGRADED]

    @property
    def healthy_services(self) -> list[HealthCheckEntity]:
        """Get list of healthy services."""
        return [s for s in self.services if s.status == ServiceStatus.HEALTHY]

    @property
    def service_count(self) -> int:
        """Get total number of services checked."""
        return len(self.services)

    @property
    def healthy_percentage(self) -> float:
        """Get percentage of healthy services."""
        if not self.services:
            return 0.0
        return len(self.healthy_services) / len(self.services) * 100

    def get_service(self, service_name: ServiceName) -> HealthCheckEntity | None:
        """
        Get health check result for a specific service.

        Args:
            service_name: Name of the service to find

        Returns:
            HealthCheckEntity if found, None otherwise
        """
        for service in self.services:
            if service.service_name == service_name:
                return service
        return None

    def add_service(self, health_check: HealthCheckEntity) -> None:
        """
        Add a service health check result.

        Updates overall status based on the new check.

        Args:
            health_check: Health check result to add
        """
        self.services.append(health_check)
        self._recalculate_overall_status()

    def _recalculate_overall_status(self) -> None:
        """Recalculate overall status based on individual service statuses."""
        if not self.services:
            self.overall_status = ServiceStatus.HEALTHY
            return

        # If any service is unhealthy, system is unhealthy
        if any(s.status == ServiceStatus.UNHEALTHY for s in self.services):
            self.overall_status = ServiceStatus.UNHEALTHY
        # If any service is degraded, system is degraded
        elif any(s.status == ServiceStatus.DEGRADED for s in self.services):
            self.overall_status = ServiceStatus.DEGRADED
        else:
            self.overall_status = ServiceStatus.HEALTHY

    @classmethod
    def from_checks(
        cls,
        health_checks: list[HealthCheckEntity],
        timestamp: datetime | None = None,
    ) -> "SystemHealthEntity":
        """
        Create SystemHealthEntity from a list of health checks.

        Automatically calculates overall status.

        Args:
            health_checks: List of individual service health checks
            timestamp: Optional timestamp for the system check

        Returns:
            SystemHealthEntity with calculated overall status
        """
        entity = cls(
            overall_status=ServiceStatus.HEALTHY,
            services=health_checks,
            timestamp=timestamp,
        )
        entity._recalculate_overall_status()
        return entity

    def to_dict(self) -> dict[str, str | list | float | None]:
        """Convert to dictionary representation."""
        return {
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
            "service_count": self.service_count,
            "healthy_percentage": self.healthy_percentage,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"SystemHealthEntity(overall_status={self.overall_status.value}, "
            f"service_count={self.service_count})"
        )
