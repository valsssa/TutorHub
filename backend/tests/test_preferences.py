"""Tests for user preferences API endpoints."""

from fastapi import status

import pytest


class TestUpdatePreferences:
    """Test PATCH /api/users/preferences endpoint."""

    def test_update_timezone_success(self, client, student_token, student_user, db_session):
        """Test successful timezone update."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "America/New_York"

        # Verify database was updated
        db_session.refresh(student_user)
        assert student_user.timezone == "America/New_York"

    def test_update_timezone_pacific(self, client, student_token, student_user, db_session):
        """Test updating to Pacific timezone."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/Los_Angeles"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "America/Los_Angeles"

    def test_update_timezone_european(self, client, student_token, student_user, db_session):
        """Test updating to European timezone."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Europe/London"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "Europe/London"

    def test_update_timezone_asian(self, client, student_token, student_user, db_session):
        """Test updating to Asian timezone."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Asia/Tokyo"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "Asia/Tokyo"

    def test_update_timezone_utc(self, client, student_token, student_user, db_session):
        """Test updating to UTC timezone."""
        # First change to non-UTC
        client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/New_York"},
        )

        # Then change back to UTC
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "UTC"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "UTC"

    def test_update_timezone_invalid_returns_422(self, client, student_token):
        """Test invalid timezone returns 422 Unprocessable Entity."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Invalid/Timezone"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid IANA timezone" in response.text

    def test_update_timezone_abbreviation_invalid(self, client, student_token):
        """Test timezone abbreviation (EST, PST) is not valid IANA."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "EST"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_timezone_offset_invalid(self, client, student_token):
        """Test timezone offset format (GMT+5) is not valid IANA."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "GMT+5"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_timezone_empty_string(self, client, student_token, student_user, db_session):
        """Test empty timezone string doesn't change value."""
        original_tz = student_user.timezone

        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": ""},
        )

        # Empty string should be treated as None, which is a no-op
        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        assert student_user.timezone == original_tz

    def test_update_timezone_null(self, client, student_token, student_user, db_session):
        """Test null timezone doesn't change value."""
        original_tz = student_user.timezone

        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": None},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        assert student_user.timezone == original_tz

    def test_update_timezone_no_auth(self, client):
        """Test update without authentication returns 401."""
        response = client.patch(
            "/api/users/preferences",
            json={"timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_timezone_invalid_token(self, client):
        """Test update with invalid token returns 401."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": "Bearer invalid_token"},
            json={"timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_timezone_tutor_can_update(self, client, tutor_token, tutor_user, db_session):
        """Test tutor role can update preferences."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"timezone": "Europe/Paris"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "Europe/Paris"

    def test_update_timezone_admin_can_update(self, client, admin_token, admin_user, db_session):
        """Test admin role can update preferences."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"timezone": "Asia/Singapore"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "Asia/Singapore"

    def test_update_timezone_updates_timestamp(self, client, student_token, student_user, db_session):
        """Test updating timezone updates the updated_at timestamp."""
        original_updated_at = student_user.updated_at

        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Australia/Sydney"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        assert student_user.updated_at > original_updated_at

    def test_update_timezone_case_sensitive(self, client, student_token):
        """Test timezone validation is case sensitive."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "america/new_york"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_timezone_etc_format(self, client, student_token, student_user, db_session):
        """Test Etc/ timezone format is accepted."""
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Etc/UTC"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "Etc/UTC"


class TestSyncTimezone:
    """Test POST /api/users/preferences/sync-timezone endpoint."""

    def test_sync_timezone_same_returns_no_update(self, client, student_token, student_user):
        """Test syncing same timezone returns needs_update=false."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "UTC"},  # Same as user's default
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["needs_update"] is False
        assert data["saved_timezone"] == "UTC"
        assert data["detected_timezone"] == "UTC"

    def test_sync_timezone_different_returns_update_needed(
        self, client, student_token, student_user
    ):
        """Test syncing different timezone returns needs_update=true."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["needs_update"] is True
        assert data["saved_timezone"] == "UTC"
        assert data["detected_timezone"] == "America/New_York"

    def test_sync_timezone_after_update(self, client, student_token, student_user, db_session):
        """Test sync after updating timezone shows no update needed."""
        # First update timezone
        client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/New_York"},
        )

        # Then sync with same timezone
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["needs_update"] is False
        assert data["saved_timezone"] == "America/New_York"
        assert data["detected_timezone"] == "America/New_York"

    def test_sync_timezone_invalid_returns_422(self, client, student_token):
        """Test syncing invalid timezone returns 422."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Invalid/Timezone"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sync_timezone_abbreviation_invalid(self, client, student_token):
        """Test syncing timezone abbreviation returns 422."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "PST"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sync_timezone_no_auth(self, client):
        """Test sync without authentication returns 401."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            json={"detected_timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sync_timezone_missing_field(self, client, student_token):
        """Test sync without detected_timezone field returns 422."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sync_timezone_empty_string(self, client, student_token):
        """Test sync with empty string returns 422."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sync_timezone_tutor(self, client, tutor_token, tutor_user):
        """Test tutor can sync timezone."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"detected_timezone": "Europe/London"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detected_timezone"] == "Europe/London"

    def test_sync_timezone_admin(self, client, admin_token, admin_user):
        """Test admin can sync timezone."""
        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"detected_timezone": "Asia/Tokyo"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detected_timezone"] == "Asia/Tokyo"

    def test_sync_timezone_does_not_modify_database(
        self, client, student_token, student_user, db_session
    ):
        """Test sync endpoint is read-only and doesn't modify timezone."""
        original_tz = student_user.timezone

        response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "America/Los_Angeles"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        # Timezone should NOT have changed
        assert student_user.timezone == original_tz

    def test_sync_timezone_various_valid_timezones(self, client, student_token):
        """Test sync with various valid IANA timezones."""
        valid_timezones = [
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "America/Denver",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Singapore",
            "Australia/Sydney",
            "Pacific/Auckland",
            "UTC",
            "Etc/UTC",
        ]

        for tz in valid_timezones:
            response = client.post(
                "/api/users/preferences/sync-timezone",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"detected_timezone": tz},
            )
            assert (
                response.status_code == status.HTTP_200_OK
            ), f"Timezone {tz} should be valid"


