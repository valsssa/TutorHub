"""
Time and timezone utilities for consistent datetime handling.

This module provides standardized functions for working with datetimes,
ensuring all timestamps are consistently in UTC and timezone-aware.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """
    Get the current UTC datetime with timezone info.

    Returns:
        Timezone-aware datetime in UTC

    Example:
        created_at = utc_now()
        # Instead of: datetime.now(UTC)
    """
    return datetime.now(UTC)


def utc_today() -> datetime:
    """
    Get today's date at midnight in UTC.

    Returns:
        Timezone-aware datetime at UTC midnight

    Example:
        start_of_day = utc_today()
    """
    now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def to_utc(dt: datetime, tz_string: str | None = None) -> datetime:
    """
    Convert a datetime to UTC.

    Args:
        dt: Datetime to convert (can be naive or aware)
        tz_string: If dt is naive, assume it's in this timezone (e.g., "America/New_York")
                   If None and dt is naive, assumes UTC

    Returns:
        Timezone-aware datetime in UTC

    Example:
        local_time = datetime(2024, 1, 15, 9, 0)  # 9 AM local
        utc_time = to_utc(local_time, "America/New_York")  # 2 PM UTC (EST is UTC-5)
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's in the given timezone
        if tz_string:
            local_tz = ZoneInfo(tz_string)
            dt = dt.replace(tzinfo=local_tz)
        else:
            # Assume UTC if no timezone provided
            dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    return dt.astimezone(UTC)


def from_utc(dt: datetime, tz_string: str) -> datetime:
    """
    Convert a UTC datetime to a local timezone.

    Args:
        dt: UTC datetime (naive assumed UTC, aware converted)
        tz_string: Target timezone (e.g., "Europe/London", "America/Los_Angeles")

    Returns:
        Timezone-aware datetime in the target timezone

    Example:
        utc_time = utc_now()
        london_time = from_utc(utc_time, "Europe/London")
    """
    # Ensure dt is UTC-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    elif dt.tzinfo != UTC:
        dt = dt.astimezone(UTC)

    # Convert to target timezone
    target_tz = ZoneInfo(tz_string)
    return dt.astimezone(target_tz)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format a datetime to a human-readable string.

    Args:
        dt: Datetime to format
        fmt: strftime format string (default includes timezone)

    Returns:
        Formatted datetime string

    Example:
        formatted = format_datetime(utc_now())
        # "2024-01-15 14:30:00 UTC"
    """
    return dt.strftime(fmt)


def format_datetime_for_user(dt: datetime, user_tz: str | None = None) -> str:
    """
    Format a datetime for display to a user in their timezone.

    Args:
        dt: Datetime to format (usually UTC)
        user_tz: User's timezone (e.g., "America/New_York"). If None, displays UTC.

    Returns:
        User-friendly formatted string

    Example:
        booking_time = format_datetime_for_user(booking.start_time, user.timezone)
        # "January 15, 2024 at 9:30 AM EST"
    """
    if user_tz:
        dt = from_utc(dt, user_tz)

    return dt.strftime("%B %d, %Y at %I:%M %p %Z")


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse an ISO 8601 datetime string to a timezone-aware datetime.

    Args:
        iso_string: ISO 8601 formatted string (e.g., "2024-01-15T14:30:00Z")

    Returns:
        Timezone-aware datetime (converted to UTC if needed)

    Example:
        dt = parse_iso_datetime("2024-01-15T14:30:00Z")
        dt = parse_iso_datetime("2024-01-15T09:30:00-05:00")  # Also works
    """
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return to_utc(dt)


def is_past(dt: datetime) -> bool:
    """
    Check if a datetime is in the past.

    Args:
        dt: Datetime to check

    Returns:
        True if dt is before now
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt < now


def is_future(dt: datetime) -> bool:
    """
    Check if a datetime is in the future.

    Args:
        dt: Datetime to check

    Returns:
        True if dt is after now
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt > now


def time_until(dt: datetime) -> timedelta:
    """
    Get the time remaining until a datetime.

    Args:
        dt: Future datetime

    Returns:
        Timedelta representing time until dt (negative if dt is in the past)

    Example:
        remaining = time_until(booking.start_time)
        if remaining.total_seconds() < 3600:
            send_reminder()
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt - now


def time_since(dt: datetime) -> timedelta:
    """
    Get the time elapsed since a datetime.

    Args:
        dt: Past datetime

    Returns:
        Timedelta representing time since dt (negative if dt is in the future)

    Example:
        elapsed = time_since(session.started_at)
        if elapsed.total_seconds() > 3600:
            end_session()
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return now - dt


def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to a datetime.

    Args:
        dt: Base datetime
        days: Number of days to add (can be negative)

    Returns:
        New datetime with days added
    """
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Add hours to a datetime.

    Args:
        dt: Base datetime
        hours: Number of hours to add (can be negative)

    Returns:
        New datetime with hours added
    """
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    Add minutes to a datetime.

    Args:
        dt: Base datetime
        minutes: Number of minutes to add (can be negative)

    Returns:
        New datetime with minutes added
    """
    return dt + timedelta(minutes=minutes)


def start_of_day(dt: datetime) -> datetime:
    """
    Get the start of the day (midnight) for a datetime.

    Args:
        dt: Any datetime

    Returns:
        Datetime at midnight (00:00:00) on the same day
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """
    Get the end of the day (23:59:59.999999) for a datetime.

    Args:
        dt: Any datetime

    Returns:
        Datetime at end of day on the same day
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def days_between(dt1: datetime, dt2: datetime) -> int:
    """
    Calculate the number of days between two datetimes.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        Number of full days between dt1 and dt2 (absolute value)
    """
    diff = abs((dt2 - dt1).days)
    return diff
