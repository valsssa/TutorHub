"""
Value objects for the utils domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NewType


# Type-safe identifier for service names
ServiceName = NewType("ServiceName", str)


class ServiceStatus(str, Enum):
    """
    Service health status levels.

    Represents the current operational state of a service.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    @property
    def is_operational(self) -> bool:
        """Check if the service is operational (healthy or degraded)."""
        return self in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED)

    @property
    def display_name(self) -> str:
        """Get human-readable status name."""
        return self.value.capitalize()

    @classmethod
    def from_string(cls, value: str) -> "ServiceStatus":
        """
        Convert string to ServiceStatus.

        Args:
            value: String representation of service status

        Returns:
            ServiceStatus enum member

        Raises:
            ValueError: If value is not a valid service status
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = [s.value for s in cls]
            raise ValueError(
                f"Invalid service status: {value}. Valid statuses: {valid}"
            )


@dataclass(frozen=True)
class VersionInfo:
    """
    Application version information.

    Immutable value object containing version, build, and deployment details.
    """

    version: str
    git_commit: str | None = None
    build_date: str | None = None

    def __post_init__(self) -> None:
        """Validate version format."""
        if not self.version:
            raise ValueError("Version string cannot be empty")

    @property
    def short_commit(self) -> str | None:
        """Get short form of git commit hash (first 7 characters)."""
        if self.git_commit:
            return self.git_commit[:7]
        return None

    @property
    def full_version(self) -> str:
        """Get full version string including git commit if available."""
        if self.git_commit:
            return f"{self.version}+{self.short_commit}"
        return self.version

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "git_commit": self.git_commit,
            "build_date": self.build_date,
        }