class TestPreferencesIntegration:
    """Integration tests for preferences workflow."""

    def test_full_timezone_update_workflow(self, client, student_token, student_user, db_session):
        """Test complete workflow: sync -> detect difference -> update."""
        # 1. Check initial state - sync detects different timezone
        sync_response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "America/New_York"},
        )
        assert sync_response.status_code == status.HTTP_200_OK
        assert sync_response.json()["needs_update"] is True

        # 2. Update the timezone
        update_response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/New_York"},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["timezone"] == "America/New_York"

        # 3. Sync again - should show no update needed
        sync_response2 = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "America/New_York"},
        )
        assert sync_response2.status_code == status.HTTP_200_OK
        assert sync_response2.json()["needs_update"] is False

    def test_timezone_persists_across_sessions(self, client, student_user, db_session):
        """Test timezone persists after logout/login."""
        # Login and update timezone
        login_response = client.post(
            "/api/auth/login",
            data={"username": student_user.email, "password": "student123"},
        )
        token1 = login_response.json()["access_token"]

        client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {token1}"},
            json={"timezone": "Europe/Paris"},
        )

        # Login again (simulating new session)
        login_response2 = client.post(
            "/api/auth/login",
            data={"username": student_user.email, "password": "student123"},
        )
        token2 = login_response2.json()["access_token"]

        # Check timezone via /me endpoint
        me_response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["timezone"] == "Europe/Paris"

    def test_multiple_timezone_changes(self, client, student_token, student_user, db_session):
        """Test multiple sequential timezone changes."""
        timezones = [
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "UTC",
        ]

        for tz in timezones:
            response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["timezone"] == tz

            db_session.refresh(student_user)
            assert student_user.timezone == tz


class TestTimezoneValidationInRegistration:
    """Test timezone validation during user registration."""

    def test_register_with_valid_timezone(self, client):
        """Test registration with valid timezone."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "timezone_user@test.com",
                "password": "Password123!",
                "timezone": "America/New_York",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["timezone"] == "America/New_York"

    def test_register_with_invalid_timezone(self, client):
        """Test registration with invalid timezone returns 422."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid_tz_user@test.com",
                "password": "Password123!",
                "timezone": "Invalid/Timezone",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid IANA timezone" in response.text

    def test_register_with_abbreviation_timezone(self, client):
        """Test registration with timezone abbreviation returns 422."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "abbrev_tz_user@test.com",
                "password": "Password123!",
                "timezone": "EST",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_without_timezone_defaults_to_utc(self, client):
        """Test registration without timezone defaults to UTC."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "no_tz_user@test.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["timezone"] == "UTC"

    def test_register_with_null_timezone_defaults_to_utc(self, client):
        """Test registration with null timezone defaults to UTC."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "null_tz_user@test.com",
                "password": "Password123!",
                "timezone": None,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["timezone"] == "UTC"

    def test_register_with_various_valid_timezones(self, client):
        """Test registration with various valid IANA timezones."""
        test_cases = [
            ("tz_user_1@test.com", "America/Los_Angeles"),
            ("tz_user_2@test.com", "Europe/Paris"),
            ("tz_user_3@test.com", "Asia/Tokyo"),
            ("tz_user_4@test.com", "Australia/Sydney"),
            ("tz_user_5@test.com", "UTC"),
            ("tz_user_6@test.com", "Etc/GMT"),
        ]

        for email, timezone in test_cases:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": email,
                    "password": "Password123!",
                    "timezone": timezone,
                },
            )
            assert (
                response.status_code == status.HTTP_201_CREATED
            ), f"Registration with timezone {timezone} should succeed"
            assert response.json()["timezone"] == timezone
