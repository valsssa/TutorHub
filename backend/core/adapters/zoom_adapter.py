"""
Zoom Adapter - Implementation of MeetingPort for Zoom.

Wraps the ZoomClient from zoom_router.py with the MeetingPort interface.
Preserves Server-to-Server OAuth and retry logic.
"""

import asyncio
import base64
import logging
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from typing import Any

import httpx

from core.config import settings
from core.ports.meeting import (
    MeetingDetails,
    MeetingProvider,
    MeetingResult,
    MeetingStatus,
)

logger = logging.getLogger(__name__)

# Zoom API endpoints
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"

# Retry configuration
ZOOM_MAX_RETRIES = 3
ZOOM_RETRY_BASE_DELAY = 1.0
ZOOM_RETRY_MAX_DELAY = 10.0


class ZoomAdapter:
    """
    Zoom implementation of MeetingPort using Server-to-Server OAuth.

    Features:
    - Server-to-Server OAuth authentication
    - Automatic token refresh
    - Retry logic with exponential backoff
    - Meeting CRUD operations
    """

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expires: datetime | None = None

    async def _get_access_token(self) -> str:
        """Get or refresh Server-to-Server OAuth token."""
        if not settings.ZOOM_CLIENT_ID or not settings.ZOOM_CLIENT_SECRET:
            raise ValueError("Zoom integration not configured")

        # Check if token is still valid
        if (
            self._access_token
            and self._token_expires
            and utc_now() < self._token_expires - timedelta(minutes=5)
        ):
            return self._access_token

        # Get new token
        credentials = base64.b64encode(
            f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ZOOM_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "account_credentials",
                    "account_id": settings.ZOOM_ACCOUNT_ID,
                },
            )

            if response.status_code != 200:
                logger.error("Zoom token error: %s", response.text)
                raise ValueError("Failed to authenticate with Zoom")

            data = response.json()
            self._access_token = data["access_token"]
            self._token_expires = utc_now() + timedelta(seconds=data["expires_in"])

            return self._access_token

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Make an authenticated Zoom API request with retry logic."""
        last_error: Exception | None = None

        for attempt in range(ZOOM_MAX_RETRIES + 1):
            try:
                token = await self._get_access_token()

                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        f"{ZOOM_API_BASE}{endpoint}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        **kwargs,
                    )

                    if response.status_code == 429:
                        # Rate limited - retry with backoff
                        delay = min(ZOOM_RETRY_BASE_DELAY * (2 ** attempt), ZOOM_RETRY_MAX_DELAY)
                        logger.warning("Zoom rate limited, retrying in %ss", delay)
                        await asyncio.sleep(delay)
                        continue

                    if response.status_code >= 500:
                        # Server error - retry
                        delay = min(ZOOM_RETRY_BASE_DELAY * (2 ** attempt), ZOOM_RETRY_MAX_DELAY)
                        logger.warning("Zoom server error, retrying in %ss", delay)
                        await asyncio.sleep(delay)
                        continue

                    if response.status_code == 204:
                        return {}

                    if response.status_code >= 400:
                        error_data = response.json() if response.content else {}
                        raise ValueError(
                            error_data.get("message", f"Zoom API error: {response.status_code}")
                        )

                    return response.json()

            except httpx.RequestError as e:
                last_error = e
                delay = min(ZOOM_RETRY_BASE_DELAY * (2 ** attempt), ZOOM_RETRY_MAX_DELAY)
                logger.warning("Zoom connection error, retrying in %ss: %s", delay, e)
                await asyncio.sleep(delay)
                continue

        raise last_error or ValueError("Zoom API request failed after retries")

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
        """Create a Zoom meeting."""
        try:
            meeting_data = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration": duration_minutes,
                "timezone": "UTC",
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": True,
                    "waiting_room": False,
                    "mute_upon_entry": False,
                    "audio": "both",
                    "auto_recording": "none",
                },
            }

            result = await self._api_request(
                "POST",
                "/users/me/meetings",
                json=meeting_data,
            )

            logger.info(
                "Created Zoom meeting %s for booking %s",
                result.get("id"),
                booking_id,
            )

            return MeetingResult(
                success=True,
                join_url=result.get("join_url"),
                host_url=result.get("start_url"),
                meeting_id=str(result.get("id")),
                provider=MeetingProvider.ZOOM.value,
            )

        except Exception as e:
            logger.error("Failed to create Zoom meeting: %s", e)
            return MeetingResult(
                success=False,
                provider=MeetingProvider.ZOOM.value,
                error_message=str(e),
                needs_retry=True,
            )

    async def cancel_meeting(
        self,
        meeting_id: str,
        *,
        notify_attendees: bool = True,
    ) -> MeetingResult:
        """Cancel a Zoom meeting."""
        try:
            await self._api_request(
                "DELETE",
                f"/meetings/{meeting_id}",
                params={"schedule_for_reminder": str(notify_attendees).lower()},
            )

            logger.info("Cancelled Zoom meeting %s", meeting_id)

            return MeetingResult(
                success=True,
                meeting_id=meeting_id,
                provider=MeetingProvider.ZOOM.value,
            )

        except Exception as e:
            logger.error("Failed to cancel Zoom meeting %s: %s", meeting_id, e)
            return MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=MeetingProvider.ZOOM.value,
                error_message=str(e),
            )

    async def update_meeting(
        self,
        meeting_id: str,
        *,
        topic: str | None = None,
        start_time: datetime | None = None,
        duration_minutes: int | None = None,
    ) -> MeetingResult:
        """Update a Zoom meeting."""
        try:
            update_data: dict[str, Any] = {}

            if topic:
                update_data["topic"] = topic
            if start_time:
                update_data["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            if duration_minutes:
                update_data["duration"] = duration_minutes

            if update_data:
                await self._api_request(
                    "PATCH",
                    f"/meetings/{meeting_id}",
                    json=update_data,
                )

            logger.info("Updated Zoom meeting %s", meeting_id)

            return MeetingResult(
                success=True,
                meeting_id=meeting_id,
                provider=MeetingProvider.ZOOM.value,
            )

        except Exception as e:
            logger.error("Failed to update Zoom meeting %s: %s", meeting_id, e)
            return MeetingResult(
                success=False,
                meeting_id=meeting_id,
                provider=MeetingProvider.ZOOM.value,
                error_message=str(e),
            )

    async def get_meeting_status(
        self,
        meeting_id: str,
    ) -> MeetingDetails | None:
        """Get the status of a Zoom meeting."""
        try:
            result = await self._api_request(
                "GET",
                f"/meetings/{meeting_id}",
            )

            status_map = {
                "waiting": MeetingStatus.SCHEDULED,
                "started": MeetingStatus.IN_PROGRESS,
                "finished": MeetingStatus.COMPLETED,
            }

            zoom_status = result.get("status", "waiting")

            return MeetingDetails(
                meeting_id=str(result.get("id")),
                provider=MeetingProvider.ZOOM,
                join_url=result.get("join_url", ""),
                host_url=result.get("start_url"),
                status=status_map.get(zoom_status, MeetingStatus.SCHEDULED),
                start_time=datetime.fromisoformat(result.get("start_time", "").replace("Z", "+00:00"))
                if result.get("start_time")
                else None,
                duration_minutes=result.get("duration"),
                topic=result.get("topic"),
            )

        except Exception as e:
            logger.error("Failed to get Zoom meeting status %s: %s", meeting_id, e)
            return None

    def get_provider(self) -> MeetingProvider:
        """Get the provider type."""
        return MeetingProvider.ZOOM


# Default instance
zoom_adapter = ZoomAdapter()
