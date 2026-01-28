"""End-to-end tests for timezone functionality across the application."""

from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi import status


class TestTimezoneRegistrationToLoginFlow:
    """Test complete timezone flow from registration through login."""

    def test_register_with_timezone_then_login(self, client):
        """Test user can register with timezone and see it after login."""
        # Register with specific timezone
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "tz_flow_test@test.com",
                "password": "Password123!",
                "timezone": "America/New_York",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        assert register_response.json()["timezone"] == "America/New_York"

        # Login
        login_response = client.post(
            "/api/auth/login",
            data={"username": "tz_flow_test@test.com", "password": "Password123!"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Get current user - verify timezone persists
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["timezone"] == "America/New_York"

    def test_register_without_timezone_defaults_utc_then_update(self, client):
        """Test user registers without timezone, defaults to UTC, then updates."""
        # Register without timezone
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "tz_default_test@test.com",
                "password": "Password123!",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        assert register_response.json()["timezone"] == "UTC"

        # Login
        login_response = client.post(
            "/api/auth/login",
            data={"username": "tz_default_test@test.com", "password": "Password123!"},
        )
        token = login_response.json()["access_token"]

        # Update timezone
        update_response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"timezone": "Europe/London"},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["timezone"] == "Europe/London"

        # Verify persisted
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.json()["timezone"] == "Europe/London"


class TestTimezoneSyncWorkflow:
    """Test the timezone sync workflow for detecting browser timezone changes."""

    def test_sync_detects_change_then_user_updates(self, client, student_token, student_user):
        """Test sync detects change and user can update."""
        # User's saved timezone is UTC (from fixture)
        # Simulate browser detecting different timezone
        sync_response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Asia/Tokyo"},
        )
        assert sync_response.status_code == status.HTTP_200_OK
        assert sync_response.json()["needs_update"] is True
        assert sync_response.json()["saved_timezone"] == "UTC"
        assert sync_response.json()["detected_timezone"] == "Asia/Tokyo"

        # User chooses to update
        update_response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Asia/Tokyo"},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["timezone"] == "Asia/Tokyo"

        # Sync again - should show no update needed
        sync_response2 = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Asia/Tokyo"},
        )
        assert sync_response2.json()["needs_update"] is False

    def test_sync_user_keeps_saved_timezone(self, client, student_token, student_user):
        """Test user can choose to keep saved timezone."""
        # Sync shows different timezone
        sync_response = client.post(
            "/api/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Australia/Sydney"},
        )
        assert sync_response.json()["needs_update"] is True

        # User chooses NOT to update - timezone stays as is
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert me_response.json()["timezone"] == "UTC"  # Unchanged


class TestTimezoneAcrossRoles:
    """Test timezone functionality across different user roles."""

    def test_student_timezone_workflow(self, client, student_token, student_user, db_session):
        """Test complete timezone workflow for student."""
        # Update timezone
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/Chicago"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify via /me
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert me_response.json()["timezone"] == "America/Chicago"

    def test_tutor_timezone_workflow(self, client, tutor_token, tutor_user, db_session):
        """Test complete timezone workflow for tutor."""
        # Update timezone
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"timezone": "Europe/Paris"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify via /me
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert me_response.json()["timezone"] == "Europe/Paris"

    def test_admin_timezone_workflow(self, client, admin_token, admin_user, db_session):
        """Test complete timezone workflow for admin."""
        # Update timezone
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"timezone": "Asia/Singapore"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify via /me
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert me_response.json()["timezone"] == "Asia/Singapore"


class TestTimezoneDataIntegrity:
    """Test timezone data integrity and consistency."""

    def test_timezone_survives_multiple_updates(self, client, student_token, student_user, db_session):
        """Test timezone value survives multiple updates."""
        timezones = [
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "America/Los_Angeles",
            "UTC",
        ]

        for tz in timezones:
            # Update
            update_response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert update_response.status_code == status.HTTP_200_OK

            # Verify
            me_response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert me_response.json()["timezone"] == tz

    def test_timezone_not_affected_by_other_updates(self, client, student_token, student_user, db_session):
        """Test timezone isn't affected by other profile updates."""
        # Set timezone
        client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Europe/Berlin"},
        )

        # Update user info (not timezone)
        client.patch(
            "/api/users/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"first_name": "UpdatedName"},
        )

        # Verify timezone unchanged
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert me_response.json()["timezone"] == "Europe/Berlin"
        assert me_response.json()["first_name"] == "UpdatedName"


class TestTimezoneEdgeCasesE2E:
    """End-to-end tests for timezone edge cases."""

    def test_rapid_timezone_changes(self, client, student_token):
        """Test handling rapid timezone changes."""
        timezones = [
            "America/New_York",
            "America/Los_Angeles",
            "America/New_York",
            "Europe/London",
            "America/New_York",
        ]

        for tz in timezones:
            response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert response.status_code == status.HTTP_200_OK

        # Final state should be last timezone
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert me_response.json()["timezone"] == "America/New_York"

    def test_all_continental_timezones(self, client, student_token):
        """Test a representative timezone from each continent."""
        continental_timezones = [
            ("America/New_York", "North America"),
            ("America/Sao_Paulo", "South America"),
            ("Europe/London", "Europe"),
            ("Africa/Cairo", "Africa"),
            ("Asia/Tokyo", "Asia"),
            ("Australia/Sydney", "Australia"),
            ("Pacific/Auckland", "Pacific"),
            ("Antarctica/McMurdo", "Antarctica"),
        ]

        for tz, continent in continental_timezones:
            response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert response.status_code == status.HTTP_200_OK, f"Failed for {continent}: {tz}"

            me_response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert me_response.json()["timezone"] == tz, f"Timezone not saved for {continent}"

    def test_uncommon_timezone_offsets(self, client, student_token):
        """Test timezones with uncommon offsets."""
        uncommon_timezones = [
            "Asia/Kolkata",  # UTC+5:30
            "Asia/Kathmandu",  # UTC+5:45
            "Australia/Eucla",  # UTC+8:45
            "Pacific/Chatham",  # UTC+12:45/+13:45
        ]

        for tz in uncommon_timezones:
            response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert response.status_code == status.HTTP_200_OK, f"Failed for {tz}"


class TestTimezoneValidationE2E:
    """End-to-end validation tests for timezone."""

    def test_various_invalid_timezones_rejected(self, client, student_token):
        """Test various invalid timezone formats are rejected."""
        invalid_timezones = [
            "EST",
            "PST",
            "GMT+5",
            "UTC+5",
            "+05:00",
            "5",
            "new_york",
            "America",
            "america/new_york",
            "AMERICA/NEW_YORK",
            " America/New_York",
            "America/New_York ",
            "America/Fake_City",
            "Fake/Timezone",
            "",
        ]

        for invalid_tz in invalid_timezones:
            if invalid_tz == "":
                continue  # Empty string is handled differently (no-op)

            response = client.patch(
                "/api/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": invalid_tz},
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"Should reject invalid timezone: {invalid_tz}"
            )

    def test_null_timezone_noop(self, client, student_token, student_user, db_session):
        """Test null timezone in update is a no-op."""
        # Set initial timezone
        client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/Denver"},
        )

        # Send null - should not change
        response = client.patch(
            "/api/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": None},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify unchanged
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert me_response.json()["timezone"] == "America/Denver"
