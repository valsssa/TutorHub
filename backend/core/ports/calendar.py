"""
Calendar Port - Interface for calendar operations.

This port defines the contract for calendar operations,
abstracting away the specific calendar provider (Google Calendar, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class CalendarEvent:
    """Represents a calendar event."""

    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    location: str | None = None
    attendees: list[str] = field(default_factory=list)
    html_link: str | None = None
    ical_uid: str | None = None
    meeting_url: str | None = None
    timezone: str = "UTC"


@dataclass(frozen=True)
class CalendarResult:
    """Result of a calendar operation."""

    success: bool
    event_id: str | None = None
    html_link: str | None = None
    ical_uid: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class FreeBusySlot:
    """A busy time slot."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class FreeBusyResult:
    """Result of a freebusy query."""

    success: bool
    busy_slots: list[FreeBusySlot] = field(default_factory=list)
    error_message: str | None = None


@dataclass(frozen=True)
class CalendarInfo:
    """Information about a calendar."""

    calendar_id: str
    summary: str
    description: str | None = None
    timezone: str | None = None
    is_primary: bool = False


class CalendarPort(Protocol):
    """
    Protocol for calendar operations.

    Implementations should handle:
    - OAuth credential management and refresh
    - Calendar event CRUD operations
    - FreeBusy queries for conflict checking
    - Proper error handling
    """

    async def create_event(
        self,
        *,
        user_id: int,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        attendees: list[tuple[str, str]] | None = None,
        meeting_url: str | None = None,
        timezone: str = "UTC",
        send_notifications: bool = True,
    ) -> CalendarResult:
        """
        Create a calendar event.

        Args:
            user_id: Internal user ID (for credential lookup)
            title: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            attendees: List of (email, name) tuples
            meeting_url: Video meeting URL to include
            timezone: Event timezone
            send_notifications: Whether to send email invites

        Returns:
            CalendarResult with event details
        """
        ...

    async def update_event(
        self,
        *,
        user_id: int,
        event_id: str,
        title: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        description: str | None = None,
        meeting_url: str | None = None,
        timezone: str = "UTC",
    ) -> CalendarResult:
        """
        Update an existing calendar event.

        Args:
            user_id: Internal user ID (for credential lookup)
            event_id: Calendar event ID
            title: New title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            meeting_url: New meeting URL (optional)
            timezone: Event timezone

        Returns:
            CalendarResult with update status
        """
        ...

    async def delete_event(
        self,
        *,
        user_id: int,
        event_id: str,
        send_notifications: bool = True,
    ) -> CalendarResult:
        """
        Delete a calendar event.

        Args:
            user_id: Internal user ID (for credential lookup)
            event_id: Calendar event ID to delete
            send_notifications: Whether to notify attendees

        Returns:
            CalendarResult with deletion status
        """
        ...

    async def get_freebusy(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
    ) -> FreeBusyResult:
        """
        Check for busy times in a calendar.

        Args:
            user_id: Internal user ID (for credential lookup)
            start_time: Start of time range to check
            end_time: End of time range to check
            calendar_id: Calendar ID to query

        Returns:
            FreeBusyResult with busy time slots
        """
        ...

    async def get_events_in_range(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """
        Get calendar events within a time range.

        Args:
            user_id: Internal user ID (for credential lookup)
            start_time: Start of time range
            end_time: End of time range
            calendar_id: Calendar ID to query
            max_results: Maximum events to return

        Returns:
            List of CalendarEvent objects
        """
        ...

    async def list_calendars(
        self,
        user_id: int,
    ) -> list[CalendarInfo]:
        """
        List user's available calendars.

        Args:
            user_id: Internal user ID (for credential lookup)

        Returns:
            List of CalendarInfo objects
        """
        ...

    async def sync_calendar(
        self,
        user_id: int,
        *,
        calendar_id: str = "primary",
    ) -> CalendarResult:
        """
        Trigger a calendar sync operation.

        Args:
            user_id: Internal user ID (for credential lookup)
            calendar_id: Calendar ID to sync

        Returns:
            CalendarResult with sync status
        """
        ...
