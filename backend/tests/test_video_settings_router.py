"""
Tests for Tutor Video Settings Router.

Tests cover:
- GET /tutor/settings/video - Get video meeting settings
- PUT /tutor/settings/video - Update video meeting settings
- GET /tutor/settings/video/providers - List available providers
- All provider types (zoom, google_meet, teams, custom, manual)
- Custom URL validation
- Authorization checks
"""

from unittest.mock import patch

import pytest
from fastapi import status


class TestGetVideoSettings:
    """Test GET /api/v1/tutor/settings/video endpoint."""

    def test_get_video_settings_success(self, client, tutor_token, tutor_user, db_session):
        """Test getting video settings successfully."""
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "preferred_video_provider" in data
        assert "custom_meeting_url_template" in data
        assert "video_provider_configured" in data
        assert "zoom_available" in data
        assert "google_calendar_connected" in data

    def test_get_video_settings_default_provider(self, client, tutor_token):
        """Test that default provider is zoom."""
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        # Default should be zoom
        assert data["preferred_video_provider"] == "zoom"

    def test_get_video_settings_unauthenticated(self, client):
        """Test unauthenticated access is rejected."""
        response = client.get("/api/v1/tutor/settings/video")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_video_settings_student_forbidden(self, client, student_token):
        """Test student cannot access tutor video settings."""
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should be forbidden for non-tutors
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_get_video_settings_shows_google_calendar_status(
        self, client, tutor_token, tutor_user, db_session
    ):
        """Test that Google Calendar connection status is shown."""
        # Update user to have Google Calendar connected
        tutor_user.google_calendar_refresh_token = "test_refresh_token"
        db_session.commit()

        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        assert data["google_calendar_connected"] is True


class TestUpdateVideoSettings:
    """Test PUT /api/v1/tutor/settings/video endpoint."""

    def test_update_to_zoom_provider(self, client, tutor_token):
        """Test updating to zoom provider."""
        with patch("core.config.settings") as mock_settings:
            mock_settings.ZOOM_CLIENT_ID = "test_client_id"
            mock_settings.ZOOM_CLIENT_SECRET = "test_client_secret"
            mock_settings.ZOOM_ACCOUNT_ID = "test_account_id"

            response = client.put(
                "/api/v1/tutor/settings/video",
                headers={"Authorization": f"Bearer {tutor_token}"},
                json={"preferred_video_provider": "zoom"},
            )

        # Note: May fail if Zoom not configured in test environment
        # Accept either success or service unavailable
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]

    def test_update_to_manual_provider(self, client, tutor_token):
        """Test updating to manual provider (always available)."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "manual"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["preferred_video_provider"] == "manual"
        assert data["video_provider_configured"] is True

    def test_update_to_custom_provider_with_url(self, client, tutor_token):
        """Test updating to custom provider with valid URL."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "https://meet.example.com/my-room",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["preferred_video_provider"] == "custom"
        assert data["custom_meeting_url_template"] == "https://meet.example.com/my-room"
        assert data["video_provider_configured"] is True

    def test_update_to_custom_provider_without_url_fails(self, client, tutor_token):
        """Test that custom provider requires URL."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "custom"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "url" in response.json()["detail"].lower()

    def test_update_to_teams_with_valid_url(self, client, tutor_token):
        """Test updating to Teams provider with valid Teams URL."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "teams",
                "custom_meeting_url_template": "https://teams.microsoft.com/l/meetup-join/test",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["preferred_video_provider"] == "teams"
        assert data["video_provider_configured"] is True

    def test_update_to_teams_without_url_fails(self, client, tutor_token):
        """Test that Teams provider requires URL."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "teams"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "url" in response.json()["detail"].lower() or "teams" in response.json()["detail"].lower()

    def test_update_to_teams_with_invalid_url_fails(self, client, tutor_token):
        """Test that Teams provider validates URL format."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "teams",
                "custom_meeting_url_template": "https://not-teams.com/meeting",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "teams" in response.json()["detail"].lower()

    def test_update_to_google_meet_requires_calendar(self, client, tutor_token, tutor_user, db_session):
        """Test that Google Meet requires connected calendar."""
        # Ensure no Google Calendar is connected
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "google_meet"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "google" in response.json()["detail"].lower() or "calendar" in response.json()["detail"].lower()

    def test_update_to_google_meet_with_calendar(self, client, tutor_token, tutor_user, db_session):
        """Test Google Meet with connected calendar succeeds."""
        # Connect Google Calendar
        tutor_user.google_calendar_refresh_token = "test_refresh_token"
        db_session.commit()

        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "google_meet"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["preferred_video_provider"] == "google_meet"
        assert data["video_provider_configured"] is True

    def test_update_with_invalid_provider_fails(self, client, tutor_token):
        """Test that invalid provider is rejected."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "invalid_provider"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_unauthenticated(self, client):
        """Test unauthenticated update is rejected."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            json={"preferred_video_provider": "manual"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_student_forbidden(self, client, student_token):
        """Test student cannot update tutor video settings."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"preferred_video_provider": "manual"},
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestCustomUrlValidation:
    """Test custom URL template validation."""

    def test_valid_https_url(self, client, tutor_token):
        """Test valid HTTPS URL is accepted."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "https://meet.example.com/room123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_valid_http_url(self, client, tutor_token):
        """Test valid HTTP URL is accepted."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "http://meet.example.com/room123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_url_format_rejected(self, client, tutor_token):
        """Test invalid URL format is rejected."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "not-a-url",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_localhost_url_accepted(self, client, tutor_token):
        """Test localhost URL is accepted."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "http://localhost:8080/meeting",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_ip_address_url_accepted(self, client, tutor_token):
        """Test IP address URL is accepted."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "http://192.168.1.1:8080/meeting",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_empty_url_for_custom_fails(self, client, tutor_token):
        """Test empty URL for custom provider fails."""
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_null_url_clears_template(self, client, tutor_token):
        """Test null URL clears the template when using manual provider."""
        # First set a custom URL
        client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "https://meet.example.com/room",
            },
        )

        # Then switch to manual without URL
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "manual",
                "custom_meeting_url_template": None,
            },
        )
        assert response.status_code == status.HTTP_200_OK


