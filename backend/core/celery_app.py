"""
Celery configuration for background task processing.

This module replaces APScheduler with Celery for:
- Persistent job queue with Redis broker
- Retry logic with exponential backoff
- Worker process isolation
- Monitoring via Flower dashboard

Migration from APScheduler:
- APScheduler runs in-process, loses jobs on restart
- Celery workers are separate processes with persistent queues
- Jobs are now durable across backend restarts
"""

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Use separate Redis databases for broker and results
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL.replace("/0", "/1"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL.replace("/0", "/2"))

# Create Celery application
celery_app = Celery(
    "edustream",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks.booking_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completion (durability)
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    worker_prefetch_multiplier=1,  # Fetch one task at a time

    # Retry settings with exponential backoff
    task_default_retry_delay=60,  # 1 minute initial retry delay
    task_max_retries=5,

    # Result settings
    result_expires=3600,  # Results expire after 1 hour

    # Task routing (optional, for future scaling)
    task_routes={
        "tasks.booking_tasks.*": {"queue": "bookings"},
    },

    # Worker settings
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,

    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        "expire-booking-requests": {
            "task": "tasks.booking_tasks.expire_requests",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "bookings"},
        },
        "start-scheduled-sessions": {
            "task": "tasks.booking_tasks.start_sessions",
            "schedule": 60.0,  # Every 1 minute
            "options": {"queue": "bookings"},
        },
        "end-active-sessions": {
            "task": "tasks.booking_tasks.end_sessions",
            "schedule": 60.0,  # Every 1 minute
            "options": {"queue": "bookings"},
        },
    },

    # Beat scheduler persistence
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="/tmp/celerybeat-schedule",
)


def get_celery_app() -> Celery:
    """Get the Celery application instance."""
    return celery_app


# Task retry configuration helper
class TaskRetryConfig:
    """Standard retry configuration for booking tasks."""

    # Exponential backoff: 60s, 120s, 240s, 480s, 960s
    BACKOFF_BASE = 60
    BACKOFF_MULTIPLIER = 2
    MAX_RETRIES = 5

    @classmethod
    def get_countdown(cls, retry_count: int) -> int:
        """Calculate retry delay with exponential backoff."""
        return cls.BACKOFF_BASE * (cls.BACKOFF_MULTIPLIER ** retry_count)


logger.info(
    "Celery configured with broker=%s, result_backend=%s",
    CELERY_BROKER_URL.replace(REDIS_URL.split("@")[0] if "@" in REDIS_URL else "", "***"),
    CELERY_RESULT_BACKEND.replace(REDIS_URL.split("@")[0] if "@" in REDIS_URL else "", "***"),
)
