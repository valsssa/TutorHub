"""Centralized datetime utilities for timezone-aware operations.

All datetime operations in the codebase MUST use these utilities
to ensure timezone consistency. Never use datetime.utcnow().
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current time as timezone-aware UTC datetime.

    Use this instead of datetime.utcnow() or datetime.now().
    """
    return datetime.now(timezone.utc)


def is_aware(dt: datetime) -> bool:
    """Check if datetime is timezone-aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def ensure_utc(dt: datetime) -> datetime:
    """Validate that datetime is timezone-aware UTC.

    Raises:
        ValueError: If datetime is naive (no timezone info)
    """
    if not is_aware(dt):
        raise ValueError(
            f"Received naive datetime {dt}. All datetimes must be timezone-aware UTC."
        )
    return dt
