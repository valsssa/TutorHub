"""
Tests for Video Meeting Service

Tests the multi-provider video meeting creation functionality.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.integrations.video_meeting_service import (
    VideoMeetingService,
    VideoProvider,
    create_meeting_for_booking,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def mock_booking():
    """Create a mock booking."""
    booking = MagicMock()
    booking.id = 123
    booking.subject_name = "Math"
    booking.student_name = "John Student"
    booking.tutor_name = "Jane Tutor"
    booking.start_time = datetime.now(UTC) + timedelta(hours=1)
    booking.end_time = datetime.now(UTC) + timedelta(hours=2)
    booking.tutor_tz = "America/New_York"
    booking.student = MagicMock()
    booking.student.email = "student@example.com"
    return booking


@pytest.fixture
def mock_tutor_profile():
    """Create a mock tutor profile."""
    profile = MagicMock()
    profile.id = 456
    profile.preferred_video_provider = "zoom"
    profile.custom_meeting_url_template = None
    profile.user = MagicMock()
    profile.user.email = "tutor@example.com"
    profile.user.google_calendar_refresh_token = None
    return profile


class TestVideoMeetingService:
    """Test VideoMeetingService methods."""

    @pytest.mark.asyncio
    async def test_create_zoom_meeting_success(self, mock_db, mock_booking, mock_tutor_profile):
        """Test successful Zoom meeting creation."""
        mock_tutor_profile.preferred_video_provider = "zoom"

        with patch("modules.integrations.video_meeting_service.zoom_client") as mock_zoom:
            mock_zoom.create_meeting = AsyncMock(return_value={
                "join_url": "https://zoom.us/j/123456",
                "start_url": "https://zoom.us/s/123456",
                "id": 123456,
            })

            service = VideoMeetingService(mock_db)
            result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

            assert result.success is True
            assert result.join_url == "https://zoom.us/j/123456"
            assert result.host_url == "https://zoom.us/s/123456"
            assert result.meeting_id == "123456"
            assert result.provider == "zoom"

    @pytest.mark.asyncio
    async def test_create_zoom_meeting_failure_retryable(self, mock_db, mock_booking, mock_tutor_profile):
        """Test Zoom meeting creation failure with retryable error."""
        mock_tutor_profile.preferred_video_provider = "zoom"

        with patch("modules.integrations.video_meeting_service.zoom_client") as mock_zoom:
            from modules.integrations.zoom_router import ZoomRateLimitError
            mock_zoom.create_meeting = AsyncMock(side_effect=ZoomRateLimitError())

            service = VideoMeetingService(mock_db)
            result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

            assert result.success is False
            assert result.needs_retry is True
            assert result.provider == "zoom"

    @pytest.mark.asyncio
    async def test_create_teams_meeting_with_template(self, mock_db, mock_booking, mock_tutor_profile):
        """Test Teams meeting creation with URL template."""
        mock_tutor_profile.preferred_video_provider = "teams"
        mock_tutor_profile.custom_meeting_url_template = "https://teams.microsoft.com/l/meetup-join/my-room"

        service = VideoMeetingService(mock_db)
        result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

        assert result.success is True
        assert result.join_url == "https://teams.microsoft.com/l/meetup-join/my-room"
        assert result.provider == "teams"

    @pytest.mark.asyncio
    async def test_create_teams_meeting_without_template(self, mock_db, mock_booking, mock_tutor_profile):
        """Test Teams meeting creation fails without URL template."""
        mock_tutor_profile.preferred_video_provider = "teams"
        mock_tutor_profile.custom_meeting_url_template = None

        service = VideoMeetingService(mock_db)
        result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

        assert result.success is False
        assert "No Microsoft Teams meeting URL configured" in result.error_message
        assert result.provider == "teams"

    @pytest.mark.asyncio
    async def test_create_custom_meeting_with_placeholders(self, mock_db, mock_booking, mock_tutor_profile):
        """Test custom meeting URL with placeholder substitution."""
        mock_tutor_profile.preferred_video_provider = "custom"
        mock_tutor_profile.custom_meeting_url_template = "https://meet.jit.si/edustream-{booking_id}"

        service = VideoMeetingService(mock_db)
        result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

        assert result.success is True
        assert result.join_url == "https://meet.jit.si/edustream-123"
        assert result.provider == "custom"

    @pytest.mark.asyncio
    async def test_create_google_meet_without_calendar(self, mock_db, mock_booking, mock_tutor_profile):
        """Test Google Meet creation fails without calendar connection."""
        mock_tutor_profile.preferred_video_provider = "google_meet"
        mock_tutor_profile.user.google_calendar_refresh_token = None

        service = VideoMeetingService(mock_db)
        result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

        assert result.success is False
        assert "Google Calendar not connected" in result.error_message
        assert result.provider == "google_meet"

    @pytest.mark.asyncio
    async def test_manual_provider_returns_no_url(self, mock_db, mock_booking, mock_tutor_profile):
        """Test manual provider returns success but no URL."""
        mock_tutor_profile.preferred_video_provider = "manual"

        service = VideoMeetingService(mock_db)
        result = await service.create_meeting_for_booking(mock_booking, mock_tutor_profile)

        assert result.success is True
        assert result.join_url is None
        assert result.provider == "manual"

    def test_is_valid_url(self, mock_db):
        """Test URL validation."""
        service = VideoMeetingService(mock_db)

        assert service._is_valid_url("https://example.com") is True
        assert service._is_valid_url("http://localhost:8000") is True
        assert service._is_valid_url("https://zoom.us/j/123") is True
        assert service._is_valid_url("not-a-url") is False
        assert service._is_valid_url("ftp://example.com") is False

    def test_is_valid_teams_url(self, mock_db):
        """Test Teams URL validation."""
        service = VideoMeetingService(mock_db)

        assert service._is_valid_teams_url("https://teams.microsoft.com/l/meetup-join/123") is True
        assert service._is_valid_teams_url("https://teams.live.com/meet/123") is True
        assert service._is_valid_teams_url("https://zoom.us/j/123") is False
        assert service._is_valid_teams_url("https://example.com") is False

    def test_process_url_template(self, mock_db, mock_booking):
        """Test URL template processing."""
        service = VideoMeetingService(mock_db)

        template = "https://meet.example.com/{booking_id}/{date}/{time}"
        result = service._process_url_template(template, mock_booking)

        assert "{booking_id}" not in result
        assert "{date}" not in result
        assert "{time}" not in result
        assert "123" in result  # booking_id

    def test_get_effective_provider_defaults_to_zoom(self, mock_db, mock_tutor_profile):
        """Test that effective provider defaults to zoom."""
        mock_tutor_profile.preferred_video_provider = None

        service = VideoMeetingService(mock_db)
        provider = service._get_effective_provider(mock_tutor_profile)

        assert provider == VideoProvider.ZOOM

    def test_get_effective_provider_respects_preference(self, mock_db, mock_tutor_profile):
        """Test that effective provider respects tutor preference."""
        mock_tutor_profile.preferred_video_provider = "google_meet"

        service = VideoMeetingService(mock_db)
        provider = service._get_effective_provider(mock_tutor_profile)

        assert provider == VideoProvider.GOOGLE_MEET


class TestConvenienceFunction:
    """Test the convenience function."""

    @pytest.mark.asyncio
    async def test_create_meeting_for_booking_convenience(self, mock_db, mock_booking, mock_tutor_profile):
        """Test convenience function creates service and calls method."""
        mock_tutor_profile.preferred_video_provider = "manual"

        result = await create_meeting_for_booking(mock_db, mock_booking, mock_tutor_profile)

        assert result.success is True
        assert result.provider == "manual"
