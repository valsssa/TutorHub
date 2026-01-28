"""Tests for timezone utilities module."""

from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

import pytest

from core.timezone import (
    VALID_TIMEZONES,
    convert_to_timezone,
    format_dual_timezone,
    format_time_in_timezone,
    get_timezone_abbreviation,
    is_valid_timezone,
)


class TestValidTimezones:
    """Test VALID_TIMEZONES constant."""

    def test_valid_timezones_is_frozen_set(self):
        """Test VALID_TIMEZONES is a frozenset for immutability."""
        assert isinstance(VALID_TIMEZONES, frozenset)

    def test_valid_timezones_contains_common_timezones(self):
        """Test common timezones are included."""
        common_timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
            "Pacific/Auckland",
        ]
        for tz in common_timezones:
            assert tz in VALID_TIMEZONES, f"{tz} should be in VALID_TIMEZONES"

    def test_valid_timezones_not_empty(self):
        """Test VALID_TIMEZONES has many entries."""
        # There are hundreds of IANA timezones
        assert len(VALID_TIMEZONES) > 400


class TestIsValidTimezone:
    """Test is_valid_timezone function."""

    def test_utc_is_valid(self):
        """Test UTC is valid."""
        assert is_valid_timezone("UTC") is True

    def test_common_us_timezones_valid(self):
        """Test common US timezones are valid."""
        us_timezones = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "Pacific/Honolulu",
        ]
        for tz in us_timezones:
            assert is_valid_timezone(tz) is True, f"{tz} should be valid"

    def test_common_european_timezones_valid(self):
        """Test common European timezones are valid."""
        eu_timezones = [
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Moscow",
            "Europe/Istanbul",
        ]
        for tz in eu_timezones:
            assert is_valid_timezone(tz) is True, f"{tz} should be valid"

    def test_common_asian_timezones_valid(self):
        """Test common Asian timezones are valid."""
        asia_timezones = [
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Hong_Kong",
            "Asia/Singapore",
            "Asia/Dubai",
            "Asia/Kolkata",
        ]
        for tz in asia_timezones:
            assert is_valid_timezone(tz) is True, f"{tz} should be valid"

    def test_invalid_timezone_returns_false(self):
        """Test invalid timezone identifiers return False."""
        invalid_timezones = [
            "Invalid/Timezone",
            "NotATimezone",
            "EST",  # Abbreviations are not valid IANA identifiers
            "PST",
            "GMT+5",  # Offset format is not IANA
            "",
            "America/InvalidCity",
            "Europe/FakeCity",
            "123",
            "America",
            "New_York",
        ]
        for tz in invalid_timezones:
            assert is_valid_timezone(tz) is False, f"{tz} should be invalid"

    def test_case_sensitive(self):
        """Test timezone validation is case sensitive."""
        assert is_valid_timezone("america/new_york") is False
        assert is_valid_timezone("AMERICA/NEW_YORK") is False
        assert is_valid_timezone("America/New_York") is True

    def test_etc_timezones_valid(self):
        """Test Etc/ timezone entries are valid."""
        etc_timezones = [
            "Etc/UTC",
            "Etc/GMT",
            "Etc/GMT+0",
            "Etc/GMT-0",
        ]
        for tz in etc_timezones:
            assert is_valid_timezone(tz) is True, f"{tz} should be valid"


