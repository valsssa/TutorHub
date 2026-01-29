"""
Zoom Integration Router

Handles:
- Zoom OAuth for tutor account connection
- Meeting creation for bookings
- Meeting management
- Resilient meeting creation with retries
"""

import asyncio
import base64
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel

from core.config import settings
from core.dependencies import CurrentUser, DatabaseSession, TutorUser
from core.rate_limiting import limiter
from models import Booking

logger = logging.getLogger(__name__)

# Retry configuration for Zoom API calls
ZOOM_MAX_RETRIES = 3
ZOOM_RETRY_BASE_DELAY = 1.0  # Base delay in seconds
ZOOM_RETRY_MAX_DELAY = 10.0  # Maximum delay between retries

router = APIRouter(
    prefix="/integrations/zoom",
    tags=["integrations"],
)

# Zoom API endpoints
ZOOM_AUTH_URL = "https://zoom.us/oauth/authorize"
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"


# ============================================================================
# Schemas
# ============================================================================


class ZoomConnectionStatus(BaseModel):
    """Zoom connection status."""
    is_connected: bool
    zoom_email: str | None = None
    connected_at: datetime | None = None


class ZoomAuthURLResponse(BaseModel):
    """Zoom OAuth authorization URL."""
    authorization_url: str


class ZoomMeetingResponse(BaseModel):
    """Created Zoom meeting details."""
    meeting_id: int
    join_url: str
    start_url: str
    password: str | None = None
    topic: str


# ============================================================================
# Zoom Exceptions
# ============================================================================


class ZoomError(Exception):
    """Base exception for Zoom API errors."""

    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False):
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


class ZoomRateLimitError(ZoomError):
    """Zoom rate limit exceeded."""

    def __init__(self, message: str = "Zoom rate limit exceeded"):
        super().__init__(message, status_code=429, retryable=True)


class ZoomServiceError(ZoomError):
    """Zoom service unavailable or server error."""

    def __init__(self, message: str = "Zoom service unavailable"):
        super().__init__(message, status_code=503, retryable=True)


class ZoomAuthError(ZoomError):
    """Zoom authentication error."""

    def __init__(self, message: str = "Zoom authentication failed"):
        super().__init__(message, status_code=401, retryable=False)


# ============================================================================
# Zoom API Client
# ============================================================================


