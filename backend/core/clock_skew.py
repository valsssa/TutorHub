"""
Clock skew detection and database time utilities.

Provides utilities to detect clock drift between the application server
and the database server, ensuring background jobs use consistent time
references for critical operations.

Usage:
    from core.clock_skew import get_db_time, check_clock_skew, ClockSkewMonitor

    # Get current time from database
    db_time = get_db_time(db)

    # Check and log clock skew
    offset = check_clock_skew(db, threshold_seconds=5)

    # Use monitor for periodic checks
    monitor = ClockSkewMonitor(threshold_seconds=5)
    await monitor.check_and_warn(db)
"""

import logging
from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ClockSkewResult(NamedTuple):
    """Result of a clock skew check."""

    app_time: datetime
    db_time: datetime
    offset_seconds: float
    is_within_threshold: bool


# Default threshold for acceptable clock skew (in seconds)
DEFAULT_SKEW_THRESHOLD_SECONDS = 5

# How often to perform skew checks (in seconds)
SKEW_CHECK_INTERVAL_SECONDS = 300  # 5 minutes


def get_db_time(db: Session) -> datetime:
    """
    Get current UTC time from the database server.

    Uses PostgreSQL's NOW() AT TIME ZONE 'UTC' to get the database server's
    current time, ensuring consistency for time-sensitive operations.

    Args:
        db: SQLAlchemy database session

    Returns:
        Timezone-aware datetime in UTC from the database server
    """
    result = db.execute(text("SELECT NOW() AT TIME ZONE 'UTC'")).scalar()

    # Ensure the result is timezone-aware
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)

    return result


def check_clock_skew(
    db: Session, threshold_seconds: int = DEFAULT_SKEW_THRESHOLD_SECONDS
) -> ClockSkewResult:
    """
    Check clock skew between the application server and database server.

    Compares the current time from Python's datetime to the database
    server's time and logs a warning if the difference exceeds the threshold.

    Args:
        db: SQLAlchemy database session
        threshold_seconds: Maximum acceptable skew before warning (default: 5)

    Returns:
        ClockSkewResult with app_time, db_time, offset_seconds, and is_within_threshold
    """
    app_time = datetime.now(UTC)
    db_time = get_db_time(db)

    # Calculate offset (positive = app ahead of db, negative = app behind db)
    offset_seconds = (app_time - db_time).total_seconds()
    is_within_threshold = abs(offset_seconds) <= threshold_seconds

    if not is_within_threshold:
        logger.warning(
            "Clock skew detected: app server is %.2f seconds %s database server "
            "(app_time=%s, db_time=%s, threshold=%ds)",
            abs(offset_seconds),
            "ahead of" if offset_seconds > 0 else "behind",
            app_time.isoformat(),
            db_time.isoformat(),
            threshold_seconds,
        )

    return ClockSkewResult(
        app_time=app_time,
        db_time=db_time,
        offset_seconds=offset_seconds,
        is_within_threshold=is_within_threshold,
    )


class ClockSkewMonitor:
    """
    Monitor for clock skew with rate-limited checks.

    Prevents excessive database queries by only checking clock skew
    at specified intervals.

    Usage:
        monitor = ClockSkewMonitor(threshold_seconds=5)

        # In job function:
        await monitor.check_and_warn(db)
        now = get_db_time(db)  # Use db time for comparisons
    """

    def __init__(
        self,
        threshold_seconds: int = DEFAULT_SKEW_THRESHOLD_SECONDS,
        check_interval_seconds: int = SKEW_CHECK_INTERVAL_SECONDS,
    ):
        """
        Initialize the clock skew monitor.

        Args:
            threshold_seconds: Maximum acceptable skew before warning
            check_interval_seconds: Minimum time between skew checks
        """
        self.threshold_seconds = threshold_seconds
        self.check_interval_seconds = check_interval_seconds
        self._last_check_time: datetime | None = None
        self._last_skew_result: ClockSkewResult | None = None

    def should_check(self) -> bool:
        """Determine if a skew check is due based on the interval."""
        if self._last_check_time is None:
            return True

        elapsed = (datetime.now(UTC) - self._last_check_time).total_seconds()
        return elapsed >= self.check_interval_seconds

    def check_and_warn(self, db: Session) -> ClockSkewResult | None:
        """
        Check clock skew if interval has elapsed and log warnings.

        Args:
            db: SQLAlchemy database session

        Returns:
            ClockSkewResult if check was performed, None if skipped
        """
        if not self.should_check():
            return self._last_skew_result

        result = check_clock_skew(db, self.threshold_seconds)
        self._last_check_time = datetime.now(UTC)
        self._last_skew_result = result

        # Log info level if within threshold for monitoring purposes
        if result.is_within_threshold:
            logger.debug(
                "Clock skew check: %.2f seconds offset (within %ds threshold)",
                result.offset_seconds,
                self.threshold_seconds,
            )

        return result

    @property
    def last_offset(self) -> float | None:
        """Get the last recorded clock skew offset in seconds."""
        if self._last_skew_result is None:
            return None
        return self._last_skew_result.offset_seconds


# Global monitor instance for background jobs
_job_skew_monitor: ClockSkewMonitor | None = None


def get_job_skew_monitor() -> ClockSkewMonitor:
    """Get the global clock skew monitor for background jobs."""
    global _job_skew_monitor
    if _job_skew_monitor is None:
        _job_skew_monitor = ClockSkewMonitor()
    return _job_skew_monitor
