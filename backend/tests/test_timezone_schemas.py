"""Tests for timezone validation in Pydantic schemas."""

import pytest
from pydantic import ValidationError

from schemas import (
    TutorAvailabilityBulkUpdate,
    UserCreate,
    UserPreferencesUpdate,
    UserProfileUpdate,
    UserSelfUpdate,
)


class TestUserCreateTimezoneValidation:
    """Test timezone validation in UserCreate schema."""

    def test_valid_iana_timezone(self):
        """Test valid IANA timezone is accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="America/New_York",
        )
        assert user.timezone == "America/New_York"

    def test_utc_timezone(self):
        """Test UTC is accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="UTC",
        )
        assert user.timezone == "UTC"

    def test_european_timezone(self):
        """Test European timezones are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Europe/London",
        )
        assert user.timezone == "Europe/London"

    def test_asian_timezone(self):
        """Test Asian timezones are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Asia/Tokyo",
        )
        assert user.timezone == "Asia/Tokyo"

    def test_pacific_timezone(self):
        """Test Pacific timezones are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Pacific/Auckland",
        )
        assert user.timezone == "Pacific/Auckland"

    def test_etc_timezone(self):
        """Test Etc/ timezones are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Etc/UTC",
        )
        assert user.timezone == "Etc/UTC"

    def test_invalid_timezone_raises_error(self):
        """Test invalid timezone raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone="Invalid/Timezone",
            )
        assert "Invalid IANA timezone" in str(exc_info.value)

    def test_timezone_abbreviation_invalid(self):
        """Test timezone abbreviations are not valid."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone="EST",
            )
        assert "Invalid IANA timezone" in str(exc_info.value)

    def test_timezone_offset_invalid(self):
        """Test timezone offsets are not valid."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone="GMT+5",
            )
        assert "Invalid IANA timezone" in str(exc_info.value)

    def test_none_timezone_defaults_to_utc(self):
        """Test None timezone defaults to UTC."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone=None,
        )
        assert user.timezone == "UTC"

    def test_missing_timezone_defaults_to_utc(self):
        """Test missing timezone defaults to UTC."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
        )
        assert user.timezone == "UTC"

    def test_empty_string_defaults_to_utc(self):
        """Test empty string timezone defaults to UTC."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="",
        )
        assert user.timezone == "UTC"

    def test_case_sensitive_validation(self):
        """Test timezone validation is case sensitive."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone="america/new_york",
            )

    def test_various_us_timezones(self):
        """Test various US timezones are valid."""
        us_timezones = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "Pacific/Honolulu",
            "America/Phoenix",
        ]
        for tz in us_timezones:
            user = UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone=tz,
            )
            assert user.timezone == tz


class TestUserPreferencesUpdateTimezoneValidation:
    """Test timezone validation in UserPreferencesUpdate schema."""

    def test_valid_timezone(self):
        """Test valid timezone is accepted."""
        prefs = UserPreferencesUpdate(timezone="America/New_York")
        assert prefs.timezone == "America/New_York"

    def test_invalid_timezone_raises_error(self):
        """Test invalid timezone raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(timezone="Invalid/Timezone")
        assert "Invalid IANA timezone" in str(exc_info.value)

    def test_none_timezone_is_valid(self):
        """Test None timezone is valid (no update)."""
        prefs = UserPreferencesUpdate(timezone=None)
        assert prefs.timezone is None

    def test_missing_timezone_is_valid(self):
        """Test missing timezone is valid (no update)."""
        prefs = UserPreferencesUpdate()
        assert prefs.timezone is None

    def test_abbreviation_invalid(self):
        """Test timezone abbreviation is invalid."""
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(timezone="PST")

    def test_utc_valid(self):
        """Test UTC is valid."""
        prefs = UserPreferencesUpdate(timezone="UTC")
        assert prefs.timezone == "UTC"

    def test_empty_string_passes(self):
        """Test empty string passes validation but becomes None-like."""
        # Empty string should pass and be treated as no-op in the endpoint
        prefs = UserPreferencesUpdate(timezone="")
        assert prefs.timezone == ""


