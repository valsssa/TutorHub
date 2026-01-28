"""
Google Calendar Integration Router

Handles:
- OAuth flow for calendar access
- Calendar connection status
- Manual event creation/sync
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core.config import settings
from core.dependencies import CurrentUser, DatabaseSession
from core.google_calendar import google_calendar
from core.rate_limiting import limiter
from models import Booking, User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/integrations/calendar",
    tags=["integrations"],
)


# ============================================================================
# Schemas
# ============================================================================


class CalendarConnectionStatus(BaseModel):
    """Calendar connection status."""

    is_connected: bool
    calendar_email: str | None = None
    connected_at: datetime | None = None
    can_create_events: bool = False


class CalendarAuthURLResponse(BaseModel):
    """Calendar OAuth authorization URL."""

    authorization_url: str
    state: str


class CalendarEventResponse(BaseModel):
    """Created calendar event details."""

    event_id: str
    html_link: str | None = None
    message: str


# ============================================================================
# State Management (CSRF Protection)
# ============================================================================

# In production, use Redis
_calendar_states: dict[str, dict] = {}


def _generate_state(user_id: int) -> str:
    """Generate OAuth state token for CSRF protection."""
    state = secrets.token_urlsafe(32)
    _calendar_states[state] = {
        "user_id": user_id,
        "created_at": datetime.now(UTC),
    }
    # Clean up old states
    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    for s, data in list(_calendar_states.items()):
        if data["created_at"] < cutoff:
            del _calendar_states[s]
    return state


def _validate_state(state: str) -> dict | None:
    """Validate and consume OAuth state token."""
    if state not in _calendar_states:
        return None
    calendar_state_data = _calendar_states.pop(state)
    if datetime.now(UTC) - calendar_state_data["created_at"] > timedelta(minutes=10):
        return None
    return calendar_state_data


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/status",
    response_model=CalendarConnectionStatus,
    summary="Check Google Calendar connection status",
)
@limiter.limit("30/minute")
async def get_calendar_status(
    request: Request,
    current_user: CurrentUser,
) -> CalendarConnectionStatus:
    """Check if user has connected Google Calendar."""

    is_connected = bool(current_user.google_calendar_refresh_token)

    return CalendarConnectionStatus(
        is_connected=is_connected,
        calendar_email=current_user.google_calendar_email if is_connected else None,
        connected_at=current_user.google_calendar_connected_at if is_connected else None,
        can_create_events=is_connected,
    )


@router.get(
    "/connect",
    response_model=CalendarAuthURLResponse,
    summary="Get Google Calendar authorization URL",
    description="""
**Connect Google Calendar**

Returns the Google authorization URL for calendar access.
Redirect the user to this URL to grant calendar permissions.

After authorization, Google will redirect to the callback URL
with the tokens to store.
    """,
)
@limiter.limit("10/minute")
async def get_calendar_auth_url(
    request: Request,
    current_user: CurrentUser,
) -> CalendarAuthURLResponse:
    """Get Google Calendar OAuth authorization URL."""

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration not configured",
        )

    state = _generate_state(current_user.id)

    authorization_url = google_calendar.get_authorization_url(
        state=state,
        redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URI,
    )

    return CalendarAuthURLResponse(
        authorization_url=authorization_url,
        state=state,
    )


@router.get(
    "/callback",
    summary="Google Calendar OAuth callback",
    description="Handles the OAuth callback from Google after calendar authorization.",
)
@limiter.limit("10/minute")
async def calendar_callback(
    request: Request,
    code: Annotated[str, Query(description="Authorization code from Google")],
    state: Annotated[str, Query(description="State parameter for CSRF protection")],
    db: DatabaseSession,
):
    """Handle Google Calendar OAuth callback."""

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration not configured",
        )

    # Validate state
    state_data = _validate_state(state)
    if not state_data:
        logger.warning("Invalid or expired calendar OAuth state")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings/integrations?error=invalid_state"
        )

    user_id = state_data["user_id"]

    try:
        # Exchange code for tokens
        tokens = await google_calendar.exchange_code_for_tokens(code)

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)

        if not refresh_token:
            logger.error("No refresh token received from Google")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/settings/integrations?error=no_refresh_token"
            )

        # Get user's calendar email
        calendars = await google_calendar.get_user_calendars(access_token, refresh_token)
        primary_calendar = next(
            (c for c in calendars if c.get("primary")), calendars[0] if calendars else None
        )
        calendar_email = primary_calendar.get("id") if primary_calendar else None

        # Update user with calendar tokens
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/settings/integrations?error=user_not_found"
            )

        user.google_calendar_access_token = access_token
        user.google_calendar_refresh_token = refresh_token
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(seconds=expires_in)
        user.google_calendar_email = calendar_email
        user.google_calendar_connected_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        db.commit()

        logger.info(f"User {user_id} connected Google Calendar: {calendar_email}")

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings/integrations?calendar=connected"
        )

    except Exception as e:
        logger.error(f"Calendar OAuth error: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings/integrations?error=oauth_error"
        )


@router.delete(
    "/disconnect",
    summary="Disconnect Google Calendar",
    description="Remove Google Calendar connection and delete stored tokens.",
)
@limiter.limit("20/minute")
async def disconnect_calendar(
    request: Request,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Disconnect Google Calendar from user account."""

    if not current_user.google_calendar_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar not connected",
        )

    # Clear calendar tokens
    user = db.query(User).filter(User.id == current_user.id).first()
    user.google_calendar_access_token = None
    user.google_calendar_refresh_token = None
    user.google_calendar_token_expires = None
    user.google_calendar_email = None
    user.google_calendar_connected_at = None
    user.updated_at = datetime.now(UTC)
    db.commit()

    logger.info(f"User {current_user.id} disconnected Google Calendar")

    return {"message": "Google Calendar disconnected successfully"}


