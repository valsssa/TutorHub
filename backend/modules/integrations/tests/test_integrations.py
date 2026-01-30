"""
Comprehensive tests for the integrations module.

Tests cover:
- Google Calendar integration (OAuth, events, connection management)
- Zoom integration (OAuth, meeting creation, management)
- Error handling and edge cases
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from httpx import ConnectError, TimeoutException

from models import Booking, User


# =============================================================================
# Calendar Router Tests
# =============================================================================


class TestCalendarConnectionStatus:
    """Tests for calendar connection status endpoint."""

    def test_get_status_not_connected(self, client, tutor_token, tutor_user, db_session):
        """Test getting status when calendar is not connected."""
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.get(
            "/api/v1/integrations/calendar/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is False
        assert data["calendar_email"] is None
        assert data["can_create_events"] is False

    def test_get_status_connected(self, client, tutor_token, tutor_user, db_session):
        """Test getting status when calendar is connected."""
        tutor_user.google_calendar_refresh_token = "test_refresh_token"
        tutor_user.google_calendar_email = "tutor@gmail.com"
        tutor_user.google_calendar_connected_at = datetime.now(UTC)
        db_session.commit()

        response = client.get(
            "/api/v1/integrations/calendar/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is True
        assert data["calendar_email"] == "tutor@gmail.com"
        assert data["can_create_events"] is True

    def test_get_status_unauthenticated(self, client):
        """Test that status endpoint requires authentication."""
        response = client.get("/api/v1/integrations/calendar/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCalendarConnect:
    """Tests for calendar OAuth connect endpoint."""

    @patch("modules.integrations.calendar_router.settings")
    def test_connect_not_configured(self, mock_settings, client, tutor_token):
        """Test connect when Google Calendar is not configured."""
        mock_settings.GOOGLE_CLIENT_ID = None

        response = client.get(
            "/api/v1/integrations/calendar/connect",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "not configured" in response.json()["detail"]

    @patch("modules.integrations.calendar_router.oauth_state_store")
    @patch("modules.integrations.calendar_router.google_calendar")
    @patch("modules.integrations.calendar_router.settings")
    def test_connect_returns_auth_url(
        self, mock_settings, mock_calendar, mock_state_store, client, tutor_token
    ):
        """Test that connect returns an authorization URL."""
        mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
        mock_settings.GOOGLE_CALENDAR_REDIRECT_URI = "http://localhost/callback"
        mock_state_store.generate_state = AsyncMock(return_value="test_state_token")
        mock_calendar.get_authorization_url.return_value = "https://accounts.google.com/o/oauth2/auth?..."

        response = client.get(
            "/api/v1/integrations/calendar/connect",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["state"] == "test_state_token"

    def test_connect_unauthenticated(self, client):
        """Test that connect endpoint requires authentication."""
        response = client.get("/api/v1/integrations/calendar/connect")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCalendarCallback:
    """Tests for calendar OAuth callback endpoint."""

    @patch("modules.integrations.calendar_router.settings")
    def test_callback_not_configured(self, mock_settings, client):
        """Test callback when Google Calendar is not configured."""
        mock_settings.GOOGLE_CLIENT_ID = None

        response = client.get(
            "/api/v1/integrations/calendar/callback",
            params={"code": "test_code", "state": "test_state"},
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @patch("modules.integrations.calendar_router.oauth_state_store")
    @patch("modules.integrations.calendar_router.settings")
    def test_callback_invalid_state(self, mock_settings, mock_state_store, client):
        """Test callback with invalid OAuth state."""
        mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_state_store.validate_state = AsyncMock(return_value=None)

        response = client.get(
            "/api/v1/integrations/calendar/callback",
            params={"code": "test_code", "state": "invalid_state"},
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert "error=invalid_state" in response.headers["location"]


class TestCalendarDisconnect:
    """Tests for calendar disconnect endpoint."""

    def test_disconnect_not_connected(self, client, tutor_token, tutor_user, db_session):
        """Test disconnect when not connected."""
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.delete(
            "/api/v1/integrations/calendar/disconnect",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not connected" in response.json()["detail"]

    def test_disconnect_success(self, client, tutor_token, tutor_user, db_session):
        """Test successful calendar disconnect."""
        tutor_user.google_calendar_refresh_token = "test_token"
        tutor_user.google_calendar_access_token = "access_token"
        tutor_user.google_calendar_email = "test@gmail.com"
        db_session.commit()

        response = client.delete(
            "/api/v1/integrations/calendar/disconnect",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "disconnected" in response.json()["message"]

        db_session.refresh(tutor_user)
        assert tutor_user.google_calendar_refresh_token is None
        assert tutor_user.google_calendar_access_token is None

    def test_disconnect_unauthenticated(self, client):
        """Test that disconnect requires authentication."""
        response = client.delete("/api/v1/integrations/calendar/disconnect")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCalendarBookingEvent:
    """Tests for calendar event creation for bookings."""

    def test_create_event_not_connected(
        self, client, tutor_token, tutor_user, test_booking, db_session
    ):
        """Test creating event when calendar is not connected."""
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.post(
            f"/api/v1/integrations/calendar/events/booking/{test_booking.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not connected" in response.json()["detail"]

    def test_create_event_booking_not_found(self, client, tutor_token, tutor_user, db_session):
        """Test creating event for non-existent booking."""
        tutor_user.google_calendar_refresh_token = "test_token"
        db_session.commit()

        response = client.post(
            "/api/v1/integrations/calendar/events/booking/99999",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_event_not_part_of_booking(
        self, client, student_token, student_user, tutor_user, test_booking, db_session
    ):
        """Test creating event when not part of the booking."""
        # Create another student who is not part of the booking
        from tests.conftest import create_test_user

        other_student = create_test_user(
            db_session, "other@test.com", "OtherPass123!", "student"
        )
        from core.security import TokenManager

        other_token = TokenManager.create_access_token({"sub": other_student.email})

        other_student.google_calendar_refresh_token = "test_token"
        db_session.commit()

        response = client.post(
            f"/api/v1/integrations/calendar/events/booking/{test_booking.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_event_already_exists(
        self, client, tutor_token, tutor_user, test_booking, db_session
    ):
        """Test creating event when one already exists."""
        tutor_user.google_calendar_refresh_token = "test_token"
        test_booking.google_calendar_event_id = "existing_event_id"
        db_session.commit()

        response = client.post(
            f"/api/v1/integrations/calendar/events/booking/{test_booking.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_delete_event_not_connected(self, client, tutor_token, tutor_user, db_session):
        """Test deleting event when calendar is not connected."""
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.delete(
            "/api/v1/integrations/calendar/events/booking/1",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_event_booking_not_found(self, client, tutor_token, tutor_user, db_session):
        """Test deleting event for non-existent booking."""
        tutor_user.google_calendar_refresh_token = "test_token"
        db_session.commit()

        response = client.delete(
            "/api/v1/integrations/calendar/events/booking/99999",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_event_no_event_exists(
        self, client, tutor_token, tutor_user, test_booking, db_session
    ):
        """Test deleting event when none exists."""
        tutor_user.google_calendar_refresh_token = "test_token"
        test_booking.google_calendar_event_id = None
        db_session.commit()

        response = client.delete(
            f"/api/v1/integrations/calendar/events/booking/{test_booking.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No calendar event" in response.json()["detail"]


# =============================================================================
# Zoom Router Tests
# =============================================================================


class TestZoomConnectionStatus:
    """Tests for Zoom connection status endpoint."""

    @patch("modules.integrations.zoom_router.settings")
    def test_status_configured(self, mock_settings, client, tutor_token):
        """Test status when Zoom is configured."""
        mock_settings.ZOOM_CLIENT_ID = "test_client_id"
        mock_settings.ZOOM_CLIENT_SECRET = "test_secret"
        mock_settings.ZOOM_ACCOUNT_ID = "test_account"

        response = client.get(
            "/api/v1/integrations/zoom/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is True

    @patch("modules.integrations.zoom_router.settings")
    def test_status_not_configured(self, mock_settings, client, tutor_token):
        """Test status when Zoom is not configured."""
        mock_settings.ZOOM_CLIENT_ID = None
        mock_settings.ZOOM_CLIENT_SECRET = None
        mock_settings.ZOOM_ACCOUNT_ID = None

        response = client.get(
            "/api/v1/integrations/zoom/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is False


class TestZoomClient:
    """Tests for the ZoomClient class."""

    @pytest.fixture
    def zoom_client(self):
        """Create ZoomClient instance."""
        from modules.integrations.zoom_router import ZoomClient

        return ZoomClient()

    @pytest.mark.asyncio
    @patch("modules.integrations.zoom_router.settings")
    async def test_get_access_token_not_configured(self, mock_settings, zoom_client):
        """Test getting access token when Zoom is not configured."""
        mock_settings.ZOOM_CLIENT_ID = None
        mock_settings.ZOOM_CLIENT_SECRET = None

        with pytest.raises(HTTPException) as exc_info:
            await zoom_client._get_access_token()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    @patch("modules.integrations.zoom_router.settings")
    async def test_get_access_token_caches_token(self, mock_settings, zoom_client):
        """Test that access token is cached."""
        mock_settings.ZOOM_CLIENT_ID = "test_id"
        mock_settings.ZOOM_CLIENT_SECRET = "test_secret"
        mock_settings.ZOOM_ACCOUNT_ID = "test_account"

        # Set a valid cached token
        zoom_client._access_token = "cached_token"
        zoom_client._token_expires = datetime.now(UTC) + timedelta(hours=1)

        token = await zoom_client._get_access_token()
        assert token == "cached_token"


class TestZoomExceptions:
    """Tests for Zoom exception classes."""

    def test_zoom_error_creation(self):
        """Test ZoomError creation."""
        from modules.integrations.zoom_router import ZoomError

        error = ZoomError("Test error", status_code=500, retryable=True)
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.retryable is True

    def test_zoom_rate_limit_error(self):
        """Test ZoomRateLimitError defaults."""
        from modules.integrations.zoom_router import ZoomRateLimitError

        error = ZoomRateLimitError()
        assert error.status_code == 429
        assert error.retryable is True

    def test_zoom_service_error(self):
        """Test ZoomServiceError defaults."""
        from modules.integrations.zoom_router import ZoomServiceError

        error = ZoomServiceError()
        assert error.status_code == 503
        assert error.retryable is True

    def test_zoom_auth_error(self):
        """Test ZoomAuthError defaults."""
        from modules.integrations.zoom_router import ZoomAuthError

        error = ZoomAuthError()
        assert error.status_code == 401
        assert error.retryable is False


class TestZoomMeetingCreation:
    """Tests for Zoom meeting creation endpoint."""

    def test_create_meeting_booking_not_found(self, client, tutor_token):
        """Test creating meeting for non-existent booking."""
        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {tutor_token}"},
            params={"booking_id": 99999},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_meeting_not_tutor(
        self, client, student_token, test_booking
    ):
        """Test that only tutors can create meetings."""
        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {student_token}"},
            params={"booking_id": test_booking.id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_meeting_not_own_booking(
        self, client, tutor_user, test_booking, db_session
    ):
        """Test that tutors can only create meetings for their own bookings."""
        from tests.conftest import create_test_user, create_test_tutor_profile

        other_tutor = create_test_user(
            db_session, "other_tutor@test.com", "OtherPass123!", "tutor"
        )
        create_test_tutor_profile(db_session, other_tutor.id)

        from core.security import TokenManager

        other_token = TokenManager.create_access_token({"sub": other_tutor.email})

        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {other_token}"},
            params={"booking_id": test_booking.id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_meeting_invalid_status(
        self, client, tutor_token, test_booking, db_session
    ):
        """Test creating meeting for booking with invalid status."""
        test_booking.status = "CANCELLED"
        db_session.commit()

        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {tutor_token}"},
            params={"booking_id": test_booking.id},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "CANCELLED" in response.json()["detail"]

    @patch("modules.integrations.zoom_router.zoom_client")
    def test_create_meeting_success(
        self, mock_zoom_client, client, tutor_token, test_booking, db_session
    ):
        """Test successful meeting creation."""
        mock_zoom_client.create_meeting = AsyncMock(
            return_value={
                "id": 123456789,
                "join_url": "https://zoom.us/j/123456789",
                "start_url": "https://zoom.us/s/123456789",
                "password": "test123",
                "topic": "Test Meeting",
            }
        )

        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {tutor_token}"},
            params={"booking_id": test_booking.id},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["meeting_id"] == 123456789
        assert data["join_url"] == "https://zoom.us/j/123456789"


class TestZoomMeetingDeletion:
    """Tests for Zoom meeting deletion endpoint."""

    @patch("modules.integrations.zoom_router.zoom_client")
    def test_delete_meeting_success(
        self, mock_zoom_client, client, tutor_token, tutor_user, test_booking, db_session
    ):
        """Test successful meeting deletion."""
        test_booking.zoom_meeting_id = "123456789"
        db_session.commit()

        mock_zoom_client.delete_meeting = AsyncMock(return_value=True)

        response = client.delete(
            "/api/v1/integrations/zoom/meetings/123456789",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.json()["message"]

    @patch("modules.integrations.zoom_router.zoom_client")
    def test_delete_meeting_not_found(self, mock_zoom_client, client, tutor_token):
        """Test deleting non-existent meeting."""
        mock_zoom_client.delete_meeting = AsyncMock(return_value=False)

        response = client.delete(
            "/api/v1/integrations/zoom/meetings/999999",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_meeting_access_denied(
        self, client, tutor_user, test_booking, db_session
    ):
        """Test that tutors can only delete their own meetings."""
        from tests.conftest import create_test_user, create_test_tutor_profile

        other_tutor = create_test_user(
            db_session, "other_tutor@test.com", "OtherPass123!", "tutor"
        )
        create_test_tutor_profile(db_session, other_tutor.id)

        from core.security import TokenManager

        other_token = TokenManager.create_access_token({"sub": other_tutor.email})

        test_booking.zoom_meeting_id = "123456789"
        db_session.commit()

        response = client.delete(
            "/api/v1/integrations/zoom/meetings/123456789",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestZoomAutoCreateMeetings:
    """Tests for auto-create meetings endpoint."""

    def test_auto_create_requires_admin(self, client, tutor_token):
        """Test that auto-create requires admin access."""
        response = client.post(
            "/api/v1/integrations/zoom/meetings/auto-create",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("modules.integrations.zoom_router.zoom_client")
    def test_auto_create_success(
        self, mock_zoom_client, client, admin_token, test_booking, db_session
    ):
        """Test successful auto-creation of meetings."""
        test_booking.status = "CONFIRMED"
        test_booking.join_url = None
        test_booking.start_time = datetime.now(UTC) + timedelta(hours=12)
        db_session.commit()

        mock_zoom_client.create_meeting = AsyncMock(
            return_value={
                "id": 123456789,
                "join_url": "https://zoom.us/j/123456789",
                "start_url": "https://zoom.us/s/123456789",
                "topic": "Test Meeting",
            }
        )

        response = client.post(
            "/api/v1/integrations/zoom/meetings/auto-create",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"hours_ahead": 24},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "created" in data
        assert "errors" in data

    def test_auto_create_invalid_hours_ahead(self, client, admin_token):
        """Test auto-create with invalid hours_ahead parameter."""
        response = client.post(
            "/api/v1/integrations/zoom/meetings/auto-create",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"hours_ahead": 100},  # Exceeds max of 72
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Zoom Client Retry Logic Tests
# =============================================================================


class TestZoomClientRetryLogic:
    """Tests for Zoom client retry logic."""

    @pytest.fixture
    def zoom_client(self):
        """Create ZoomClient instance."""
        from modules.integrations.zoom_router import ZoomClient

        return ZoomClient()

    @pytest.mark.asyncio
    async def test_create_meeting_retries_on_rate_limit(self, zoom_client):
        """Test that meeting creation retries on rate limit."""
        from modules.integrations.zoom_router import ZoomRateLimitError

        # Mock the attempt method to fail twice then succeed
        call_count = 0

        async def mock_attempt(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ZoomRateLimitError()
            return {
                "id": 123,
                "join_url": "https://zoom.us/j/123",
                "start_url": "https://zoom.us/s/123",
                "topic": "Test",
            }

        with patch.object(zoom_client, "_create_meeting_attempt", side_effect=mock_attempt):
            result = await zoom_client.create_meeting(
                topic="Test",
                start_time=datetime.now(UTC),
                duration_minutes=60,
                max_retries=3,
            )

        assert result["id"] == 123
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_create_meeting_no_retry_on_auth_error(self, zoom_client):
        """Test that meeting creation does not retry on auth error."""
        from modules.integrations.zoom_router import ZoomAuthError

        async def mock_attempt(*args, **kwargs):
            raise ZoomAuthError()

        with patch.object(zoom_client, "_create_meeting_attempt", side_effect=mock_attempt):
            with pytest.raises(ZoomAuthError):
                await zoom_client.create_meeting(
                    topic="Test",
                    start_time=datetime.now(UTC),
                    duration_minutes=60,
                    max_retries=3,
                )

    @pytest.mark.asyncio
    async def test_create_meeting_max_retries_exceeded(self, zoom_client):
        """Test that meeting creation fails after max retries."""
        from modules.integrations.zoom_router import ZoomServiceError

        async def mock_attempt(*args, **kwargs):
            raise ZoomServiceError()

        with patch.object(zoom_client, "_create_meeting_attempt", side_effect=mock_attempt):
            with pytest.raises(ZoomServiceError):
                await zoom_client.create_meeting(
                    topic="Test",
                    start_time=datetime.now(UTC),
                    duration_minutes=60,
                    max_retries=2,
                )


# =============================================================================
# Calendar Schemas Tests
# =============================================================================


class TestCalendarSchemas:
    """Tests for calendar Pydantic schemas."""

    def test_calendar_connection_status_schema(self):
        """Test CalendarConnectionStatus schema."""
        from modules.integrations.calendar_router import CalendarConnectionStatus

        status = CalendarConnectionStatus(
            is_connected=True,
            calendar_email="test@gmail.com",
            connected_at=datetime.now(UTC),
            can_create_events=True,
        )
        assert status.is_connected is True
        assert status.calendar_email == "test@gmail.com"

    def test_calendar_auth_url_response_schema(self):
        """Test CalendarAuthURLResponse schema."""
        from modules.integrations.calendar_router import CalendarAuthURLResponse

        response = CalendarAuthURLResponse(
            authorization_url="https://accounts.google.com/oauth",
            state="test_state",
        )
        assert "google.com" in response.authorization_url
        assert response.state == "test_state"

    def test_calendar_event_response_schema(self):
        """Test CalendarEventResponse schema."""
        from modules.integrations.calendar_router import CalendarEventResponse

        response = CalendarEventResponse(
            event_id="event123",
            html_link="https://calendar.google.com/event/123",
            message="Event created",
        )
        assert response.event_id == "event123"


# =============================================================================
# Zoom Schemas Tests
# =============================================================================


class TestZoomSchemas:
    """Tests for Zoom Pydantic schemas."""

    def test_zoom_connection_status_schema(self):
        """Test ZoomConnectionStatus schema."""
        from modules.integrations.zoom_router import ZoomConnectionStatus

        status = ZoomConnectionStatus(
            is_connected=True,
            zoom_email="test@zoom.us",
            connected_at=datetime.now(UTC),
        )
        assert status.is_connected is True

    def test_zoom_meeting_response_schema(self):
        """Test ZoomMeetingResponse schema."""
        from modules.integrations.zoom_router import ZoomMeetingResponse

        response = ZoomMeetingResponse(
            meeting_id=123456789,
            join_url="https://zoom.us/j/123456789",
            start_url="https://zoom.us/s/123456789",
            password="test123",
            topic="Test Meeting",
        )
        assert response.meeting_id == 123456789
        assert response.password == "test123"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegrationsModule:
    """Integration tests for the integrations module."""

    def test_calendar_and_zoom_coexist(
        self, client, tutor_token, tutor_user, db_session
    ):
        """Test that both calendar and zoom endpoints work together."""
        # Check calendar status
        cal_response = client.get(
            "/api/v1/integrations/calendar/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert cal_response.status_code == status.HTTP_200_OK

        # Check zoom status
        zoom_response = client.get(
            "/api/v1/integrations/zoom/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert zoom_response.status_code == status.HTTP_200_OK

    def test_different_roles_different_access(
        self, client, student_token, tutor_token, admin_token
    ):
        """Test that different roles have appropriate access."""
        # Students can check integration status
        response = client.get(
            "/api/v1/integrations/calendar/status",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Tutors can check integration status
        response = client.get(
            "/api/v1/integrations/zoom/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Only tutors can create meetings (students get 403)
        response = client.post(
            "/api/v1/integrations/zoom/meetings/create",
            headers={"Authorization": f"Bearer {student_token}"},
            params={"booking_id": 1},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
