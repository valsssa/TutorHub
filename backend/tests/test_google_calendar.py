"""
Comprehensive tests for the Google Calendar integration service.

Tests cover:
- OAuth URL generation
- Token exchange and refresh
- Calendar event creation, update, and deletion
- Busy time checking (freebusy API)
- Event listing
- Error handling and edge cases
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from core.google_calendar import (
    CALENDAR_SCOPES,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GoogleCalendarService,
    google_calendar,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def calendar_service() -> GoogleCalendarService:
    """Fresh GoogleCalendarService instance for each test."""
    return GoogleCalendarService()


@pytest.fixture
def mock_settings():
    """Mock settings with Google OAuth configured."""
    with patch("core.google_calendar.settings") as mock:
        mock.GOOGLE_CLIENT_ID = "test-client-id"
        mock.GOOGLE_CLIENT_SECRET = "test-client-secret"
        mock.GOOGLE_CALENDAR_REDIRECT_URI = "https://example.com/callback"
        mock.FRONTEND_URL = "https://example.com"
        yield mock


@pytest.fixture
def mock_credentials():
    """Mock Google credentials object."""
    with patch("core.google_calendar.Credentials") as mock_creds:
        mock_instance = MagicMock()
        mock_creds.return_value = mock_instance
        yield mock_creds


@pytest.fixture
def mock_calendar_build():
    """Mock Google Calendar API build function."""
    with patch("core.google_calendar.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


# =============================================================================
# Test OAuth URL Generation
# =============================================================================


class TestGetAuthorizationUrl:
    """Tests for OAuth authorization URL generation."""

    def test_generate_authorization_url_success(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test generating authorization URL with valid settings."""
        state = "test-csrf-state"
        url = calendar_service.get_authorization_url(state)

        assert GOOGLE_AUTH_URL in url
        assert "client_id=test-client-id" in url
        assert "state=test-csrf-state" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url

    def test_generate_authorization_url_with_custom_redirect(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test generating authorization URL with custom redirect URI."""
        state = "test-state"
        custom_redirect = "https://custom.example.com/oauth/callback"
        url = calendar_service.get_authorization_url(state, redirect_uri=custom_redirect)

        assert f"redirect_uri={custom_redirect}" in url

    def test_generate_authorization_url_includes_scopes(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test that authorization URL includes required scopes."""
        url = calendar_service.get_authorization_url("state")

        for scope in CALENDAR_SCOPES:
            # Scopes are space-separated and URL-encoded
            assert scope.replace(":", "%3A").replace("/", "%2F") in url or scope in url

    def test_generate_authorization_url_no_client_id_raises(
        self, calendar_service: GoogleCalendarService
    ):
        """Test that missing client ID raises ValueError."""
        with patch("core.google_calendar.settings") as mock:
            mock.GOOGLE_CLIENT_ID = None

            with pytest.raises(ValueError, match="Google OAuth not configured"):
                calendar_service.get_authorization_url("state")

    def test_generate_authorization_url_empty_client_id_raises(
        self, calendar_service: GoogleCalendarService
    ):
        """Test that empty client ID raises ValueError."""
        with patch("core.google_calendar.settings") as mock:
            mock.GOOGLE_CLIENT_ID = ""

            with pytest.raises(ValueError, match="Google OAuth not configured"):
                calendar_service.get_authorization_url("state")


# =============================================================================
# Test Token Exchange
# =============================================================================


class TestExchangeCodeForTokens:
    """Tests for authorization code exchange."""

    @pytest.mark.asyncio
    async def test_exchange_code_success(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test successful token exchange."""
        expected_tokens = {
            "access_token": "ya29.test-access-token",
            "refresh_token": "1//test-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_tokens
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await calendar_service.exchange_code_for_tokens("auth-code-123")

            assert result == expected_tokens
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == GOOGLE_TOKEN_URL
            assert call_args[1]["data"]["code"] == "auth-code-123"
            assert call_args[1]["data"]["grant_type"] == "authorization_code"

    @pytest.mark.asyncio
    async def test_exchange_code_with_custom_redirect(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test token exchange with custom redirect URI."""
        custom_redirect = "https://custom.example.com/callback"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "test"}
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await calendar_service.exchange_code_for_tokens(
                "auth-code", redirect_uri=custom_redirect
            )

            call_args = mock_client.post.call_args
            assert call_args[1]["data"]["redirect_uri"] == custom_redirect

    @pytest.mark.asyncio
    async def test_exchange_code_failure(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test token exchange failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid code"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="Failed to exchange authorization code"):
                await calendar_service.exchange_code_for_tokens("invalid-code")

    @pytest.mark.asyncio
    async def test_exchange_code_no_credentials_raises(
        self, calendar_service: GoogleCalendarService
    ):
        """Test that missing credentials raises ValueError."""
        with patch("core.google_calendar.settings") as mock:
            mock.GOOGLE_CLIENT_ID = None
            mock.GOOGLE_CLIENT_SECRET = None

            with pytest.raises(ValueError, match="Google OAuth not configured"):
                await calendar_service.exchange_code_for_tokens("code")

    @pytest.mark.asyncio
    async def test_exchange_code_missing_secret_raises(
        self, calendar_service: GoogleCalendarService
    ):
        """Test that missing client secret raises ValueError."""
        with patch("core.google_calendar.settings") as mock:
            mock.GOOGLE_CLIENT_ID = "test-id"
            mock.GOOGLE_CLIENT_SECRET = None

            with pytest.raises(ValueError, match="Google OAuth not configured"):
                await calendar_service.exchange_code_for_tokens("code")


# =============================================================================
# Test Token Refresh
# =============================================================================


class TestRefreshAccessToken:
    """Tests for access token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test successful token refresh."""
        expected_tokens = {
            "access_token": "ya29.new-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_tokens
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await calendar_service.refresh_access_token("1//refresh-token")

            assert result == expected_tokens
            call_args = mock_client.post.call_args
            assert call_args[1]["data"]["grant_type"] == "refresh_token"
            assert call_args[1]["data"]["refresh_token"] == "1//refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_token_failure(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test token refresh failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Token revoked"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="Failed to refresh token"):
                await calendar_service.refresh_access_token("invalid-refresh-token")

    @pytest.mark.asyncio
    async def test_refresh_token_no_credentials_raises(
        self, calendar_service: GoogleCalendarService
    ):
        """Test that missing credentials raises ValueError."""
        with patch("core.google_calendar.settings") as mock:
            mock.GOOGLE_CLIENT_ID = None
            mock.GOOGLE_CLIENT_SECRET = None

            with pytest.raises(ValueError, match="Google OAuth not configured"):
                await calendar_service.refresh_access_token("refresh-token")


# =============================================================================
# Test Calendar Event Creation
# =============================================================================


class TestCreateBookingEvent:
    """Tests for calendar event creation."""

    @pytest.mark.asyncio
    async def test_create_booking_event_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful event creation."""
        mock_build, mock_service = mock_calendar_build

        # Mock the events().insert().execute() chain
        mock_execute = MagicMock()
        mock_execute.return_value = {
            "id": "event-123",
            "htmlLink": "https://calendar.google.com/event/123",
            "iCalUID": "ical-uid-123@google.com",
        }
        mock_insert = MagicMock()
        mock_insert.execute = mock_execute
        mock_events = MagicMock()
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events

        start_time = datetime.now(UTC) + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        result = await calendar_service.create_booking_event(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            booking_id=123,
            title="Math Tutoring Session",
            description="Calculus review",
            start_time=start_time,
            end_time=end_time,
            tutor_email="tutor@example.com",
            student_email="student@example.com",
            tutor_name="John Tutor",
            student_name="Jane Student",
            meeting_url="https://zoom.us/j/123456",
            timezone="America/New_York",
        )

        assert result is not None
        assert result["event_id"] == "event-123"
        assert result["html_link"] == "https://calendar.google.com/event/123"
        assert result["ical_uid"] == "ical-uid-123@google.com"

    @pytest.mark.asyncio
    async def test_create_booking_event_without_meeting_url(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test event creation without meeting URL."""
        mock_build, mock_service = mock_calendar_build

        mock_execute = MagicMock()
        mock_execute.return_value = {"id": "event-456", "htmlLink": None, "iCalUID": None}
        mock_insert = MagicMock()
        mock_insert.execute = mock_execute
        mock_events = MagicMock()
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events

        start_time = datetime.now(UTC) + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        result = await calendar_service.create_booking_event(
            access_token="test-token",
            refresh_token=None,
            booking_id=456,
            title="Physics Session",
            description="Quantum mechanics",
            start_time=start_time,
            end_time=end_time,
            tutor_email="tutor@example.com",
            student_email="student@example.com",
            tutor_name="Dr. Physics",
            student_name="Student Name",
            meeting_url=None,
        )

        assert result is not None
        assert result["event_id"] == "event-456"

    @pytest.mark.asyncio
    async def test_create_booking_event_http_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test event creation handles HTTP error gracefully."""
        mock_build, mock_service = mock_calendar_build

        # Mock HttpError
        mock_resp = MagicMock()
        mock_resp.status = 403
        mock_resp.reason = "Forbidden"
        http_error = HttpError(mock_resp, b"Calendar access denied")

        mock_events = MagicMock()
        mock_events.insert.return_value.execute.side_effect = http_error
        mock_service.events.return_value = mock_events

        start_time = datetime.now(UTC) + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        result = await calendar_service.create_booking_event(
            access_token="test-token",
            refresh_token=None,
            booking_id=789,
            title="Test",
            description="Test",
            start_time=start_time,
            end_time=end_time,
            tutor_email="tutor@example.com",
            student_email="student@example.com",
            tutor_name="Tutor",
            student_name="Student",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_booking_event_generic_exception(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test event creation handles generic exception gracefully."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.insert.return_value.execute.side_effect = Exception("Network error")
        mock_service.events.return_value = mock_events

        start_time = datetime.now(UTC) + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        result = await calendar_service.create_booking_event(
            access_token="test-token",
            refresh_token=None,
            booking_id=999,
            title="Test",
            description="Test",
            start_time=start_time,
            end_time=end_time,
            tutor_email="tutor@example.com",
            student_email="student@example.com",
            tutor_name="Tutor",
            student_name="Student",
        )

        assert result is None


# =============================================================================
# Test Calendar Event Update
# =============================================================================


class TestUpdateBookingEvent:
    """Tests for calendar event update."""

    @pytest.mark.asyncio
    async def test_update_event_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful event update."""
        mock_build, mock_service = mock_calendar_build

        # Mock get and update chain
        existing_event = {
            "id": "event-123",
            "summary": "Original Title",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
        }

        mock_events = MagicMock()
        mock_events.get.return_value.execute.return_value = existing_event
        mock_events.update.return_value.execute.return_value = None
        mock_service.events.return_value = mock_events

        new_start = datetime.now(UTC) + timedelta(days=2)
        new_end = new_start + timedelta(hours=2)

        result = await calendar_service.update_booking_event(
            access_token="test-token",
            refresh_token="test-refresh",
            event_id="event-123",
            start_time=new_start,
            end_time=new_end,
            title="Updated Title",
            description="Updated description",
            meeting_url="https://zoom.us/new-meeting",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_event_partial_update(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test updating only some fields."""
        mock_build, mock_service = mock_calendar_build

        existing_event = {
            "id": "event-123",
            "summary": "Original Title",
            "description": "Original description",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
        }

        mock_events = MagicMock()
        mock_events.get.return_value.execute.return_value = existing_event
        mock_events.update.return_value.execute.return_value = None
        mock_service.events.return_value = mock_events

        result = await calendar_service.update_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="event-123",
            title="Only Title Updated",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_event_failure(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test event update handles failure gracefully."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.get.return_value.execute.side_effect = Exception("Event not found")
        mock_service.events.return_value = mock_events

        result = await calendar_service.update_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="nonexistent-event",
            title="New Title",
        )

        assert result is False


# =============================================================================
# Test Calendar Event Deletion
# =============================================================================


class TestDeleteBookingEvent:
    """Tests for calendar event deletion."""

    @pytest.mark.asyncio
    async def test_delete_event_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful event deletion."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.delete.return_value.execute.return_value = None
        mock_service.events.return_value = mock_events

        result = await calendar_service.delete_booking_event(
            access_token="test-token",
            refresh_token="test-refresh",
            event_id="event-to-delete",
            send_updates=True,
        )

        assert result is True
        mock_events.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_event_without_updates(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test event deletion without sending updates."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.delete.return_value.execute.return_value = None
        mock_service.events.return_value = mock_events

        result = await calendar_service.delete_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="event-id",
            send_updates=False,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_event_not_found_returns_true(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test deleting already-deleted event returns True (idempotent)."""
        mock_build, mock_service = mock_calendar_build

        # Mock 404 HttpError
        mock_resp = MagicMock()
        mock_resp.status = 404
        http_error = HttpError(mock_resp, b"Not Found")

        mock_events = MagicMock()
        mock_events.delete.return_value.execute.side_effect = http_error
        mock_service.events.return_value = mock_events

        result = await calendar_service.delete_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="already-deleted",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_event_http_error_returns_false(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test delete event handles non-404 HTTP error."""
        mock_build, mock_service = mock_calendar_build

        mock_resp = MagicMock()
        mock_resp.status = 403
        http_error = HttpError(mock_resp, b"Forbidden")

        mock_events = MagicMock()
        mock_events.delete.return_value.execute.side_effect = http_error
        mock_service.events.return_value = mock_events

        result = await calendar_service.delete_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="forbidden-event",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_event_generic_exception(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test delete event handles generic exception."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.delete.return_value.execute.side_effect = Exception("Network error")
        mock_service.events.return_value = mock_events

        result = await calendar_service.delete_booking_event(
            access_token="test-token",
            refresh_token=None,
            event_id="event-id",
        )

        assert result is False


# =============================================================================
# Test Get User Calendars
# =============================================================================


class TestGetUserCalendars:
    """Tests for getting user's calendar list."""

    @pytest.mark.asyncio
    async def test_get_calendars_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful calendar list retrieval."""
        mock_build, mock_service = mock_calendar_build

        calendar_list = {
            "items": [
                {"id": "primary", "summary": "Primary Calendar"},
                {"id": "work@example.com", "summary": "Work Calendar"},
            ]
        }

        mock_calendar_list = MagicMock()
        mock_calendar_list.list.return_value.execute.return_value = calendar_list
        mock_service.calendarList.return_value = mock_calendar_list

        result = await calendar_service.get_user_calendars(
            access_token="test-token", refresh_token="test-refresh"
        )

        assert len(result) == 2
        assert result[0]["id"] == "primary"
        assert result[1]["summary"] == "Work Calendar"

    @pytest.mark.asyncio
    async def test_get_calendars_empty(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test getting empty calendar list."""
        mock_build, mock_service = mock_calendar_build

        mock_calendar_list = MagicMock()
        mock_calendar_list.list.return_value.execute.return_value = {"items": []}
        mock_service.calendarList.return_value = mock_calendar_list

        result = await calendar_service.get_user_calendars(access_token="test-token")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_calendars_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test getting calendars handles error gracefully."""
        mock_build, mock_service = mock_calendar_build

        mock_calendar_list = MagicMock()
        mock_calendar_list.list.return_value.execute.side_effect = Exception("API Error")
        mock_service.calendarList.return_value = mock_calendar_list

        result = await calendar_service.get_user_calendars(access_token="test-token")

        assert result == []


# =============================================================================
# Test Check Busy Times (Freebusy API)
# =============================================================================


class TestCheckBusyTimes:
    """Tests for checking calendar busy times."""

    @pytest.mark.asyncio
    async def test_check_busy_times_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful busy time check."""
        mock_build, mock_service = mock_calendar_build

        freebusy_response = {
            "calendars": {
                "primary": {
                    "busy": [
                        {
                            "start": "2024-01-15T09:00:00Z",
                            "end": "2024-01-15T10:00:00Z",
                        },
                        {
                            "start": "2024-01-15T14:00:00Z",
                            "end": "2024-01-15T15:00:00Z",
                        },
                    ]
                }
            }
        }

        mock_freebusy = MagicMock()
        mock_freebusy.query.return_value.execute.return_value = freebusy_response
        mock_service.freebusy.return_value = mock_freebusy

        start = datetime.now(UTC)
        end = start + timedelta(days=1)

        result = await calendar_service.check_busy_times(
            access_token="test-token",
            refresh_token="test-refresh",
            start_time=start,
            end_time=end,
        )

        assert len(result) == 2
        assert result[0]["start"] == "2024-01-15T09:00:00Z"

    @pytest.mark.asyncio
    async def test_check_busy_times_no_conflicts(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test busy time check with no conflicts."""
        mock_build, mock_service = mock_calendar_build

        freebusy_response = {"calendars": {"primary": {"busy": []}}}

        mock_freebusy = MagicMock()
        mock_freebusy.query.return_value.execute.return_value = freebusy_response
        mock_service.freebusy.return_value = mock_freebusy

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.check_busy_times(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_check_busy_times_custom_calendar(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test busy time check for specific calendar."""
        mock_build, mock_service = mock_calendar_build

        custom_calendar_id = "work@example.com"
        freebusy_response = {
            "calendars": {
                custom_calendar_id: {
                    "busy": [{"start": "2024-01-15T11:00:00Z", "end": "2024-01-15T12:00:00Z"}]
                }
            }
        }

        mock_freebusy = MagicMock()
        mock_freebusy.query.return_value.execute.return_value = freebusy_response
        mock_service.freebusy.return_value = mock_freebusy

        start = datetime.now(UTC)
        end = start + timedelta(days=1)

        result = await calendar_service.check_busy_times(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
            calendar_id=custom_calendar_id,
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_check_busy_times_http_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test busy time check handles HTTP error."""
        mock_build, mock_service = mock_calendar_build

        mock_resp = MagicMock()
        mock_resp.status = 403
        http_error = HttpError(mock_resp, b"Forbidden")

        mock_freebusy = MagicMock()
        mock_freebusy.query.return_value.execute.side_effect = http_error
        mock_service.freebusy.return_value = mock_freebusy

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.check_busy_times(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_check_busy_times_generic_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test busy time check handles generic error."""
        mock_build, mock_service = mock_calendar_build

        mock_freebusy = MagicMock()
        mock_freebusy.query.return_value.execute.side_effect = Exception("Network error")
        mock_service.freebusy.return_value = mock_freebusy

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.check_busy_times(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []


# =============================================================================
# Test Get Events in Range
# =============================================================================


class TestGetEventsInRange:
    """Tests for getting calendar events in a time range."""

    @pytest.mark.asyncio
    async def test_get_events_success(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test successful event retrieval."""
        mock_build, mock_service = mock_calendar_build

        events_response = {
            "items": [
                {
                    "id": "event-1",
                    "summary": "Meeting 1",
                    "start": {"dateTime": "2024-01-15T09:00:00Z"},
                    "end": {"dateTime": "2024-01-15T10:00:00Z"},
                },
                {
                    "id": "event-2",
                    "summary": "Meeting 2",
                    "start": {"dateTime": "2024-01-15T14:00:00Z"},
                    "end": {"dateTime": "2024-01-15T15:00:00Z"},
                },
            ]
        }

        mock_events = MagicMock()
        mock_events.list.return_value.execute.return_value = events_response
        mock_service.events.return_value = mock_events

        start = datetime.now(UTC)
        end = start + timedelta(days=1)

        result = await calendar_service.get_events_in_range(
            access_token="test-token",
            refresh_token="test-refresh",
            start_time=start,
            end_time=end,
        )

        assert len(result) == 2
        assert result[0]["summary"] == "Meeting 1"

    @pytest.mark.asyncio
    async def test_get_events_empty(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test getting events when none exist."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.list.return_value.execute.return_value = {"items": []}
        mock_service.events.return_value = mock_events

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.get_events_in_range(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_events_custom_calendar(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test getting events from specific calendar."""
        mock_build, mock_service = mock_calendar_build

        events_response = {
            "items": [{"id": "work-event-1", "summary": "Work Meeting"}]
        }

        mock_events = MagicMock()
        mock_events.list.return_value.execute.return_value = events_response
        mock_service.events.return_value = mock_events

        start = datetime.now(UTC)
        end = start + timedelta(days=1)

        result = await calendar_service.get_events_in_range(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
            calendar_id="work@example.com",
        )

        assert len(result) == 1
        assert result[0]["summary"] == "Work Meeting"

    @pytest.mark.asyncio
    async def test_get_events_http_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test get events handles HTTP error."""
        mock_build, mock_service = mock_calendar_build

        mock_resp = MagicMock()
        mock_resp.status = 401
        http_error = HttpError(mock_resp, b"Unauthorized")

        mock_events = MagicMock()
        mock_events.list.return_value.execute.side_effect = http_error
        mock_service.events.return_value = mock_events

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.get_events_in_range(
            access_token="invalid-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_events_generic_error(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_credentials,
        mock_calendar_build,
    ):
        """Test get events handles generic error."""
        mock_build, mock_service = mock_calendar_build

        mock_events = MagicMock()
        mock_events.list.return_value.execute.side_effect = Exception("Network error")
        mock_service.events.return_value = mock_events

        start = datetime.now(UTC)
        end = start + timedelta(hours=2)

        result = await calendar_service.get_events_in_range(
            access_token="test-token",
            refresh_token=None,
            start_time=start,
            end_time=end,
        )

        assert result == []


# =============================================================================
# Test Singleton Instance
# =============================================================================


class TestSingletonInstance:
    """Tests for the singleton google_calendar instance."""

    def test_singleton_instance_exists(self):
        """Test that singleton instance is available."""
        assert google_calendar is not None
        assert isinstance(google_calendar, GoogleCalendarService)

    def test_singleton_credentials_cache_initialized(self):
        """Test that credentials cache is initialized."""
        assert hasattr(google_calendar, "_credentials_cache")
        assert isinstance(google_calendar._credentials_cache, dict)


# =============================================================================
# Test Internal Methods
# =============================================================================


class TestInternalMethods:
    """Tests for internal helper methods."""

    def test_get_credentials(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test credentials object creation."""
        with patch("core.google_calendar.Credentials") as mock_creds:
            mock_instance = MagicMock()
            mock_creds.return_value = mock_instance

            calendar_service._get_credentials(
                access_token="test-access-token",
                refresh_token="test-refresh-token",
            )

            mock_creds.assert_called_once()
            call_kwargs = mock_creds.call_args[1]
            assert call_kwargs["token"] == "test-access-token"
            assert call_kwargs["refresh_token"] == "test-refresh-token"

    def test_get_credentials_without_refresh_token(
        self, calendar_service: GoogleCalendarService, mock_settings
    ):
        """Test credentials object creation without refresh token."""
        with patch("core.google_calendar.Credentials") as mock_creds:
            mock_instance = MagicMock()
            mock_creds.return_value = mock_instance

            calendar_service._get_credentials(
                access_token="test-access-token",
                refresh_token=None,
            )

            call_kwargs = mock_creds.call_args[1]
            assert call_kwargs["refresh_token"] is None

    def test_get_calendar_service(
        self,
        calendar_service: GoogleCalendarService,
        mock_settings,
        mock_calendar_build,
    ):
        """Test building Google Calendar service."""
        mock_build, mock_service = mock_calendar_build
        mock_credentials = MagicMock()

        calendar_service._get_calendar_service(mock_credentials)

        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_credentials)
