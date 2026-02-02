"""
Value objects for integrations module.

Immutable objects that represent concepts without identity.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType


# Type aliases for integration identifiers
IntegrationId = NewType("IntegrationId", int)
VideoMeetingId = NewType("VideoMeetingId", int)


class IntegrationType(str, Enum):
    """
    Supported third-party integration types.

    Each type represents a different category of integration.
    """

    GOOGLE_CALENDAR = "google_calendar"
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    CUSTOM_VIDEO = "custom_video"


class IntegrationStatus(str, Enum):
    """
    Integration connection status.

    Status lifecycle:
        PENDING -> CONNECTED (OAuth complete)
        CONNECTED -> ERROR (token expired/invalid)
        CONNECTED -> DISCONNECTED (user disconnected)
        ERROR -> CONNECTED (user reconnected)
        ERROR -> DISCONNECTED (user gave up)
    """

    PENDING = "pending"  # OAuth flow initiated
    CONNECTED = "connected"  # Active and working
    DISCONNECTED = "disconnected"  # User disconnected
    ERROR = "error"  # Authentication/connection error


class VideoProvider(str, Enum):
    """
    Supported video meeting providers.

    Used to specify which video conferencing platform to use.
    """

    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    CUSTOM = "custom"
    MANUAL = "manual"  # Tutor provides URL manually
    PLATFORM = "platform"  # Platform's built-in video


@dataclass(frozen=True)
class OAuthCredentials:
    """
    OAuth credentials value object.

    Immutable container for OAuth tokens and expiration.
    """

    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    token_type: str = "Bearer"
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at

    @property
    def needs_refresh(self) -> bool:
        """Check if the token should be refreshed (5 min buffer)."""
        if self.expires_at is None:
            return False
        from datetime import timedelta

        buffer = timedelta(minutes=5)
        return datetime.now(self.expires_at.tzinfo) >= (self.expires_at - buffer)

    @property
    def can_refresh(self) -> bool:
        """Check if the token can be refreshed."""
        return self.refresh_token is not None


@dataclass(frozen=True)
class MeetingLink:
    """
    Video meeting link value object.

    Contains all information needed to join a video meeting.
    """

    url: str
    provider: VideoProvider
    meeting_id: str | None = None
    password: str | None = None
    host_url: str | None = None

    @property
    def is_valid(self) -> bool:
        """Check if the meeting link is valid."""
        return bool(self.url and self.url.startswith(("http://", "https://")))

    def __str__(self) -> str:
        """Return the join URL."""
        return self.url


@dataclass(frozen=True)
class CalendarEventInfo:
    """
    Calendar event information value object.

    Contains identifiers for a calendar event.
    """

    event_id: str
    calendar_id: str = "primary"
    html_link: str | None = None
    provider: IntegrationType = IntegrationType.GOOGLE_CALENDAR

    def __str__(self) -> str:
        """Return the event ID."""
        return self.event_id


@dataclass(frozen=True)
class IntegrationConfig:
    """
    Integration configuration value object.

    Stores provider-specific configuration.
    """

    provider: IntegrationType
    client_id: str | None = None
    is_enabled: bool = True
    webhook_url: str | None = None
    custom_settings: dict | None = None


# Terminal statuses (no further transitions expected)
TERMINAL_INTEGRATION_STATUSES = {IntegrationStatus.DISCONNECTED}

# Statuses that indicate the integration is usable
ACTIVE_INTEGRATION_STATUSES = {IntegrationStatus.CONNECTED}

# Statuses that allow reconnection
RECONNECTABLE_STATUSES = {IntegrationStatus.DISCONNECTED, IntegrationStatus.ERROR}