class ZoomClient:
    """Zoom API client using Server-to-Server OAuth."""

    def __init__(self):
        self._access_token: str | None = None
        self._token_expires: datetime | None = None

    async def _get_access_token(self) -> str:
        """Get or refresh Server-to-Server OAuth token."""

        if not settings.ZOOM_CLIENT_ID or not settings.ZOOM_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Zoom integration not configured",
            )

        # Check if token is still valid
        if (
            self._access_token
            and self._token_expires
            and datetime.now(UTC) < self._token_expires - timedelta(minutes=5)
        ):
            return self._access_token

        # Get new token using Server-to-Server OAuth
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
                logger.error(f"Zoom token error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to authenticate with Zoom",
                )

            data = response.json()
            self._access_token = data["access_token"]
            self._token_expires = datetime.now(UTC) + timedelta(seconds=data["expires_in"])

            return self._access_token

    async def create_meeting(
        self,
        topic: str,
        start_time: datetime,
        duration_minutes: int,
        tutor_email: str | None = None,
        student_email: str | None = None,
        max_retries: int = ZOOM_MAX_RETRIES,
    ) -> dict:
        """
        Create a Zoom meeting with retry logic.

        Args:
            topic: Meeting topic/title
            start_time: Scheduled start time
            duration_minutes: Meeting duration
            tutor_email: Tutor's email (for logging)
            student_email: Student's email (for logging)
            max_retries: Maximum number of retry attempts

        Returns:
            Zoom API response with meeting details

        Raises:
            ZoomError: If meeting creation fails after all retries
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await self._create_meeting_attempt(
                    topic=topic,
                    start_time=start_time,
                    duration_minutes=duration_minutes,
                )
            except ZoomError as e:
                last_error = e
                if not e.retryable or attempt >= max_retries:
                    logger.error(
                        "Zoom meeting creation failed (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries + 1,
                        e.message,
                    )
                    raise

                # Calculate delay with exponential backoff and jitter
                delay = min(
                    ZOOM_RETRY_BASE_DELAY * (2 ** attempt) + (asyncio.get_event_loop().time() % 1),
                    ZOOM_RETRY_MAX_DELAY,
                )
                logger.warning(
                    "Zoom meeting creation failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    e.message,
                )
                await asyncio.sleep(delay)

            except Exception as e:
                last_error = e
                logger.error("Unexpected error creating Zoom meeting: %s", e)
                raise ZoomError(str(e), retryable=False)

        # Should not reach here, but just in case
        raise last_error or ZoomError("Failed to create Zoom meeting after retries")

    async def _create_meeting_attempt(
        self,
        topic: str,
        start_time: datetime,
        duration_minutes: int,
    ) -> dict:
        """Single attempt to create a Zoom meeting."""
        token = await self._get_access_token()

        # Format start time for Zoom (ISO 8601)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        meeting_payload = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time_str,
            "duration": duration_minutes,
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "waiting_room": False,
                "mute_upon_entry": False,
                "auto_recording": "none",
                "meeting_authentication": False,
            },
        }

        # Use "me" for the authenticated user (Server-to-Server)
        user_id = "me"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{ZOOM_API_BASE}/users/{user_id}/meetings",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=meeting_payload,
                )
            except httpx.TimeoutException:
                raise ZoomServiceError("Zoom API request timed out")
            except httpx.ConnectError:
                raise ZoomServiceError("Failed to connect to Zoom API")

            if response.status_code in (200, 201):
                return response.json()

            # Handle specific error codes
            if response.status_code == 429:
                raise ZoomRateLimitError()
            elif response.status_code == 401:
                # Clear cached token and retry
                self._access_token = None
                self._token_expires = None
                raise ZoomAuthError()
            elif response.status_code >= 500:
                raise ZoomServiceError(f"Zoom server error: {response.status_code}")
            else:
                logger.error("Zoom meeting creation error: %s", response.text)
                raise ZoomError(
                    f"Failed to create Zoom meeting: {response.text}",
                    status_code=response.status_code,
                    retryable=False,
                )

    async def get_meeting(self, meeting_id: int) -> dict:
        """Get meeting details."""

        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ZOOM_API_BASE}/meetings/{meeting_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Meeting not found",
                )

            return response.json()

    async def delete_meeting(self, meeting_id: int) -> bool:
        """Delete a meeting."""

        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{ZOOM_API_BASE}/meetings/{meeting_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            return response.status_code == 204


# Singleton client
zoom_client = ZoomClient()


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/status",
    response_model=ZoomConnectionStatus,
    summary="Check Zoom integration status",
)
@limiter.limit("30/minute")
async def get_zoom_status(request: Request) -> ZoomConnectionStatus:
    """Check if Zoom integration is configured."""

    is_configured = bool(
        settings.ZOOM_CLIENT_ID
        and settings.ZOOM_CLIENT_SECRET
        and settings.ZOOM_ACCOUNT_ID
    )

    return ZoomConnectionStatus(
        is_connected=is_configured,
        zoom_email=None,  # Server-to-Server doesn't have user email
        connected_at=None,
    )


@router.post(
    "/meetings/create",
    response_model=ZoomMeetingResponse,
    summary="Create Zoom meeting for booking",
    description="""
**Create a Zoom meeting for a confirmed booking**

