"""
Google Calendar Adapter - Implementation of CalendarPort for Google Calendar.

Wraps the google_calendar.py functionality with the CalendarPort interface.
Preserves OAuth credential management and API operations.
"""

import logging
from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings
from core.ports.calendar import (
    CalendarEvent,
    CalendarInfo,
    CalendarResult,
    FreeBusyResult,
    FreeBusySlot,
)

logger = logging.getLogger(__name__)

# Google API endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Calendar scopes
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleCalendarAdapter:
    """
    Google Calendar implementation of CalendarPort.

    Features:
    - OAuth credential management
    - Token refresh
    - Calendar event CRUD
    - FreeBusy queries
    """

    def __init__(self, credential_provider=None) -> None:
        """
        Initialize the adapter.

        Args:
            credential_provider: Optional callable that takes user_id and returns
                                 (access_token, refresh_token) tuple.
        """
        self._credential_provider = credential_provider

    def _get_credentials(
        self,
        access_token: str,
        refresh_token: str | None = None,
    ) -> Credentials:
        """Create Google credentials object."""
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URL,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=CALENDAR_SCOPES,
        )

    def _get_calendar_service(self, credentials: Credentials):
        """Build Google Calendar API service."""
        return build("calendar", "v3", credentials=credentials)

    async def _get_user_credentials(self, user_id: int) -> tuple[str, str | None]:
        """Get credentials for a user."""
        if self._credential_provider:
            return await self._credential_provider(user_id)
        raise ValueError("No credential provider configured")

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
        """Create a calendar event."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            event_body: dict[str, Any] = {
                "summary": title,
                "description": description or "",
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone,
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }

            if attendees:
                event_body["attendees"] = [
                    {"email": email, "displayName": name}
                    for email, name in attendees
                ]

            if meeting_url:
                event_body["location"] = meeting_url

            created_event = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    sendUpdates="all" if send_notifications else "none",
                )
                .execute()
            )

            logger.info("Created calendar event %s", created_event.get("id"))

            return CalendarResult(
                success=True,
                event_id=created_event.get("id"),
                html_link=created_event.get("htmlLink"),
                ical_uid=created_event.get("iCalUID"),
            )

        except HttpError as e:
            logger.error("Google Calendar API error: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error("Failed to create calendar event: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )

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
        """Update an existing calendar event."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            # Get existing event
            event = service.events().get(calendarId="primary", eventId=event_id).execute()

            # Update fields
            if title:
                event["summary"] = title
            if start_time:
                event["start"] = {"dateTime": start_time.isoformat(), "timeZone": timezone}
            if end_time:
                event["end"] = {"dateTime": end_time.isoformat(), "timeZone": timezone}
            if description:
                event["description"] = description
            if meeting_url:
                event["location"] = meeting_url

            service.events().update(
                calendarId="primary",
                eventId=event_id,
                body=event,
                sendUpdates="all",
            ).execute()

            logger.info("Updated calendar event %s", event_id)

            return CalendarResult(
                success=True,
                event_id=event_id,
            )

        except HttpError as e:
            logger.error("Failed to update calendar event: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error("Failed to update calendar event: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )

    async def delete_event(
        self,
        *,
        user_id: int,
        event_id: str,
        send_notifications: bool = True,
    ) -> CalendarResult:
        """Delete a calendar event."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            service.events().delete(
                calendarId="primary",
                eventId=event_id,
                sendUpdates="all" if send_notifications else "none",
            ).execute()

            logger.info("Deleted calendar event %s", event_id)

            return CalendarResult(
                success=True,
                event_id=event_id,
            )

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning("Calendar event %s not found", event_id)
                return CalendarResult(success=True, event_id=event_id)
            logger.error("Failed to delete calendar event: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error("Failed to delete calendar event: %s", e)
            return CalendarResult(
                success=False,
                error_message=str(e),
            )

    async def get_freebusy(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
    ) -> FreeBusyResult:
        """Check for busy times in a calendar."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": calendar_id}],
            }

            result = service.freebusy().query(body=body).execute()

            calendars = result.get("calendars", {})
            calendar_data = calendars.get(calendar_id, {})
            busy_times = calendar_data.get("busy", [])

            slots = []
            for slot in busy_times:
                slots.append(
                    FreeBusySlot(
                        start=datetime.fromisoformat(slot["start"].replace("Z", "+00:00")),
                        end=datetime.fromisoformat(slot["end"].replace("Z", "+00:00")),
                    )
                )

            return FreeBusyResult(
                success=True,
                busy_slots=slots,
            )

        except Exception as e:
            logger.error("Failed to check calendar freebusy: %s", e)
            return FreeBusyResult(
                success=False,
                error_message=str(e),
            )

    async def get_events_in_range(
        self,
        *,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """Get calendar events within a time range."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=max_results,
                )
                .execute()
            )

            events = []
            for item in events_result.get("items", []):
                start = item.get("start", {})
                end = item.get("end", {})

                start_dt = start.get("dateTime") or start.get("date")
                end_dt = end.get("dateTime") or end.get("date")

                events.append(
                    CalendarEvent(
                        event_id=item.get("id", ""),
                        title=item.get("summary", ""),
                        start_time=datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
                        if start_dt
                        else start_time,
                        end_time=datetime.fromisoformat(end_dt.replace("Z", "+00:00"))
                        if end_dt
                        else end_time,
                        description=item.get("description"),
                        location=item.get("location"),
                        html_link=item.get("htmlLink"),
                        attendees=[a.get("email", "") for a in item.get("attendees", [])],
                    )
                )

            return events

        except Exception as e:
            logger.error("Failed to get calendar events: %s", e)
            return []

    async def list_calendars(
        self,
        user_id: int,
    ) -> list[CalendarInfo]:
        """List user's available calendars."""
        try:
            access_token, refresh_token = await self._get_user_credentials(user_id)
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            calendar_list = service.calendarList().list().execute()

            calendars = []
            for item in calendar_list.get("items", []):
                calendars.append(
                    CalendarInfo(
                        calendar_id=item.get("id", ""),
                        summary=item.get("summary", ""),
                        description=item.get("description"),
                        timezone=item.get("timeZone"),
                        is_primary=item.get("primary", False),
                    )
                )

            return calendars

        except Exception as e:
            logger.error("Failed to list calendars: %s", e)
            return []

    async def sync_calendar(
        self,
        user_id: int,
        *,
        calendar_id: str = "primary",
    ) -> CalendarResult:
        """Trigger a calendar sync operation."""
        # Google Calendar syncs automatically, so this is essentially a no-op
        # We could implement incremental sync using sync tokens here
        return CalendarResult(
            success=True,
        )


# Default instance (without credential provider - must be configured)
google_calendar_adapter = GoogleCalendarAdapter()