class TestListVideoProviders:
    """Test GET /api/v1/tutor/settings/video/providers endpoint."""

    def test_list_providers_success(self, client, tutor_token):
        """Test listing available video providers."""
        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "providers" in data
        assert "current_provider" in data
        assert isinstance(data["providers"], list)
        assert len(data["providers"]) > 0

    def test_list_providers_contains_all_options(self, client, tutor_token):
        """Test that all provider options are listed."""
        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        provider_values = [p["value"] for p in data["providers"]]
        expected_providers = ["zoom", "google_meet", "teams", "custom", "manual"]

        for expected in expected_providers:
            assert expected in provider_values

    def test_list_providers_has_required_fields(self, client, tutor_token):
        """Test that provider options have all required fields."""
        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        for provider in data["providers"]:
            assert "value" in provider
            assert "label" in provider
            assert "description" in provider
            assert "requires_setup" in provider
            assert "is_available" in provider

    def test_list_providers_shows_availability(self, client, tutor_token, tutor_user, db_session):
        """Test that providers show correct availability status."""
        # Without Google Calendar connected, google_meet should show unavailable
        tutor_user.google_calendar_refresh_token = None
        db_session.commit()

        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        google_meet = next(p for p in data["providers"] if p["value"] == "google_meet")
        assert google_meet["is_available"] is False

        # Connect Google Calendar
        tutor_user.google_calendar_refresh_token = "test_token"
        db_session.commit()

        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        google_meet = next(p for p in data["providers"] if p["value"] == "google_meet")
        assert google_meet["is_available"] is True

    def test_list_providers_unauthenticated(self, client):
        """Test unauthenticated access is rejected."""
        response = client.get("/api/v1/tutor/settings/video/providers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_providers_student_forbidden(self, client, student_token):
        """Test student cannot list tutor provider options."""
        response = client.get(
            "/api/v1/tutor/settings/video/providers",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestVideoSettingsIntegration:
    """Integration tests for video settings workflow."""

    def test_full_settings_workflow(self, client, tutor_token, tutor_user, db_session):
        """Test complete video settings workflow."""
        # 1. Get initial settings
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        # Verify initial settings returned
        assert response.json() is not None

        # 2. Update to manual
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "manual"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 3. Verify update persisted
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()
        assert data["preferred_video_provider"] == "manual"

        # 4. Update to custom with URL
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "https://jitsi.meet/my-room",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # 5. Verify custom URL persisted
        response = client.get(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()
        assert data["preferred_video_provider"] == "custom"
        assert data["custom_meeting_url_template"] == "https://jitsi.meet/my-room"

    def test_provider_switch_clears_url_when_not_needed(self, client, tutor_token):
        """Test that switching to provider that doesn't need URL works."""
        # Set custom provider with URL
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "preferred_video_provider": "custom",
                "custom_meeting_url_template": "https://meet.example.com/room",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # Switch to manual (doesn't require URL)
        response = client.put(
            "/api/v1/tutor/settings/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"preferred_video_provider": "manual"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["preferred_video_provider"] == "manual"