Automatically generates a Zoom meeting link and updates the booking.
Only tutors can create meetings for their own bookings.
    """,
)
@limiter.limit("20/minute")
async def create_meeting_for_booking(
    request: Request,
    booking_id: Annotated[int, Query(description="Booking ID")],
    current_user: TutorUser,
    db: DatabaseSession,
) -> ZoomMeetingResponse:
    """Create a Zoom meeting for a booking."""

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify ownership
    if not booking.tutor_profile or booking.tutor_profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create meetings for your own bookings",
        )

    # Check booking status
    if booking.status not in ("PENDING", "CONFIRMED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create meeting for booking with status {booking.status}",
        )

    # Build meeting topic
    topic = f"EduStream: {booking.subject_name or 'Tutoring Session'}"
    if booking.student_name:
        topic += f" with {booking.student_name}"

    # Create meeting
    meeting = await zoom_client.create_meeting(
        topic=topic,
        start_time=booking.start_time,
        duration_minutes=int((booking.end_time - booking.start_time).total_seconds() / 60),
        tutor_email=current_user.email,
        student_email=booking.student.email if booking.student else None,
    )

    # Update booking with meeting URL
    booking.join_url = meeting["join_url"]
    booking.meeting_url = meeting["start_url"]  # Host URL
    booking.zoom_meeting_id = str(meeting["id"])
    booking.updated_at = datetime.now(UTC)
    db.commit()

    logger.info(f"Created Zoom meeting {meeting['id']} for booking {booking_id}")

    return ZoomMeetingResponse(
        meeting_id=meeting["id"],
        join_url=meeting["join_url"],
        start_url=meeting["start_url"],
        password=meeting.get("password"),
        topic=meeting["topic"],
    )


@router.delete(
    "/meetings/{meeting_id}",
    summary="Delete Zoom meeting",
)
@limiter.limit("20/minute")
async def delete_meeting(
    request: Request,
    meeting_id: int,
    current_user: TutorUser,
    db: DatabaseSession,
):
    """Delete a Zoom meeting."""

    # Find booking with this meeting
    booking = db.query(Booking).filter(Booking.zoom_meeting_id == str(meeting_id)).first()

    if booking:
        # Verify ownership
        if not booking.tutor_profile or booking.tutor_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Clear meeting info from booking
        booking.join_url = None
        booking.meeting_url = None
        booking.zoom_meeting_id = None
        booking.updated_at = datetime.now(UTC)
        db.commit()

    # Delete from Zoom
    success = await zoom_client.delete_meeting(meeting_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or already deleted",
        )

    return {"message": "Meeting deleted successfully"}


@router.post(
    "/meetings/auto-create",
    summary="Auto-create meetings for confirmed bookings",
    description="Admin endpoint to auto-create Zoom meetings for all confirmed bookings without one.",
)
@limiter.limit("10/minute")
async def auto_create_meetings(
    request: Request,
    current_user: CurrentUser,
    db: DatabaseSession,
    hours_ahead: Annotated[int, Query(ge=1, le=72)] = 24,
):
    """Auto-create meetings for upcoming confirmed bookings."""

    from core.config import Roles

    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Find confirmed bookings without meeting URL in the next X hours
    cutoff = datetime.now(UTC) + timedelta(hours=hours_ahead)

    bookings = (
        db.query(Booking)
        .filter(
            Booking.status == "CONFIRMED",
            Booking.start_time <= cutoff,
            Booking.start_time > datetime.now(UTC),
            Booking.join_url.is_(None),
        )
        .all()
    )

    created = 0
    errors = []

    for booking in bookings:
        try:
            topic = f"EduStream: {booking.subject_name or 'Tutoring Session'}"

            meeting = await zoom_client.create_meeting(
                topic=topic,
                start_time=booking.start_time,
                duration_minutes=int((booking.end_time - booking.start_time).total_seconds() / 60),
            )

            booking.join_url = meeting["join_url"]
            booking.meeting_url = meeting["start_url"]
            booking.zoom_meeting_id = str(meeting["id"])
            booking.updated_at = datetime.now(UTC)

            created += 1

        except Exception as e:
            errors.append({"booking_id": booking.id, "error": str(e)})

    db.commit()

    return {
        "created": created,
        "errors": errors,
        "total_checked": len(bookings),
    }
