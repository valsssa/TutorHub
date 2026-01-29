"""
Celery tasks package.

This package contains all Celery task definitions for background processing.

Modules:
    booking_tasks: Booking state machine auto-transition tasks
        - expire_requests: REQUESTED -> EXPIRED (every 5 min, 24h timeout)
        - start_sessions: SCHEDULED -> ACTIVE (every 1 min, at start_time)
        - end_sessions: ACTIVE -> ENDED (every 1 min, at end_time + grace)

Migration Note:
    These tasks replace the APScheduler jobs in modules/bookings/jobs.py.
    The APScheduler implementation is deprecated but retained for incremental migration.
"""

from tasks.booking_tasks import end_sessions, expire_requests, start_sessions

__all__ = [
    "expire_requests",
    "start_sessions",
    "end_sessions",
]
