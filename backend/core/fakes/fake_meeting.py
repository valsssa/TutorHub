"""
Fake Meeting - In-memory implementation of MeetingPort for testing.

Provides configurable success/failure and meeting tracking for assertions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.ports.meeting import (
    MeetingDetails,
    MeetingProvider,
    MeetingResult,
    MeetingStatus,
)


@dataclass
class FakeMeetingCall:
    """Record of a meeting method call."""

    method: str
    timestamp: datetime
    args: dict[str, Any]
    result: Any


@dataclass
class StoredMeeting:
    """A stored meeting."""

    meeting_id: str
    topic: str
    start_time: datetime
    duration_minutes: int
    join_url: str
    host_url: str
    status: MeetingStatus = MeetingStatus.SCHEDULED
    provider: MeetingProvider = MeetingProvider.ZOOM
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeMeeting:
    """
    In-memory fake implementation of MeetingPort for testing.

    Features:
    - Tracks all method calls for assertions
    - Stores meetings in memory
    - Configurable success/failure modes
    """

    calls: list[FakeMeetingCall] = field(default_factory=list)
    meetings: dict[str, StoredMeeting] = field(default_factory=dict)
    should_fail: bool = False
    failure_message: str = "Simulated meeting failure"
    provider: MeetingProvider = MeetingProvider.ZOOM
    meeting_url_base: str = "https://fake-meeting.test"

    def _record_call(self, method: str, args: dict, result: Any) -> None:
        """Record a method call for assertions."""
        self.calls.append(
            FakeMeetingCall(
                method=method,
                timestamp=datetime.now(UTC),
                args=args,
                result=result,
            )
        )

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
        """Create a fake meeting."""
        args = {
            "topic": topic,
            "start_time": start_time.isoformat(),
            "duration_minutes": duration_minutes,
            "booking_id": booking_id,
        }

        if self.should_fail:
            result = MeetingResult(
                success=False,
                provider=self.provider.value,
                error_message=self.failure_message,
                needs_retry=True,
            )
        else:
            meeting_id = f"fake_{uuid.uuid4().hex[:12]}"
            join_url = f"{self.meeting_url_base}/join/{meeting_id}"
            host_url = f"{self.meeting_url_base}/host/{meeting_id}"

            self.meetings[meeting_id] = StoredMeeting(
                meeting_id=meeting_id,
                topic=topic,
                start_time=start_time,
                duration_minutes=duration_minutes,
                join_url=join_url,
                host_url=host_url,
                provider=self.provider,
            )

            result = MeetingResult(
                success=True,
                join_url=join_url,
                host_url=host_url,
                meeting_id=meeting_id,
                provider=self.provider.value,
            )

        self._record_call("create_meeting", args, result)
        return result

    async def cancel_meeting(
        self,
        meeting_id: str,
        *,
        notify_attendees: bool = True,
    ) -> MeetingResult:
        """Cancel a fake meeting."""
        args = {"meeting_id": meeting_id, "notify_attendees": notify_attendees}

        if self.should_fail:
            result = MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=self.provider.value,
                error_message=self.failure_message,
            )
        elif meeting_id not in self.meetings:
            result = MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=self.provider.value,
                error_message="Meeting not found",
            )
        else:
            self.meetings[meeting_id].status = MeetingStatus.CANCELLED
            result = MeetingResult(
                success=True,
                meeting_id=meeting_id,
                provider=self.provider.value,
            )

        self._record_call("cancel_meeting", args, result)
        return result

    async def update_meeting(
        self,
        meeting_id: str,
        *,
        topic: str | None = None,
        start_time: datetime | None = None,
        duration_minutes: int | None = None,
    ) -> MeetingResult:
        """Update a fake meeting."""
        args = {
            "meeting_id": meeting_id,
            "topic": topic,
            "start_time": start_time.isoformat() if start_time else None,
            "duration_minutes": duration_minutes,
        }

        if self.should_fail:
            result = MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=self.provider.value,
                error_message=self.failure_message,
            )
        elif meeting_id not in self.meetings:
            result = MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=self.provider.value,
                error_message="Meeting not found",
            )
        else:
            meeting = self.meetings[meeting_id]
            if topic:
                meeting.topic = topic
            if start_time:
                meeting.start_time = start_time
            if duration_minutes:
                meeting.duration_minutes = duration_minutes

            result = MeetingResult(
                success=True,
                meeting_id=meeting_id,
                provider=self.provider.value,
            )

        self._record_call("update_meeting", args, result)
        return result

    async def get_meeting_status(
        self,
        meeting_id: str,
    ) -> MeetingDetails | None:
        """Get fake meeting status."""
        self._record_call("get_meeting_status", {"meeting_id": meeting_id}, None)

        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            return None

        return MeetingDetails(
            meeting_id=meeting.meeting_id,
            provider=meeting.provider,
            join_url=meeting.join_url,
            host_url=meeting.host_url,
            status=meeting.status,
            start_time=meeting.start_time,
            duration_minutes=meeting.duration_minutes,
            topic=meeting.topic,
        )

    def get_provider(self) -> MeetingProvider:
        """Get the provider type."""
        return self.provider

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def get_meeting(self, meeting_id: str) -> StoredMeeting | None:
        """Get a stored meeting directly (for testing)."""
        return self.meetings.get(meeting_id)

    def set_meeting_status(self, meeting_id: str, status: MeetingStatus) -> None:
        """Set meeting status (for testing)."""
        if meeting_id in self.meetings:
            self.meetings[meeting_id].status = status

    def get_calls(self, method: str) -> list[FakeMeetingCall]:
        """Get all calls to a specific method."""
        return [c for c in self.calls if c.method == method]

    def reset(self) -> None:
        """Reset all state."""
        self.calls.clear()
        self.meetings.clear()
        self.should_fail = False
