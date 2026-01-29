"""
APScheduler setup for background jobs.

DEPRECATION NOTICE:
    This module is deprecated in favor of Celery workers.
    See backend/core/celery_app.py and backend/tasks/booking_tasks.py.

    APScheduler limitations that led to migration:
    - Jobs run in-process with backend, lost if backend restarts
    - No persistent job queue
    - No retry logic with exponential backoff
    - No monitoring dashboard

    The APScheduler code is retained for:
    - Backwards compatibility during incremental migration
    - Fallback if Celery infrastructure is not available
    - Reference implementation

    To switch to Celery:
    1. Ensure celery-worker and celery-beat services are running
    2. Comment out lifespan_scheduler usage in main.py
    3. Jobs will run via Celery Beat schedule

    Migration timeline:
    - Phase 1 (current): Celery infrastructure added, APScheduler still active
    - Phase 2: Switch to Celery, APScheduler disabled
    - Phase 3: Remove APScheduler code entirely

Handles auto-transition jobs for booking state management:
- expire_requests: REQUESTED -> EXPIRED (every 5 min, 24h timeout)
- start_sessions: SCHEDULED -> ACTIVE (every 1 min, at start_time)
- end_sessions: ACTIVE -> ENDED (every 1 min, at end_time + grace)

Handles package management jobs:
- send_package_expiry_warnings: Send warning notifications (daily)
- mark_expired_packages: Mark expired packages (hourly)

Multi-Instance Safety:
    The `max_instances=1` setting only prevents overlap within a single process.
    When running multiple backend pods/instances, jobs can still overlap.

    This is now handled by Redis distributed locks in the job functions themselves
    (see modules/bookings/jobs.py and core/distributed_lock.py). Jobs acquire a
    cluster-wide lock before execution and skip if the lock is already held.
"""

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.clock_skew import check_clock_skew

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Clock skew configuration
CLOCK_SKEW_CHECK_INTERVAL_MINUTES = 5
CLOCK_SKEW_THRESHOLD_SECONDS = 5

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def _check_clock_skew_job() -> None:
    """
    Periodic job to check clock skew between app and database servers.

    Logs warnings if skew exceeds threshold to help detect time drift issues
    that could affect booking state transitions.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        result = check_clock_skew(db, threshold_seconds=CLOCK_SKEW_THRESHOLD_SECONDS)
        if result.is_within_threshold:
            logger.debug(
                "Clock skew check: %.2f seconds (within %ds threshold)",
                result.offset_seconds,
                CLOCK_SKEW_THRESHOLD_SECONDS,
            )
    except Exception as e:
        logger.error("Error checking clock skew: %s", e)
    finally:
        db.close()


def _startup_clock_skew_check() -> None:
    """
    Perform a clock skew check at scheduler startup.

    Issues a warning if significant drift is detected so operators
    can investigate before it affects job timing.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        result = check_clock_skew(db, threshold_seconds=CLOCK_SKEW_THRESHOLD_SECONDS)
        if result.is_within_threshold:
            logger.info(
                "Startup clock skew check: %.2f seconds offset (OK)",
                result.offset_seconds,
            )
        else:
            logger.warning(
                "Startup clock skew check: SIGNIFICANT DRIFT detected! "
                "App server is %.2f seconds %s database server. "
                "This may affect booking job timing accuracy.",
                abs(result.offset_seconds),
                "ahead of" if result.offset_seconds > 0 else "behind",
            )
    except Exception as e:
        logger.error("Error during startup clock skew check: %s", e)
    finally:
        db.close()


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


def init_scheduler() -> AsyncIOScheduler:
    """Initialize and configure the scheduler with booking jobs."""
    global scheduler

    if scheduler is not None and scheduler.running:
        logger.info("Scheduler already running")
        return scheduler

    scheduler = AsyncIOScheduler()

    # Import job functions here to avoid circular imports
    from modules.bookings.jobs import (
        end_sessions,
        expire_requests,
        retry_zoom_meetings,
        start_sessions,
    )
    from modules.packages.jobs import (
        mark_expired_packages,
        send_package_expiry_warnings,
    )

    # Add booking jobs with appropriate intervals
    scheduler.add_job(
        expire_requests,
        trigger=IntervalTrigger(minutes=5),
        id="expire_requests",
        name="Expire booking requests after 24h",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        start_sessions,
        trigger=IntervalTrigger(minutes=1),
        id="start_sessions",
        name="Start scheduled sessions at start_time",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        end_sessions,
        trigger=IntervalTrigger(minutes=1),
        id="end_sessions",
        name="End active sessions at end_time + grace",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        retry_zoom_meetings,
        trigger=IntervalTrigger(minutes=5),
        id="retry_zoom_meetings",
        name="Retry failed Zoom meeting creation",
        replace_existing=True,
        max_instances=1,
    )

    # Add package management jobs
    scheduler.add_job(
        send_package_expiry_warnings,
        trigger=IntervalTrigger(hours=24),
        id="send_package_expiry_warnings",
        name="Send warning notifications for expiring packages",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        mark_expired_packages,
        trigger=IntervalTrigger(hours=1),
        id="mark_expired_packages",
        name="Mark expired packages as expired status",
        replace_existing=True,
        max_instances=1,
    )

    # Add clock skew monitoring job
    scheduler.add_job(
        _check_clock_skew_job,
        trigger=IntervalTrigger(minutes=CLOCK_SKEW_CHECK_INTERVAL_MINUTES),
        id="check_clock_skew",
        name="Monitor clock skew between app and database servers",
        replace_existing=True,
        max_instances=1,
    )

    logger.info("Scheduler configured with booking, package management, and monitoring jobs")
    return scheduler


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    global scheduler

    if scheduler is None:
        scheduler = init_scheduler()

    if not scheduler.running:
        # Perform startup clock skew check before starting jobs
        _startup_clock_skew_check()
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the scheduler."""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


@asynccontextmanager
async def lifespan_scheduler(app: "FastAPI"):
    """
    FastAPI lifespan context manager for scheduler.

    Usage in main.py:
        from core.scheduler import lifespan_scheduler

        app = FastAPI(lifespan=lifespan_scheduler)
    """
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
