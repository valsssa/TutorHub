"""
APScheduler setup for background jobs.

Handles auto-transition jobs for booking state management:
- expire_requests: REQUESTED → EXPIRED (every 5 min, 24h timeout)
- start_sessions: SCHEDULED → ACTIVE (every 1 min, at start_time)
- end_sessions: ACTIVE → ENDED (every 1 min, at end_time + grace)
"""

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


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
    from modules.bookings.jobs import end_sessions, expire_requests, start_sessions

    # Add jobs with appropriate intervals
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

    logger.info("Scheduler configured with booking auto-transition jobs")
    return scheduler


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    global scheduler

    if scheduler is None:
        scheduler = init_scheduler()

    if not scheduler.running:
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
