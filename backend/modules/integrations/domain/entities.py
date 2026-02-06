"""
Domain entities for integrations module.

These are pure data classes representing the core integration domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime

from modules.integrations.domain.value_objects import (
    IntegrationId,
    IntegrationStatus,
    IntegrationType,
    MeetingLink,
    OAuthCredentials,
    VideoMeetingId,
    VideoProvider,
)


@dataclass
class UserIntegrationEntity:
    """
    User's third-party integration connection.

    Represents a connection between a user and an external service
    (e.g., Google Calendar, Zoom).
    """

    id: IntegrationId | None
    user_id: int
    integration_type: IntegrationType
    status: IntegrationStatus = IntegrationStatus.PENDING

    # OAuth credentials
    credentials: OAuthCredentials | None = None

    # Provider-specific identifiers
    external_account_id: str | None = None
    external_email: str | None = None

    # Timestamps
    connected_at: datetime | None = None
    last_sync_at: datetime | None = None
    last_error_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Error tracking
    last_error_message: str | None = None
    error_count: int = 0

    @property
    def is_connected(self) -> bool:
        """Check if the integration is actively connected."""
        return self.status == IntegrationStatus.CONNECTED

    @property
    def is_usable(self) -> bool:
        """Check if the integration can be used for operations."""
        return (
            self.is_connected
            and self.credentials is not None
            and not self.credentials.is_expired
        )

    @property
    def needs_reconnection(self) -> bool:
        """Check if the integration needs user to reconnect."""
        return (
            self.status == IntegrationStatus.ERROR
            or (
                self.credentials is not None
                and self.credentials.is_expired
                and not self.credentials.can_refresh
            )
        )

    @property
    def can_sync(self) -> bool:
        """Check if calendar sync is available."""
        return (
            self.is_usable
            and self.integration_type == IntegrationType.GOOGLE_CALENDAR
        )

    def mark_error(self, error_message: str) -> None:
        """Mark the integration as having an error."""
        self.status = IntegrationStatus.ERROR
        self.last_error_at = datetime.utcnow()
        self.last_error_message = error_message
        self.error_count += 1
        self.updated_at = datetime.utcnow()

    def mark_connected(self) -> None:
        """Mark the integration as connected."""
        self.status = IntegrationStatus.CONNECTED
        self.connected_at = datetime.utcnow()
        self.error_count = 0
        self.last_error_message = None
        self.updated_at = datetime.utcnow()

    def mark_disconnected(self) -> None:
        """Mark the integration as disconnected."""
        self.status = IntegrationStatus.DISCONNECTED
        self.credentials = None
        self.updated_at = datetime.utcnow()

    def update_last_sync(self) -> None:
        """Update the last sync timestamp."""
        self.last_sync_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


@dataclass
class VideoMeetingEntity:
    """
    Video meeting for a booking.

    Represents a video meeting created for a tutoring session.
    """

    id: VideoMeetingId | None
    booking_id: int
    provider: VideoProvider

    # Meeting details
    meeting_url: str
    meeting_id: str | None = None
    host_url: str | None = None
    password: str | None = None

    # Provider-specific data
    provider_response: dict = field(default_factory=dict)

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None

    # Status tracking
    is_active: bool = True
    last_accessed_at: datetime | None = None

    @property
    def meeting_link(self) -> MeetingLink:
        """Get the meeting as a MeetingLink value object."""
        return MeetingLink(
            url=self.meeting_url,
            provider=self.provider,
            meeting_id=self.meeting_id,
            password=self.password,
            host_url=self.host_url,
        )

    @property
    def is_valid(self) -> bool:
        """Check if the meeting is still valid."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() >= self.expires_at:
            return False
        return bool(self.meeting_url)

    @property
    def join_url(self) -> str:
        """Get the participant join URL."""
        return self.meeting_url

    def mark_accessed(self) -> None:
        """Mark the meeting as accessed."""
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the meeting."""
        self.is_active = False
        self.updated_at = datetime.utcnow()


@dataclass
class CalendarEventEntity:
    """
    Calendar event for a booking.

    Represents a calendar event created in user's calendar.
    """

    id: int | None
    booking_id: int
    user_id: int
    integration_id: IntegrationId

    # Event identifiers
    external_event_id: str
    calendar_id: str = "primary"

    # Event details
    title: str | None = None
    html_link: str | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synced_at: datetime | None = None

    # Status
    is_synced: bool = True
    sync_error: str | None = None

    @property
    def needs_sync(self) -> bool:
        """Check if the event needs to be synced."""
        return not self.is_synced

    def mark_synced(self) -> None:
        """Mark the event as synced."""
        self.is_synced = True
        self.synced_at = datetime.utcnow()
        self.sync_error = None
        self.updated_at = datetime.utcnow()

    def mark_sync_error(self, error: str) -> None:
        """Mark the event as having a sync error."""
        self.is_synced = False
        self.sync_error = error
        self.updated_at = datetime.utcnow()


@dataclass
class IntegrationSyncResult:
    """Result of an integration sync operation."""

    success: bool
    integration_id: IntegrationId
    operation: str
    items_synced: int = 0
    items_failed: int = 0
    error_message: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return self.items_failed > 0 or self.error_message is not None


@dataclass
class MeetingCreationResult:
    """Result of a video meeting creation attempt."""

    success: bool
    provider: VideoProvider
    join_url: str | None = None
    host_url: str | None = None
    meeting_id: str | None = None
    password: str | None = None
    error_message: str | None = None
    needs_retry: bool = False

    @property
    def meeting_link(self) -> MeetingLink | None:
        """Get the meeting as a MeetingLink value object if successful."""
        if not self.success or not self.join_url:
            return None
        return MeetingLink(
            url=self.join_url,
            provider=self.provider,
            meeting_id=self.meeting_id,
            password=self.password,
            host_url=self.host_url,
        )
