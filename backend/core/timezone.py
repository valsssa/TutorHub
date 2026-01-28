"""Timezone utilities for consistent timezone handling across the application."""

from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

# Cache of valid IANA timezones for fast validation
VALID_TIMEZONES: frozenset[str] = frozenset(available_timezones())


def is_valid_timezone(tz: str) -> bool:
    """
    Check if a timezone string is a valid IANA timezone identifier.

    Args:
        tz: Timezone string to validate (e.g., "America/New_York", "UTC")

    Returns:
        True if valid IANA timezone, False otherwise
    """
    return tz in VALID_TIMEZONES


def convert_to_timezone(
    dt: datetime, from_tz: str | None = None, to_tz: str = "UTC"
) -> datetime:
    """
    Convert a datetime from one timezone to another.

    Args:
        dt: Datetime to convert (can be naive or aware)
        from_tz: Source timezone. If None and dt is naive, assumes UTC.
        to_tz: Target timezone (default UTC)

    Returns:
        Datetime in target timezone
    """
    if not is_valid_timezone(to_tz):
        raise ValueError(f"Invalid target timezone: {to_tz}")

    # Handle naive datetime
    if dt.tzinfo is None:
        if from_tz is None:
            from_tz = "UTC"
        if not is_valid_timezone(from_tz):
            raise ValueError(f"Invalid source timezone: {from_tz}")
        dt = dt.replace(tzinfo=ZoneInfo(from_tz))
    elif from_tz is not None:
        # If dt is already aware but from_tz is specified, convert first
        if not is_valid_timezone(from_tz):
            raise ValueError(f"Invalid source timezone: {from_tz}")
        dt = dt.astimezone(ZoneInfo(from_tz))

    return dt.astimezone(ZoneInfo(to_tz))


def format_time_in_timezone(dt: datetime, tz: str, format_str: str = "%I:%M %p") -> str:
    """
    Format a datetime in a specific timezone.

    Args:
        dt: Datetime to format
        tz: Timezone to format in
        format_str: strftime format string (default "2:00 PM")

    Returns:
        Formatted time string
    """
    converted = convert_to_timezone(dt, to_tz=tz)
    return converted.strftime(format_str)


def get_timezone_abbreviation(tz: str, dt: datetime | None = None) -> str:
    """
    Get the timezone abbreviation (e.g., "EST", "PST") for a timezone.

    Args:
        tz: IANA timezone identifier
        dt: Datetime to get abbreviation for (affects DST). Uses now if None.

    Returns:
        Timezone abbreviation
    """
    if not is_valid_timezone(tz):
        return "UTC"

    if dt is None:
        dt = datetime.now(ZoneInfo("UTC"))

    converted = convert_to_timezone(dt, to_tz=tz)
    return converted.strftime("%Z")


def format_dual_timezone(
    dt: datetime, user_tz: str, other_tz: str, other_label: str = "other"
) -> str:
    """
    Format a datetime showing both user's timezone and another party's timezone.

    Example output: "2:00 PM EST (11:00 AM PST for tutor)"

    Args:
        dt: Datetime to format (should be UTC-aware)
        user_tz: User's preferred timezone
        other_tz: The other party's timezone
        other_label: Label for the other party (e.g., "tutor", "student")

    Returns:
        Dual timezone formatted string
    """
    user_time = format_time_in_timezone(dt, user_tz)
    user_abbr = get_timezone_abbreviation(user_tz, dt)

    # If timezones are the same, just return single timezone
    if user_tz == other_tz:
        return f"{user_time} {user_abbr}"

    other_time = format_time_in_timezone(dt, other_tz)
    other_abbr = get_timezone_abbreviation(other_tz, dt)

    return f"{user_time} {user_abbr} ({other_time} {other_abbr} for {other_label})"
