"""
Calendar Conflict Checking Service

Provides external calendar conflict detection for booking creation.
Uses caching to minimize API calls while ensuring availability accuracy.

Features:
- Checks Google Calendar for busy times during requested booking slots
- Caches results briefly (2 minutes) to reduce API load
- Graceful degradation: calendar check failures don't block bookings
- Token refresh handling for expired access tokens
"""

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from core.google_calendar import google_calendar
from models import User

logger = logging.getLogger(__name__)

# Cache for calendar busy times: key -> (busy_times, expiry_timestamp)
# Key format: f"calendar_busy:{user_id}:{start_iso}:{end_iso}"
_calendar_cache: dict[str, tuple[list[dict[str, Any]], float]] = {}

# Cache TTL in seconds (2 minutes - balance between freshness and API limits)
CALENDAR_CACHE_TTL = 120


class CalendarAPIError(Exception):
    """Raised when calendar API calls fail."""

    pass


class CalendarConflictService:
    """
    Service for checking external calendar conflicts at booking time.

    This service provides real-time calendar conflict detection by querying
    the tutor's connected Google Calendar. Results are cached briefly to
    avoid excessive API calls during peak booking times.
    """

    def __init__(self, db: Session):
        self.db = db

    async def check_calendar_conflict(
        self,
        tutor_user: User,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[bool, str | None]:
        """
        Check if tutor has external calendar conflicts for the requested time.

        Args:
            tutor_user: The tutor's User model (must have calendar tokens)
            start_time: Proposed booking start time (UTC)
            end_time: Proposed booking end time (UTC)

        Returns:
            Tuple of (has_conflict, error_message)
            - (True, message) if there's a conflict
            - (False, None) if no conflict
            - (False, None) if calendar check fails (graceful degradation)

        Note:
            Calendar check failures are logged but don't block booking creation.
            This ensures the platform remains functional even if Google Calendar
            API is temporarily unavailable.
        """
        # Verify calendar is connected
        if not tutor_user.google_calendar_refresh_token:
            logger.debug(f"Tutor {tutor_user.id} has no calendar connected")
            return False, None

        # Ensure times are UTC
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)

        # Check cache first
        cache_key = self._get_cache_key(tutor_user.id, start_time, end_time)
        cached_result = self._get_cached_busy_times(cache_key)

        if cached_result is not None:
            logger.debug(f"Using cached calendar data for tutor {tutor_user.id}")
            busy_times = cached_result
        else:
            # Fetch fresh data from Google Calendar
            try:
                busy_times = await self._fetch_busy_times(
                    tutor_user, start_time, end_time
                )
                # Cache the result
                self._cache_busy_times(cache_key, busy_times)
            except CalendarAPIError as e:
                logger.warning(
                    f"Calendar check failed for tutor {tutor_user.id}: {e}"
                )
                # Graceful degradation - don't block booking if calendar check fails
                return False, None

        # Check if any busy time overlaps with the requested slot
        conflict = self._check_overlap(busy_times, start_time, end_time)

        if conflict:
            return True, "Tutor has a conflict on their external calendar during this time"

        return False, None

    async def _fetch_busy_times(
        self,
        tutor_user: User,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch busy times from Google Calendar API.

        Handles token refresh if access token is expired.

        Raises:
            CalendarAPIError: If the calendar API call fails
        """
        access_token = tutor_user.google_calendar_access_token
        refresh_token = tutor_user.google_calendar_refresh_token

        # Check if token needs refresh
        if self._is_token_expired(tutor_user):
            try:
                access_token = await self._refresh_token(tutor_user)
            except Exception as e:
                raise CalendarAPIError(f"Token refresh failed: {e}") from e

        # Expand the time range slightly to catch edge cases
        # (e.g., meetings that start exactly when booking ends)
        query_start = start_time - timedelta(minutes=1)
        query_end = end_time + timedelta(minutes=1)

        try:
            busy_times = await google_calendar.check_busy_times(
                access_token=access_token,
                refresh_token=refresh_token,
                start_time=query_start,
                end_time=query_end,
            )
            return busy_times
        except Exception as e:
            raise CalendarAPIError(f"Freebusy API call failed: {e}") from e

    def _is_token_expired(self, user: User) -> bool:
        """Check if the user's calendar access token is expired or near expiry."""
        if not user.google_calendar_token_expires:
            return True

        # Consider expired if within 5 minutes of expiry
        buffer = timedelta(minutes=5)
        return datetime.now(UTC) >= user.google_calendar_token_expires - buffer

    async def _refresh_token(self, user: User) -> str:
        """
        Refresh the user's Google Calendar access token.

        Updates the user record with new token and expiry time.

        Returns:
            The new access token
        """
        tokens = await google_calendar.refresh_access_token(
            user.google_calendar_refresh_token
        )

        new_access_token = tokens["access_token"]
        expires_in = tokens.get("expires_in", 3600)

        # Update user with new token
        user.google_calendar_access_token = new_access_token
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(
            seconds=expires_in
        )
        user.updated_at = datetime.now(UTC)
        self.db.flush()  # Persist changes without committing

        logger.info(f"Refreshed calendar token for user {user.id}")
        return new_access_token

    def _check_overlap(
        self,
        busy_times: list[dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """
        Check if any busy time block overlaps with the requested slot.

        Two time ranges overlap if:
        - busy_start < booking_end AND busy_end > booking_start
        """
        from dateutil import parser

        for busy in busy_times:
            try:
                busy_start = parser.isoparse(busy.get("start", ""))
                busy_end = parser.isoparse(busy.get("end", ""))

                # Check for overlap
                if busy_start < end_time and busy_end > start_time:
                    logger.debug(
                        f"Calendar conflict found: busy {busy_start}-{busy_end} "
                        f"overlaps with booking {start_time}-{end_time}"
                    )
                    return True
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse busy time: {busy}, error: {e}")
                continue

        return False

    def _get_cache_key(
        self, user_id: int, start_time: datetime, end_time: datetime
    ) -> str:
        """Generate cache key for calendar busy times."""
        # Round times to minute precision for better cache hits
        start_rounded = start_time.replace(second=0, microsecond=0)
        end_rounded = end_time.replace(second=0, microsecond=0)
        return f"calendar_busy:{user_id}:{start_rounded.isoformat()}:{end_rounded.isoformat()}"

    def _get_cached_busy_times(
        self, cache_key: str
    ) -> list[dict[str, Any]] | None:
        """Get cached busy times if still valid."""
        if cache_key in _calendar_cache:
            busy_times, expiry = _calendar_cache[cache_key]
            if time.time() < expiry:
                return busy_times
            else:
                # Expired, remove from cache
                del _calendar_cache[cache_key]
        return None

    def _cache_busy_times(
        self, cache_key: str, busy_times: list[dict[str, Any]]
    ) -> None:
        """Cache busy times with TTL."""
        _calendar_cache[cache_key] = (busy_times, time.time() + CALENDAR_CACHE_TTL)

        # Simple cache cleanup: remove expired entries if cache is large
        if len(_calendar_cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self) -> None:
        """Remove expired entries from the cache."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in _calendar_cache.items() if expiry <= now
        ]
        for key in expired_keys:
            del _calendar_cache[key]


def invalidate_calendar_cache(user_id: int | None = None) -> None:
    """
    Invalidate calendar cache entries.

    Args:
        user_id: If provided, only invalidate entries for this user.
                 If None, invalidate all calendar cache entries.
    """
    if user_id is None:
        _calendar_cache.clear()
    else:
        pattern = f"calendar_busy:{user_id}:"
        keys_to_remove = [key for key in _calendar_cache if key.startswith(pattern)]
        for key in keys_to_remove:
            del _calendar_cache[key]