class TestConvertToTimezone:
    """Test convert_to_timezone function."""

    def test_utc_to_eastern(self):
        """Test converting UTC to Eastern time."""
        # Create a UTC datetime (January - no DST)
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        eastern = convert_to_timezone(utc_dt, to_tz="America/New_York")

        # In January, EST is UTC-5
        assert eastern.hour == 7
        assert eastern.tzinfo == ZoneInfo("America/New_York")

    def test_utc_to_pacific(self):
        """Test converting UTC to Pacific time."""
        utc_dt = datetime(2024, 1, 15, 20, 0, 0, tzinfo=ZoneInfo("UTC"))
        pacific = convert_to_timezone(utc_dt, to_tz="America/Los_Angeles")

        # In January, PST is UTC-8
        assert pacific.hour == 12
        assert pacific.tzinfo == ZoneInfo("America/Los_Angeles")

    def test_naive_datetime_assumes_utc(self):
        """Test naive datetime defaults to UTC when from_tz is None."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)
        result = convert_to_timezone(naive_dt, to_tz="America/New_York")

        # Should treat as UTC, then convert to Eastern (UTC-5 in January)
        assert result.hour == 7

    def test_naive_datetime_with_from_tz(self):
        """Test naive datetime with explicit from_tz."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)
        result = convert_to_timezone(
            naive_dt, from_tz="America/New_York", to_tz="America/Los_Angeles"
        )

        # Eastern 12:00 -> Pacific (3 hours earlier)
        assert result.hour == 9

    def test_same_timezone_no_change(self):
        """Test converting to same timezone returns same time."""
        utc_dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = convert_to_timezone(utc_dt, to_tz="UTC")

        assert result.hour == 12
        assert result.minute == 30

    def test_invalid_target_timezone_raises(self):
        """Test invalid target timezone raises ValueError."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        with pytest.raises(ValueError, match="Invalid target timezone"):
            convert_to_timezone(utc_dt, to_tz="Invalid/Timezone")

    def test_invalid_source_timezone_raises(self):
        """Test invalid source timezone raises ValueError."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)
        with pytest.raises(ValueError, match="Invalid source timezone"):
            convert_to_timezone(naive_dt, from_tz="Invalid/Timezone", to_tz="UTC")

    def test_dst_transition_spring(self):
        """Test handling of DST transition (spring forward)."""
        # March 10, 2024 - US DST starts at 2am
        utc_dt = datetime(2024, 3, 10, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        eastern = convert_to_timezone(utc_dt, to_tz="America/New_York")

        # After DST starts, should be EDT (UTC-4)
        assert eastern.hour == 4

    def test_dst_transition_fall(self):
        """Test handling of DST transition (fall back)."""
        # November 3, 2024 - US DST ends at 2am
        utc_dt = datetime(2024, 11, 3, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        eastern = convert_to_timezone(utc_dt, to_tz="America/New_York")

        # After DST ends, should be EST (UTC-5)
        assert eastern.hour == 3

    def test_cross_day_boundary(self):
        """Test conversion that crosses day boundary."""
        # Late night in UTC becomes previous day in Western US
        utc_dt = datetime(2024, 1, 15, 3, 0, 0, tzinfo=ZoneInfo("UTC"))
        pacific = convert_to_timezone(utc_dt, to_tz="America/Los_Angeles")

        # UTC 3am -> PST 7pm previous day (UTC-8)
        assert pacific.day == 14
        assert pacific.hour == 19

    def test_cross_day_boundary_forward(self):
        """Test conversion that crosses day boundary forward."""
        # Late night in Asia becomes next day in UTC
        tokyo_dt = datetime(2024, 1, 15, 23, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        utc_result = convert_to_timezone(tokyo_dt, to_tz="UTC")

        # Tokyo 11pm -> UTC 2pm same day (Tokyo is UTC+9)
        assert utc_result.day == 15
        assert utc_result.hour == 14


class TestFormatTimeInTimezone:
    """Test format_time_in_timezone function."""

    def test_default_format(self):
        """Test default time format (12-hour with AM/PM)."""
        utc_dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(utc_dt, "UTC")

        assert "2:30 PM" in result or "02:30 PM" in result

    def test_custom_format(self):
        """Test custom time format."""
        utc_dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(utc_dt, "UTC", format_str="%H:%M")

        assert result == "14:30"

    def test_timezone_conversion_in_format(self):
        """Test that formatting correctly converts timezone."""
        utc_dt = datetime(2024, 1, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        # Convert to Eastern (UTC-5 in January)
        result = format_time_in_timezone(utc_dt, "America/New_York")

        assert "12:00 PM" in result or "12:00 pm" in result.lower()

    def test_morning_time(self):
        """Test morning time formatting."""
        utc_dt = datetime(2024, 1, 15, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(utc_dt, "UTC")

        assert "8:00 AM" in result or "08:00 AM" in result

    def test_midnight(self):
        """Test midnight formatting."""
        utc_dt = datetime(2024, 1, 15, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(utc_dt, "UTC")

        assert "12:00 AM" in result or "00:00" in result

    def test_noon(self):
        """Test noon formatting."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(utc_dt, "UTC")

        assert "12:00 PM" in result


class TestGetTimezoneAbbreviation:
    """Test get_timezone_abbreviation function."""

    def test_utc_abbreviation(self):
        """Test UTC abbreviation."""
        result = get_timezone_abbreviation("UTC")
        assert result == "UTC"

    def test_eastern_winter_abbreviation(self):
        """Test Eastern timezone abbreviation in winter (EST)."""
        winter_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = get_timezone_abbreviation("America/New_York", winter_dt)
        assert result == "EST"

    def test_eastern_summer_abbreviation(self):
        """Test Eastern timezone abbreviation in summer (EDT)."""
        summer_dt = datetime(2024, 7, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = get_timezone_abbreviation("America/New_York", summer_dt)
        assert result == "EDT"

    def test_pacific_winter_abbreviation(self):
        """Test Pacific timezone abbreviation in winter (PST)."""
        winter_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = get_timezone_abbreviation("America/Los_Angeles", winter_dt)
        assert result == "PST"

    def test_pacific_summer_abbreviation(self):
        """Test Pacific timezone abbreviation in summer (PDT)."""
        summer_dt = datetime(2024, 7, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = get_timezone_abbreviation("America/Los_Angeles", summer_dt)
        assert result == "PDT"

    def test_invalid_timezone_returns_utc(self):
        """Test invalid timezone returns UTC as fallback."""
        result = get_timezone_abbreviation("Invalid/Timezone")
        assert result == "UTC"

    def test_no_dst_timezone(self):
        """Test timezone that doesn't observe DST."""
        # Arizona doesn't observe DST
        winter_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        summer_dt = datetime(2024, 7, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        winter_result = get_timezone_abbreviation("America/Phoenix", winter_dt)
        summer_result = get_timezone_abbreviation("America/Phoenix", summer_dt)

        # Should be MST all year
        assert winter_result == "MST"
        assert summer_result == "MST"


class TestFormatDualTimezone:
    """Test format_dual_timezone function."""

    def test_different_timezones_shows_both(self):
        """Test that different timezones show both times."""
        utc_dt = datetime(2024, 1, 15, 19, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/New_York",
            other_tz="America/Los_Angeles",
            other_label="tutor",
        )

        # Eastern 2pm, Pacific 11am in January
        assert "2:00 PM" in result or "02:00 PM" in result
        assert "EST" in result
        assert "11:00 AM" in result or "11:00 am" in result.lower()
        assert "PST" in result
        assert "tutor" in result

    def test_same_timezone_shows_single(self):
        """Test same timezone shows only one time."""
        utc_dt = datetime(2024, 1, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/New_York",
            other_tz="America/New_York",
            other_label="tutor",
        )

        # Should show single time, not dual
        assert "tutor" not in result
        assert result.count("EST") == 1

    def test_custom_label(self):
        """Test custom label for other party."""
        utc_dt = datetime(2024, 1, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/New_York",
            other_tz="Europe/London",
            other_label="student",
        )

        assert "student" in result

    def test_default_label(self):
        """Test default label is 'other'."""
        utc_dt = datetime(2024, 1, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/New_York",
            other_tz="Europe/London",
        )

        assert "other" in result

    def test_transatlantic_booking(self):
        """Test US-to-Europe booking display."""
        utc_dt = datetime(2024, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/New_York",  # Eastern
            other_tz="Europe/London",  # GMT
            other_label="tutor",
        )

        # Eastern 1pm, London 6pm in January
        assert "1:00 PM" in result or "01:00 PM" in result
        assert "6:00 PM" in result or "06:00 PM" in result
        assert "tutor" in result

    def test_pacific_to_asia_booking(self):
        """Test US West Coast to Asia booking display."""
        utc_dt = datetime(2024, 1, 15, 1, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_dual_timezone(
            utc_dt,
            user_tz="America/Los_Angeles",  # PST (UTC-8)
            other_tz="Asia/Tokyo",  # JST (UTC+9)
            other_label="tutor",
        )

        # PST 5pm (Jan 14), Tokyo 10am (Jan 15)
        assert "tutor" in result
        assert "PST" in result or "PDT" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_leap_year_date(self):
        """Test handling of leap year date."""
        leap_dt = datetime(2024, 2, 29, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = convert_to_timezone(leap_dt, to_tz="America/New_York")

        assert result.month == 2
        assert result.day == 29

    def test_year_boundary(self):
        """Test handling of year boundary conversion."""
        # New Year's Eve UTC midnight -> still Dec 31 in West Coast
        new_years_utc = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        pacific = convert_to_timezone(new_years_utc, to_tz="America/Los_Angeles")

        assert pacific.year == 2023
        assert pacific.month == 12
        assert pacific.day == 31

    def test_very_early_morning(self):
        """Test very early morning times."""
        early_dt = datetime(2024, 1, 15, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(early_dt, "UTC")

        assert "1:30 AM" in result or "01:30 AM" in result

    def test_very_late_night(self):
        """Test very late night times."""
        late_dt = datetime(2024, 1, 15, 23, 45, 0, tzinfo=ZoneInfo("UTC"))
        result = format_time_in_timezone(late_dt, "UTC")

        assert "11:45 PM" in result

    def test_minutes_preserved(self):
        """Test that minutes are preserved in conversion."""
        utc_dt = datetime(2024, 1, 15, 12, 37, 0, tzinfo=ZoneInfo("UTC"))
        eastern = convert_to_timezone(utc_dt, to_tz="America/New_York")

        assert eastern.minute == 37

    def test_seconds_preserved(self):
        """Test that seconds are preserved in conversion."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 45, tzinfo=ZoneInfo("UTC"))
        eastern = convert_to_timezone(utc_dt, to_tz="America/New_York")

        assert eastern.second == 45

    def test_half_hour_offset_timezone(self):
        """Test timezone with half-hour offset (India)."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        india = convert_to_timezone(utc_dt, to_tz="Asia/Kolkata")

        # India is UTC+5:30
        assert india.hour == 17
        assert india.minute == 30

    def test_45_minute_offset_timezone(self):
        """Test timezone with 45-minute offset (Nepal)."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        nepal = convert_to_timezone(utc_dt, to_tz="Asia/Kathmandu")

        # Nepal is UTC+5:45
        assert nepal.hour == 17
        assert nepal.minute == 45
