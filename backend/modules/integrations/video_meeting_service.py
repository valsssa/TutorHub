"""
Video Meeting Provider Service

Abstracts video conferencing provider selection and meeting creation.
Supports: Zoom (Server-to-Server), Google Meet, Microsoft Teams, Custom URLs.

Usage:
    service = VideoMeetingService(db)
    result = await service.create_meeting_for_booking(booking, tutor_profile)
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session

from models import Booking, TutorProfile

logger = logging.getLogger(__name__)


class VideoProvider(str, Enum):
    """Supported video meeting providers."""
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    CUSTOM = "custom"
    MANUAL = "manual"  # Tutor provides URL manually for each booking


@dataclass
class MeetingResult:
    """Result of meeting creation attempt."""
    success: bool
    join_url: str | None = None
    host_url: str | None = None
    meeting_id: str | None = None
    provider: str | None = None
    error_message: str | None = None
    needs_retry: bool = False


class VideoMeetingService:
    """
    Service for creating video meetings using tutor's preferred provider.

    Provider Priority:
    1. Use tutor's preferred_video_provider if configured
    2. Fall back to Zoom if available
    3. Generate platform meeting link as final fallback
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_meeting_for_booking(
        self,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> MeetingResult:
        """
        Create a video meeting for a booking using the tutor's preferred provider.

        Args:
            booking: The booking to create a meeting for
            tutor_profile: Tutor's profile with provider preferences

        Returns:
            MeetingResult with meeting details or error information
        """
        provider = self._get_effective_provider(tutor_profile)

        logger.info(
            "Creating meeting for booking %d using provider %s",
            booking.id,
            provider,
        )

        # Route to appropriate provider
        if provider == VideoProvider.ZOOM:
            return await self._create_zoom_meeting(booking, tutor_profile)
        elif provider == VideoProvider.GOOGLE_MEET:
            return await self._create_google_meet_link(booking, tutor_profile)
        elif provider == VideoProvider.TEAMS:
            return self._create_teams_link(booking, tutor_profile)
        elif provider == VideoProvider.CUSTOM:
            return self._create_custom_link(booking, tutor_profile)
        elif provider == VideoProvider.MANUAL:
            return MeetingResult(
                success=True,
                join_url=None,  # Tutor will provide manually
                provider=provider.value,
            )
        else:
            return await self._create_fallback_link(booking)

    def _get_effective_provider(self, tutor_profile: TutorProfile) -> VideoProvider:
        """Determine which provider to use based on tutor preferences and availability."""
        preferred = getattr(tutor_profile, 'preferred_video_provider', None)

        if preferred:
            try:
                return VideoProvider(preferred)
            except ValueError:
                logger.warning(
                    "Unknown video provider '%s' for tutor %d, falling back to Zoom",
                    preferred,
                    tutor_profile.id,
                )

        return VideoProvider.ZOOM

    async def _create_zoom_meeting(
        self,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> MeetingResult:
        """Create a Zoom meeting using Server-to-Server OAuth."""
        try:
            from modules.integrations.zoom_router import ZoomError, zoom_client

            # Build meeting topic
            topic = f"EduStream: {booking.subject_name or 'Tutoring Session'}"
            if booking.student_name:
                topic += f" with {booking.student_name}"

            duration_minutes = int((booking.end_time - booking.start_time).total_seconds() / 60)

            # Get emails for logging
            tutor_email = tutor_profile.user.email if tutor_profile.user else None
            student_email = booking.student.email if booking.student else None

            meeting = await zoom_client.create_meeting(
                topic=topic,
                start_time=booking.start_time,
                duration_minutes=duration_minutes,
                tutor_email=tutor_email,
                student_email=student_email,
            )

            logger.info("Created Zoom meeting %s for booking %d", meeting["id"], booking.id)

            return MeetingResult(
                success=True,
                join_url=meeting["join_url"],
                host_url=meeting.get("start_url"),
                meeting_id=str(meeting["id"]),
                provider=VideoProvider.ZOOM.value,
            )

        except ZoomError as e:
            logger.error(
                "Zoom meeting creation failed for booking %d: %s",
                booking.id,
                e.message,
            )
            return MeetingResult(
                success=False,
                provider=VideoProvider.ZOOM.value,
                error_message=e.message,
                needs_retry=e.retryable,
            )
        except Exception as e:
            logger.error(
                "Unexpected error creating Zoom meeting for booking %d: %s",
                booking.id,
                str(e),
            )
            return MeetingResult(
                success=False,
                provider=VideoProvider.ZOOM.value,
                error_message=str(e),
                needs_retry=True,
            )

    async def _create_google_meet_link(
        self,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> MeetingResult:
        """
        Create a Google Meet link via Calendar API with conferenceData.

        Requires the tutor to have connected their Google Calendar.
        Creates a calendar event with an automatically generated Meet link.
        """
        try:
            from core.google_calendar import google_calendar

            tutor_user = tutor_profile.user
            if not tutor_user or not tutor_user.google_calendar_refresh_token:
                logger.warning(
                    "Tutor %d has Google Meet as preferred provider but no calendar connected",
                    tutor_profile.id,
                )
                return MeetingResult(
                    success=False,
                    provider=VideoProvider.GOOGLE_MEET.value,
                    error_message="Google Calendar not connected. Please connect your Google Calendar to use Google Meet.",
                    needs_retry=False,
                )

            # Refresh token if needed
            access_token = tutor_user.google_calendar_access_token
            from datetime import UTC, timedelta
            if (
                tutor_user.google_calendar_token_expires
                and datetime.now(UTC) >= tutor_user.google_calendar_token_expires - timedelta(minutes=5)
            ):
                try:
                    tokens = await google_calendar.refresh_access_token(
                        tutor_user.google_calendar_refresh_token
                    )
                    access_token = tokens["access_token"]
                    # Update token in database
                    tutor_user.google_calendar_access_token = access_token
                    tutor_user.google_calendar_token_expires = datetime.now(UTC) + timedelta(
                        seconds=tokens.get("expires_in", 3600)
                    )
                    self.db.flush()
                except Exception as e:
                    logger.error("Failed to refresh calendar token: %s", e)
                    return MeetingResult(
                        success=False,
                        provider=VideoProvider.GOOGLE_MEET.value,
                        error_message="Calendar token expired. Please reconnect your Google Calendar.",
                        needs_retry=False,
                    )

            # Create calendar event with Google Meet conference
            meet_link = await self._create_calendar_event_with_meet(
                access_token=access_token,
                refresh_token=tutor_user.google_calendar_refresh_token,
                booking=booking,
                tutor_profile=tutor_profile,
            )

            if meet_link:
                return MeetingResult(
                    success=True,
                    join_url=meet_link,
                    provider=VideoProvider.GOOGLE_MEET.value,
                )
            else:
                return MeetingResult(
                    success=False,
                    provider=VideoProvider.GOOGLE_MEET.value,
                    error_message="Failed to create Google Meet link",
                    needs_retry=True,
                )

        except Exception as e:
            logger.error(
                "Google Meet creation failed for booking %d: %s",
                booking.id,
                str(e),
            )
            return MeetingResult(
                success=False,
                provider=VideoProvider.GOOGLE_MEET.value,
                error_message=str(e),
                needs_retry=True,
            )

    async def _create_calendar_event_with_meet(
        self,
        access_token: str,
        refresh_token: str,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> str | None:
        """Create a Google Calendar event with automatically generated Meet link."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            from core.config import settings

            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
            )

            service = build("calendar", "v3", credentials=credentials)

            # Build event with conference data request
            tutor_name = booking.tutor_name or "Tutor"
            student_name = booking.student_name or "Student"
            tutor_email = tutor_profile.user.email if tutor_profile.user else ""
            student_email = booking.student.email if booking.student else ""

            event = {
                "summary": f"Tutoring: {booking.subject_name or 'Session'} - {tutor_name} & {student_name}",
                "description": f"Tutoring session for {booking.subject_name or 'General'}.\n\nBooking ID: #{booking.id}",
                "start": {
                    "dateTime": booking.start_time.isoformat(),
                    "timeZone": booking.tutor_tz or "UTC",
                },
                "end": {
                    "dateTime": booking.end_time.isoformat(),
                    "timeZone": booking.tutor_tz or "UTC",
                },
                "attendees": [
                    {"email": tutor_email, "displayName": tutor_name},
                    {"email": student_email, "displayName": student_name},
                ],
                "conferenceData": {
                    "createRequest": {
                        "requestId": f"edustream-booking-{booking.id}",
                        "conferenceSolutionKey": {
                            "type": "hangoutsMeet"
                        },
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }

            # Create event with conference data
            created_event = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event,
                    conferenceDataVersion=1,  # Required for Meet link generation
                    sendUpdates="all",
                )
                .execute()
            )

            # Extract Meet link from conference data
            conference_data = created_event.get("conferenceData", {})
            entry_points = conference_data.get("entryPoints", [])

            for entry in entry_points:
                if entry.get("entryPointType") == "video":
                    meet_link = entry.get("uri")
                    if meet_link:
                        # Store event ID for future reference
                        booking.google_calendar_event_id = created_event["id"]
                        booking.google_meet_link = meet_link
                        self.db.flush()

                        logger.info(
                            "Created Google Meet link for booking %d: %s",
                            booking.id,
                            meet_link,
                        )
                        return meet_link

            logger.warning("No Meet link found in created calendar event")
            return None

        except Exception as e:
            logger.error("Failed to create calendar event with Meet: %s", e)
            return None

    def _create_teams_link(
        self,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> MeetingResult:
        """
        Create a Microsoft Teams meeting link from template.

        Teams links can be:
        1. Static personal meeting room links (recommended)
        2. Templates with placeholders

        Placeholders supported:
        - {booking_id}: Booking ID
        - {date}: Session date (YYYY-MM-DD)
        - {time}: Session time (HH:MM)
        """
        template = getattr(tutor_profile, 'custom_meeting_url_template', None)

        if not template:
            logger.warning(
                "Tutor %d has Teams as provider but no meeting URL template",
                tutor_profile.id,
            )
            return MeetingResult(
                success=False,
                provider=VideoProvider.TEAMS.value,
                error_message="No Microsoft Teams meeting URL configured. Please add your Teams meeting link in settings.",
                needs_retry=False,
            )

        # Validate it looks like a Teams URL
        if not self._is_valid_teams_url(template):
            return MeetingResult(
                success=False,
                provider=VideoProvider.TEAMS.value,
                error_message="Invalid Microsoft Teams URL format. Please check your meeting link.",
                needs_retry=False,
            )

        # Process template placeholders
        join_url = self._process_url_template(template, booking)

        return MeetingResult(
            success=True,
            join_url=join_url,
            provider=VideoProvider.TEAMS.value,
        )

    def _create_custom_link(
        self,
        booking: Booking,
        tutor_profile: TutorProfile,
    ) -> MeetingResult:
        """
        Create a custom meeting link from tutor's template.

        Supports any video platform (Jitsi, Whereby, etc.) via custom URL.
        """
        template = getattr(tutor_profile, 'custom_meeting_url_template', None)

        if not template:
            logger.warning(
                "Tutor %d has custom provider but no meeting URL template",
                tutor_profile.id,
            )
            return MeetingResult(
                success=False,
                provider=VideoProvider.CUSTOM.value,
                error_message="No custom meeting URL configured. Please add your meeting link in settings.",
                needs_retry=False,
            )

        # Validate URL format
        if not self._is_valid_url(template):
            return MeetingResult(
                success=False,
                provider=VideoProvider.CUSTOM.value,
                error_message="Invalid meeting URL format. Please check your meeting link.",
                needs_retry=False,
            )

        # Process template placeholders
        join_url = self._process_url_template(template, booking)

        return MeetingResult(
            success=True,
            join_url=join_url,
            provider=VideoProvider.CUSTOM.value,
        )

    async def _create_fallback_link(self, booking: Booking) -> MeetingResult:
        """Generate a platform-hosted fallback meeting link."""
        import hashlib
        import time

        # Generate a secure, deterministic token
        secret = "platform_meeting_secret_key"  # Should be in settings
        timestamp = int(time.time() / 3600)
        token_data = f"{booking.id}:{timestamp}:{secret}"
        secure_token = hashlib.sha256(token_data.encode()).hexdigest()[:16]

        # Platform meeting room URL
        from core.config import settings
        base_url = getattr(settings, 'MEETING_BASE_URL', 'https://meet.edustream.com')
        join_url = f"{base_url}/session/{booking.id}?token={secure_token}"

        return MeetingResult(
            success=True,
            join_url=join_url,
            provider="platform",
        )

    def _process_url_template(self, template: str, booking: Booking) -> str:
        """Process URL template with booking-specific placeholders."""
        url = template

        # Replace placeholders
        url = url.replace("{booking_id}", str(booking.id))
        url = url.replace("{date}", booking.start_time.strftime("%Y-%m-%d"))
        url = url.replace("{time}", booking.start_time.strftime("%H-%M"))

        return url

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None

    def _is_valid_teams_url(self, url: str) -> bool:
        """Validate Microsoft Teams URL format."""
        # Teams meeting URLs typically contain teams.microsoft.com or teams.live.com
        teams_patterns = [
            r'teams\.microsoft\.com',
            r'teams\.live\.com',
        ]

        if not self._is_valid_url(url):
            return False

        return any(re.search(pattern, url, re.IGNORECASE) for pattern in teams_patterns)


# Convenience function for use in booking confirmation
async def create_meeting_for_booking(
    db: Session,
    booking: Booking,
    tutor_profile: TutorProfile,
) -> MeetingResult:
    """
    Create a video meeting for a booking using the tutor's preferred provider.

    This is a convenience function that creates a VideoMeetingService instance
    and calls create_meeting_for_booking.
    """
    service = VideoMeetingService(db)
    return await service.create_meeting_for_booking(booking, tutor_profile)
