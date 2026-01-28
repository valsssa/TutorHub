"""
Google Calendar Integration Service

Handles:
- OAuth2 flow for calendar access
- Creating calendar events for bookings
- Sending calendar invites to tutors and students
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings

logger = logging.getLogger(__name__)

# Google Calendar API scopes
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]

# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


class GoogleCalendarService:
    """Google Calendar API client."""

    def __init__(self):
        self._credentials_cache: dict[int, Credentials] = {}

    def get_authorization_url(self, state: str, redirect_uri: str | None = None) -> str:
        """
        Generate Google OAuth authorization URL for calendar access.

        Args:
            state: CSRF protection state token
            redirect_uri: Custom redirect URI (optional)

        Returns:
            Authorization URL to redirect user to
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("Google OAuth not configured")

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri or settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(CALENDAR_SCOPES),
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",  # Force consent to get refresh token
            "state": state,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query}"

    async def exchange_code_for_tokens(
        self, code: str, redirect_uri: str | None = None
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in authorization

        Returns:
            Token response with access_token, refresh_token, etc.
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri or settings.GOOGLE_CALENDAR_REDIRECT_URI,
                },
            )

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise ValueError("Failed to exchange authorization code")

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an expired access token.

        Args:
            refresh_token: Google refresh token

        Returns:
            New token response with fresh access_token
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )

            if response.status_code != 200:
                logger.error(f"Google token refresh failed: {response.text}")
                raise ValueError("Failed to refresh token")

            return response.json()

    def _get_credentials(
        self, access_token: str, refresh_token: str | None = None
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

    async def create_booking_event(
        self,
        access_token: str,
        refresh_token: str | None,
        booking_id: int,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        tutor_email: str,
        student_email: str,
        tutor_name: str,
        student_name: str,
        meeting_url: str | None = None,
        timezone: str = "UTC",
    ) -> dict[str, Any] | None:
        """
        Create a calendar event for a booking.

        Args:
            access_token: Google access token
            refresh_token: Google refresh token for renewal
            booking_id: Booking ID for reference
            title: Event title
            description: Event description
            start_time: Session start time
            end_time: Session end time
            tutor_email: Tutor's email for invite
            student_email: Student's email for invite
            tutor_name: Tutor's display name
            student_name: Student's display name
            meeting_url: Video meeting URL (Zoom, etc.)
            timezone: Timezone for the event

        Returns:
            Created event data or None if failed
        """
        try:
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            # Build event description
            full_description = f"""
{description}

Booking ID: #{booking_id}
Tutor: {tutor_name}
Student: {student_name}

{"Meeting Link: " + meeting_url if meeting_url else ""}

Manage your booking: {settings.FRONTEND_URL}/bookings/{booking_id}

---
Created by EduStream
            """.strip()

            # Build event body
            event = {
                "summary": title,
                "description": full_description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone,
                },
                "attendees": [
                    {"email": tutor_email, "displayName": tutor_name},
                    {"email": student_email, "displayName": student_name},
                ],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},  # 24 hours before
                        {"method": "popup", "minutes": 30},  # 30 minutes before
                    ],
                },
                "guestsCanModify": False,
                "guestsCanInviteOthers": False,
            }

            # Add conference data if meeting URL provided
            if meeting_url:
                event["location"] = meeting_url
                # Add as a simple link in description since we're using external meeting
                event["conferenceData"] = None

            # Create the event
            created_event = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event,
                    sendUpdates="all",  # Send email invites to attendees
                )
                .execute()
            )

            logger.info(
                f"Created calendar event {created_event['id']} for booking {booking_id}"
            )

            return {
                "event_id": created_event["id"],
                "html_link": created_event.get("htmlLink"),
                "ical_uid": created_event.get("iCalUID"),
            }

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}", exc_info=True)
            return None

    async def update_booking_event(
        self,
        access_token: str,
        refresh_token: str | None,
        event_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        title: str | None = None,
        description: str | None = None,
        meeting_url: str | None = None,
        timezone: str = "UTC",
    ) -> bool:
        """Update an existing calendar event."""
        try:
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            # Get existing event
            event = service.events().get(calendarId="primary", eventId=event_id).execute()

            # Update fields
            if start_time:
                event["start"] = {"dateTime": start_time.isoformat(), "timeZone": timezone}
            if end_time:
                event["end"] = {"dateTime": end_time.isoformat(), "timeZone": timezone}
            if title:
                event["summary"] = title
            if description:
                event["description"] = description
            if meeting_url:
                event["location"] = meeting_url

            # Update the event
            service.events().update(
                calendarId="primary",
                eventId=event_id,
                body=event,
                sendUpdates="all",
            ).execute()

            logger.info(f"Updated calendar event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}", exc_info=True)
            return False

    async def delete_booking_event(
        self,
        access_token: str,
        refresh_token: str | None,
        event_id: str,
        send_updates: bool = True,
    ) -> bool:
        """Delete a calendar event (e.g., when booking is cancelled)."""
        try:
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            service.events().delete(
                calendarId="primary",
                eventId=event_id,
                sendUpdates="all" if send_updates else "none",
            ).execute()

            logger.info(f"Deleted calendar event {event_id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Calendar event {event_id} not found (already deleted?)")
                return True
            logger.error(f"Failed to delete calendar event: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}", exc_info=True)
            return False

    async def get_user_calendars(
        self, access_token: str, refresh_token: str | None = None
    ) -> list[dict[str, Any]]:
        """Get list of user's calendars."""
        try:
            credentials = self._get_credentials(access_token, refresh_token)
            service = self._get_calendar_service(credentials)

            calendar_list = service.calendarList().list().execute()
            return calendar_list.get("items", [])

        except Exception as e:
            logger.error(f"Failed to get calendars: {e}", exc_info=True)
            return []


# Singleton instance
google_calendar = GoogleCalendarService()