class TestUserSelfUpdateTimezoneValidation:
    """Test timezone validation in UserSelfUpdate schema."""

    def test_valid_timezone(self):
        """Test valid timezone in self-update."""
        update = UserSelfUpdate(timezone="Europe/Paris")
        assert update.timezone == "Europe/Paris"

    def test_none_timezone(self):
        """Test None timezone (no update)."""
        update = UserSelfUpdate(timezone=None)
        assert update.timezone is None

    def test_partial_update_with_timezone(self):
        """Test partial update including timezone."""
        update = UserSelfUpdate(
            first_name="John",
            timezone="Asia/Tokyo",
        )
        assert update.first_name == "John"
        assert update.timezone == "Asia/Tokyo"

    def test_partial_update_without_timezone(self):
        """Test partial update without timezone."""
        update = UserSelfUpdate(first_name="John")
        assert update.first_name == "John"
        assert update.timezone is None


class TestTutorAvailabilityBulkUpdateTimezone:
    """Test timezone handling in TutorAvailabilityBulkUpdate schema."""

    def test_valid_timezone(self):
        """Test valid timezone in bulk update."""
        update = TutorAvailabilityBulkUpdate(
            availability=[],
            timezone="America/New_York",
            version=1,
        )
        assert update.timezone == "America/New_York"

    def test_default_timezone_is_utc(self):
        """Test default timezone is UTC."""
        update = TutorAvailabilityBulkUpdate(
            availability=[],
            version=1,
        )
        assert update.timezone == "UTC"

    def test_none_timezone(self):
        """Test None timezone."""
        update = TutorAvailabilityBulkUpdate(
            availability=[],
            timezone=None,
            version=1,
        )
        # None should be acceptable
        assert update.timezone is None


class TestTimezoneEdgeCases:
    """Test edge cases in timezone validation."""

    def test_whitespace_around_timezone_not_valid(self):
        """Test timezone with whitespace is not valid."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone=" America/New_York ",
            )

    def test_three_part_timezone(self):
        """Test three-part timezone identifiers are valid."""
        # Some IANA timezones have three parts
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="America/Indiana/Indianapolis",
        )
        assert user.timezone == "America/Indiana/Indianapolis"

    def test_antarctica_timezone(self):
        """Test Antarctica timezones are valid."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Antarctica/McMurdo",
        )
        assert user.timezone == "Antarctica/McMurdo"

    def test_indian_ocean_timezone(self):
        """Test Indian Ocean timezones are valid."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Indian/Maldives",
        )
        assert user.timezone == "Indian/Maldives"

    def test_atlantic_timezone(self):
        """Test Atlantic timezones are valid."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Atlantic/Reykjavik",
        )
        assert user.timezone == "Atlantic/Reykjavik"

    def test_arctic_timezone(self):
        """Test Arctic timezones are valid."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Arctic/Longyearbyen",
        )
        assert user.timezone == "Arctic/Longyearbyen"

    def test_half_hour_offset_timezone(self):
        """Test timezones with half-hour offsets are valid."""
        # India Standard Time (UTC+5:30)
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Asia/Kolkata",
        )
        assert user.timezone == "Asia/Kolkata"

    def test_45_minute_offset_timezone(self):
        """Test timezones with 45-minute offsets are valid."""
        # Nepal Time (UTC+5:45)
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            timezone="Asia/Kathmandu",
        )
        assert user.timezone == "Asia/Kathmandu"

    def test_deprecated_timezone_still_valid(self):
        """Test deprecated but still valid IANA timezones."""
        # US/Eastern is a link to America/New_York
        # It should still be in the IANA database
        try:
            user = UserCreate(
                email="test@example.com",
                password="Password123!",
                timezone="US/Eastern",
            )
            assert user.timezone == "US/Eastern"
        except ValidationError:
            # Some Python versions may not include deprecated timezones
            pytest.skip("Deprecated timezone not available in this Python version")