@router.post(
    "/events/booking/{booking_id}",
    response_model=CalendarEventResponse,
    summary="Create calendar event for booking",
    description="Manually create a calendar event for a specific booking.",
)
@limiter.limit("20/minute")
async def create_booking_event(
    request: Request,
    booking_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CalendarEventResponse:
    """Create calendar event for a booking."""

    # Check calendar connection
    if not current_user.google_calendar_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar not connected. Please connect your calendar first.",
        )

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify user is part of this booking
    is_tutor = booking.tutor_profile and booking.tutor_profile.user_id == current_user.id
    is_student = booking.student_id == current_user.id

    if not is_tutor and not is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not part of this booking",
        )

    # Check if event already exists
    if booking.google_calendar_event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calendar event already exists for this booking",
        )

    # Refresh token if needed
    access_token = current_user.google_calendar_access_token
    if (
        current_user.google_calendar_token_expires
        and datetime.now(UTC) >= current_user.google_calendar_token_expires - timedelta(minutes=5)
    ):
        try:
            tokens = await google_calendar.refresh_access_token(
                current_user.google_calendar_refresh_token
            )
            access_token = tokens["access_token"]
            user = db.query(User).filter(User.id == current_user.id).first()
            user.google_calendar_access_token = access_token
            user.google_calendar_token_expires = datetime.now(UTC) + timedelta(
                seconds=tokens.get("expires_in", 3600)
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to refresh calendar token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Calendar token expired. Please reconnect your calendar.",
            )

    # Get names
    tutor_name = booking.tutor_name or "Tutor"
    student_name = booking.student_name or "Student"
    tutor_email = booking.tutor_profile.user.email if booking.tutor_profile else ""
    student_email = booking.student.email if booking.student else ""

    # Create event
    event_data = await google_calendar.create_booking_event(
        access_token=access_token,
        refresh_token=current_user.google_calendar_refresh_token,
        booking_id=booking.id,
        title=f"Tutoring: {booking.subject_name or 'Session'} - {tutor_name} & {student_name}",
        description=f"Tutoring session for {booking.subject_name or 'General'}.\n\nTopic: {booking.topic or 'Not specified'}",
        start_time=booking.start_time,
        end_time=booking.end_time,
        tutor_email=tutor_email,
        student_email=student_email,
        tutor_name=tutor_name,
        student_name=student_name,
        meeting_url=booking.join_url,
        timezone=booking.tutor_tz or "UTC",
    )

    if not event_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create calendar event",
        )

    # Store event ID on booking
    booking.google_calendar_event_id = event_data["event_id"]
    booking.updated_at = datetime.now(UTC)
    db.commit()

    return CalendarEventResponse(
        event_id=event_data["event_id"],
        html_link=event_data.get("html_link"),
        message="Calendar event created successfully",
    )


@router.delete(
    "/events/booking/{booking_id}",
    summary="Delete calendar event for booking",
)
@limiter.limit("20/minute")
async def delete_booking_event(
    request: Request,
    booking_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Delete calendar event for a booking."""

    if not current_user.google_calendar_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar not connected",
        )

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if not booking.google_calendar_event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No calendar event exists for this booking",
        )

    # Verify ownership
    is_tutor = booking.tutor_profile and booking.tutor_profile.user_id == current_user.id
    is_student = booking.student_id == current_user.id

    if not is_tutor and not is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not part of this booking",
        )

    # Delete event
    success = await google_calendar.delete_booking_event(
        access_token=current_user.google_calendar_access_token,
        refresh_token=current_user.google_calendar_refresh_token,
        event_id=booking.google_calendar_event_id,
    )

    if success:
        booking.google_calendar_event_id = None
        booking.updated_at = datetime.now(UTC)
        db.commit()

    return {"message": "Calendar event deleted" if success else "Event may have been already deleted"}
