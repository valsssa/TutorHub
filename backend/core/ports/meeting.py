"""
Meeting Port - Interface for video meeting operations.

This port defines the contract for video meeting operations,
abstracting away the specific provider (Zoom, Google Meet, etc.).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


class MeetingProvider(str, Enum):
    """Supported video meeting providers."""

    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    CUSTOM = "custom"
    MANUAL = "manual"
    PLATFORM = "platform"


class MeetingStatus(str, Enum):
    """Status of a meeting."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class MeetingResult:
    """Result of a meeting operation."""

    success: bool
    join_url: str | None = None
    host_url: str | None = None
    meeting_id: str | None = None
    provider: str | None = None
    error_message: str | None = None
    needs_retry: bool = False


@dataclass(frozen=True)
class MeetingDetails:
    """Details of an existing meeting."""

    meeting_id: str
    provider: MeetingProvider
    join_url: str
    host_url: str | None = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    start_time: datetime | None = None
    duration_minutes: int | None = None
    topic: str | None = None
    attendees: list[str] | None = None


class MeetingPort(Protocol):
    """
    Protocol for video meeting operations.

    Implementations should handle:
    - Meeting creation with provider-specific authentication
    - Meeting cancellation and updates
    - Error handling with retry indicators
    - Provider-specific URL generation
    """

    async def create_meeting(
        self,
        *,
        topic: str,
        start_time: datetime,
        duration_minutes: int,
        host_email: str | None = None,
        attendee_emails: list[str] | None = None,
        booking_id: int | None = None,
    ) -> MeetingResult:
        """
        Create a video meeting.

        Args:
            topic: Meeting title/topic
            start_time: Scheduled start time
            duration_minutes: Expected duration
            host_email: Host's email address
            attendee_emails: List of attendee email addresses
            booking_id: Associated booking ID for tracking

        Returns:
            MeetingResult with meeting URLs and ID
        """
        ...

    async def cancel_meeting(
        self,
        meeting_id: str,
        *,
        notify_attendees: bool = True,
    ) -> MeetingResult:
        """
        Cancel an existing meeting.

        Args:
            meeting_id: ID of the meeting to cancel
            notify_attendees: Whether to notify attendees of cancellation

        Returns:
            MeetingResult with cancellation status
        """
        ...

    async def update_meeting(
        self,
        meeting_id: str,
        *,
        topic: str | None = None,
        start_time: datetime | None = None,
        duration_minutes: int | None = None,
    ) -> MeetingResult:
        """
        Update an existing meeting.

        Args:
            meeting_id: ID of the meeting to update
            topic: New topic (optional)
            start_time: New start time (optional)
            duration_minutes: New duration (optional)

        Returns:
            MeetingResult with updated meeting details
        """
        ...

    async def get_meeting_status(
        self,
        meeting_id: str,
    ) -> MeetingDetails | None:
        """
        Get the current status of a meeting.

        Args:
            meeting_id: ID of the meeting to check

        Returns:
            MeetingDetails if found, None otherwise
        """
        ...

    def get_provider(self) -> MeetingProvider:
        """
        Get the provider type for this implementation.

        Returns:
            MeetingProvider enum value
        """
        ...
