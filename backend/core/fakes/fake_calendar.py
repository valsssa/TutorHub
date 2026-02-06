"""
Fake Calendar - In-memory implementation of CalendarPort for testing.

Provides configurable freebusy responses and event tracking for assertions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.ports.calendar import (
    CalendarEvent,
    CalendarInfo,
    CalendarResult,
    FreeBusyResult,
    FreeBusySlot,
)


@dataclass
class CalendarOperation:
    """Record of a calendar operation."""

    operation: str
    timestamp: datetime
    args: dict[str, Any]
    result: Any


@dataclass
class StoredEvent:
    """A stored calendar event."""

    event_id: str
    user_id: int
    calendar_id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    location: str | None = None
    attendees: list[tuple[str, str]] = field(default_factory=list)
    meeting_url: str | None = None
    timezone: str = "UTC"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeCalendar:
    """
    In-memory fake implementation of CalendarPort for testing.

    Features:
    - Stores events in memory
    - Configurable busy slots for freebusy queries
    - Tracks all operations for assertions
    - Configurable success/failure modes
    """

    events: dict[str, StoredEvent] = field(default_factory=dict)
    operations: list[CalendarOperation] = field(default_factory=list)
    busy_slots: list[FreeBusySlot] = field(default_factory=list)
    calendars: list[CalendarInfo] = field(default_factory=list)
    should_fail: bool = False
    failure_message: str = "Simulated calendar failure"

    def __post_init__(self):
        # Add a default primary calendar
        if not self.calendars:
            self.calendars.append(
                CalendarInfo(
                    calendar_id="primary",
                    summary="Primary Calendar",
                    timezone="UTC",
                    is_primary=True,
                )
            )

    def _record_operation(self, operation: str, args: dict, result: Any) -> None:
        """Record a calendar operation."""
        self.operations.append(
            CalendarOperation(
                operation=operation,
                timestamp=datetime.now(UTC),
                args=args,
                result=result,
            )
        )

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
        """Create a fake calendar event."""
        args = {
            "user_id": user_id,
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

        if self.should_fail:
            result = CalendarResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            event_id = f"evt_{uuid.uuid4().hex[:16]}"
            ical_uid = f"{event_id}@fake-calendar.test"

            self.events[event_id] = StoredEvent(
                event_id=event_id,
                user_id=user_id,
                calendar_id="primary",
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                attendees=attendees or [],
                meeting_url=meeting_url,
                timezone=timezone,
            )

            result = CalendarResult(
                success=True,
                event_id=event_id,
                html_link=f"https://fake-calendar.test/event/{event_id}",
                ical_uid=ical_uid,
            )

        self._record_operation("create_event", args, result)
        return result

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
        """Update a fake calendar event."""
        args = {"user_id": user_id, "event_id": event_id}

        if self.should_fail:
            result = CalendarResult(
                success=False,
                error_message=self.failure_message,
            )
        elif event_id not in self.events:
            result = CalendarResult(
                success=False,
                error_message="Event not found",
            )
        else:
            event = self.events[event_id]
            if title:
                event.title = title
            if start_time:
                event.start_time = start_time
            if end_time:
                event.end_time = end_time
            if description:
                event.description = description
            if meeting_url:
                event.meeting_url = meeting_url
            event.timezone = timezone

            result = CalendarResult(
                success=True,
                event_id=event_id,
            )

        self._record_operation("update_event", args, result)
        return result

    async def delete_event(
        self,
        *,
        user_id: int,
        event_id: str,
        send_notifications: bool = True,
    ) -> CalendarResult:
        """Delete a fake calendar event."""
        args = {"user_id": user_id, "event_id": event_id}

        if self.should_fail:
            result = CalendarResult(
                success=False,
                error_message=self.failure_message,
            )
        elif event_id not in self.events:
            # Treat as success like real Google Calendar
            result = CalendarResult(
                success=True,
                event_id=event_id,
            )
        else:
            del self.events[event_id]
            result = CalendarResult(
                success=True,
                event_id=event_id,
            )

        self._record_operation("delete_event", args, result)
        return result

    async def get_freebusy(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
    ) -> FreeBusyResult:
        """Check for busy times - returns configured busy slots."""
        args = {
            "user_id": user_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

        if self.should_fail:
            result = FreeBusyResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            # Return configured busy slots that overlap with the query range
            overlapping = [
                slot
                for slot in self.busy_slots
                if not (slot.end <= start_time or slot.start >= end_time)
            ]

            # Also include events from storage
            for event in self.events.values():
                if (
                    event.user_id == user_id
                    and event.calendar_id == calendar_id
                    and not (event.end_time <= start_time or event.start_time >= end_time)
                ):
                    overlapping.append(
                        FreeBusySlot(start=event.start_time, end=event.end_time)
                    )

            result = FreeBusyResult(
                success=True,
                busy_slots=overlapping,
            )

        self._record_operation("get_freebusy", args, result)
        return result

    async def get_events_in_range(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """Get events within a time range."""
        args = {
            "user_id": user_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

        events = []
        for event in self.events.values():
            if (
                event.user_id == user_id
                and event.calendar_id == calendar_id
                and not (event.end_time <= start_time or event.start_time >= end_time)
            ):
                events.append(
                    CalendarEvent(
                        event_id=event.event_id,
                        title=event.title,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        description=event.description,
                        location=event.location,
                        attendees=[email for email, _ in event.attendees],
                        meeting_url=event.meeting_url,
                        timezone=event.timezone,
                    )
                )
                if len(events) >= max_results:
                    break

        self._record_operation("get_events_in_range", args, events)
        return events

    async def list_calendars(
        self,
        user_id: int,
    ) -> list[CalendarInfo]:
        """List user's available calendars."""
        self._record_operation("list_calendars", {"user_id": user_id}, self.calendars)
        return self.calendars

    async def sync_calendar(
        self,
        user_id: int,
        *,
        calendar_id: str = "primary",
    ) -> CalendarResult:
        """Trigger a calendar sync operation."""
        result = CalendarResult(success=True)
        self._record_operation("sync_calendar", {"user_id": user_id}, result)
        return result

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def add_busy_slot(self, start: datetime, end: datetime) -> None:
        """Add a busy time slot (for testing)."""
        self.busy_slots.append(FreeBusySlot(start=start, end=end))

    def clear_busy_slots(self) -> None:
        """Clear all busy slots."""
        self.busy_slots.clear()

    def get_event(self, event_id: str) -> StoredEvent | None:
        """Get a stored event directly (for testing)."""
        return self.events.get(event_id)

    def get_user_events(self, user_id: int) -> list[StoredEvent]:
        """Get all events for a user (for testing)."""
        return [e for e in self.events.values() if e.user_id == user_id]

    def get_operations(self, operation: str) -> list[CalendarOperation]:
        """Get all operations of a specific type."""
        return [o for o in self.operations if o.operation == operation]

    def reset(self) -> None:
        """Reset all state."""
        self.events.clear()
        self.operations.clear()
        self.busy_slots.clear()
        self.should_fail = False
