"""
Background jobs for booking auto-transitions.

DEPRECATION NOTICE:
    This module is deprecated in favor of Celery tasks.
    See backend/tasks/booking_tasks.py for the Celery implementation.

    These async jobs are used by APScheduler (core/scheduler.py) which runs
    in-process with the backend. The new Celery implementation provides:
    - Persistent job queue (survives backend restarts)
    - Retry logic with exponential backoff
    - Worker process isolation
    - Monitoring via Flower dashboard

    This code is retained for backwards compatibility during the migration period.
    Once Celery is fully deployed, this module will be removed.

Jobs run on schedule to automatically transition booking states:
- expire_requests: REQUESTED -> EXPIRED (every 5 min, 24h timeout)
- start_sessions: SCHEDULED -> ACTIVE (every 1 min, at start_time)
- end_sessions: ACTIVE -> ENDED (every 1 min, at end_time + grace)

Race Condition Prevention:
- Uses SELECT FOR UPDATE to acquire row-level locks before state transitions
- Transitions are idempotent, so concurrent updates don't cause errors
- Each booking is processed in its own transaction to minimize lock contention

Multi-Instance Safety:
- Uses Redis distributed locks to prevent job overlap across server instances
- APScheduler's max_instances=1 only works per-process; distributed locks work cluster-wide
- Locks auto-expire to prevent deadlocks if a pod crashes during job execution
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.exc import OperationalError

from core.distributed_lock import distributed_lock
from core.tracing import trace_background_job
from database import SessionLocal
from models import Booking
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import SessionOutcome, SessionState

logger = logging.getLogger(__name__)

# Configuration
REQUEST_EXPIRY_HOURS = 24  # Requests expire after 24 hours
SESSION_END_GRACE_MINUTES = 5  # Grace period after end_time before auto-ending

# Distributed lock timeouts (should be longer than expected job duration)
EXPIRE_REQUESTS_LOCK_TIMEOUT = 300  # 5 minutes
START_SESSIONS_LOCK_TIMEOUT = 120  # 2 minutes
END_SESSIONS_LOCK_TIMEOUT = 120  # 2 minutes


async def expire_requests() -> None:
    """
    Expire booking requests that have been pending for more than 24 hours.

    Runs every 5 minutes.
    Transitions: REQUESTED -> EXPIRED

    Uses row-level locking to prevent race conditions with concurrent
    tutor accepts/declines.
    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:expire_requests", timeout=EXPIRE_REQUESTS_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "expire_requests job already running on another instance, skipping"
            )
            return

        with trace_background_job("expire_requests", interval="5min"):
            logger.debug("Running expire_requests job")

            db = SessionLocal()
            try:
                cutoff_time = datetime.now(UTC) - timedelta(hours=REQUEST_EXPIRY_HOURS)

                # Find IDs of REQUESTED bookings created before cutoff
                # We only fetch IDs first, then lock each one individually
                booking_ids = (
                    db.query(Booking.id)
                    .filter(
                        and_(
                            Booking.session_state == SessionState.REQUESTED.value,
                            Booking.created_at < cutoff_time,
                        )
                    )
                    .all()
                )

                count = 0
                skipped = 0
                for (booking_id,) in booking_ids:
                    try:
                        # Lock and fetch the booking with SELECT FOR UPDATE NOWAIT
                        # This prevents conflicts with concurrent API requests
                        booking = BookingStateMachine.get_booking_with_lock(
                            db, booking_id, nowait=True
                        )

                        if not booking:
                            continue

                        # Idempotent transition - handles race where tutor accepted
                        result = BookingStateMachine.expire_booking(booking)
                        if result.success:
                            if result.already_in_target_state:
                                skipped += 1
                            else:
                                count += 1
                            db.commit()
                        else:
                            logger.warning(
                                "Failed to expire booking %d: %s",
                                booking_id,
                                result.error_message,
                            )
                            db.rollback()

                    except OperationalError:
                        # Lock could not be acquired (row is being modified by API)
                        # Skip this booking, it will be processed in the next run
                        logger.debug(
                            "Skipping booking %d - locked by another transaction",
                            booking_id,
                        )
                        db.rollback()
                        continue

                if count > 0 or skipped > 0:
                    logger.info(
                        "Expire job: expired %d bookings, skipped %d (already transitioned)",
                        count,
                        skipped,
                    )

            except Exception as e:
                logger.error("Error in expire_requests job: %s", e)
                db.rollback()
            finally:
                db.close()


async def start_sessions() -> None:
    """
    Start scheduled sessions that have reached their start_time.

    Runs every 1 minute.
    Transitions: SCHEDULED -> ACTIVE

    Uses row-level locking to prevent race conditions.
    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:start_sessions", timeout=START_SESSIONS_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "start_sessions job already running on another instance, skipping"
            )
            return

        with trace_background_job("start_sessions", interval="1min"):
            logger.debug("Running start_sessions job")

            db = SessionLocal()
            try:
                now = datetime.now(UTC)

                # Find IDs of SCHEDULED bookings where start_time has passed
                booking_ids = (
                    db.query(Booking.id)
                    .filter(
                        and_(
                            Booking.session_state == SessionState.SCHEDULED.value,
                            Booking.start_time <= now,
                        )
                    )
                    .all()
                )

                count = 0
                skipped = 0
                for (booking_id,) in booking_ids:
                    try:
                        # Lock and fetch the booking
                        booking = BookingStateMachine.get_booking_with_lock(
                            db, booking_id, nowait=True
                        )

                        if not booking:
                            continue

                        result = BookingStateMachine.start_session(booking)
                        if result.success:
                            if result.already_in_target_state:
                                skipped += 1
                            else:
                                count += 1
                            db.commit()
                        else:
                            logger.warning(
                                "Failed to start session %d: %s",
                                booking_id,
                                result.error_message,
                            )
                            db.rollback()

                    except OperationalError:
                        logger.debug(
                            "Skipping session start for booking %d - locked",
                            booking_id,
                        )
                        db.rollback()
                        continue

                if count > 0 or skipped > 0:
                    logger.info(
                        "Start sessions job: started %d sessions, skipped %d",
                        count,
                        skipped,
                    )

            except Exception as e:
                logger.error("Error in start_sessions job: %s", e)
                db.rollback()
            finally:
                db.close()


async def end_sessions() -> None:
    """
    End active sessions that have passed their end_time plus grace period.

    Runs every 1 minute.
    Transitions: ACTIVE -> ENDED

    Uses row-level locking to prevent race conditions with manual
    no-show marking or other session end operations.
    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:end_sessions", timeout=END_SESSIONS_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "end_sessions job already running on another instance, skipping"
            )
            return

        with trace_background_job("end_sessions", interval="1min"):
            logger.debug("Running end_sessions job")

            db = SessionLocal()
            try:
                now = datetime.now(UTC)
                grace_cutoff = now - timedelta(minutes=SESSION_END_GRACE_MINUTES)

                # Find IDs of ACTIVE bookings where end_time + grace has passed
                booking_ids = (
                    db.query(Booking.id)
                    .filter(
                        and_(
                            Booking.session_state == SessionState.ACTIVE.value,
                            Booking.end_time <= grace_cutoff,
                        )
                    )
                    .all()
                )

                count = 0
                skipped = 0
                for (booking_id,) in booking_ids:
                    try:
                        # Lock and fetch the booking
                        booking = BookingStateMachine.get_booking_with_lock(
                            db, booking_id, nowait=True
                        )

                        if not booking:
                            continue

                        # Default to COMPLETED outcome for auto-ended sessions
                        result = BookingStateMachine.end_session(
                            booking, SessionOutcome.COMPLETED
                        )
                        if result.success:
                            if result.already_in_target_state:
                                skipped += 1
                            else:
                                count += 1
                            db.commit()
                        else:
                            logger.warning(
                                "Failed to end session %d: %s",
                                booking_id,
                                result.error_message,
                            )
                            db.rollback()

                    except OperationalError:
                        logger.debug(
                            "Skipping session end for booking %d - locked",
                            booking_id,
                        )
                        db.rollback()
                        continue

                if count > 0 or skipped > 0:
                    logger.info(
                        "End sessions job: ended %d sessions, skipped %d",
                        count,
                        skipped,
                    )

            except Exception as e:
                logger.error("Error in end_sessions job: %s", e)
                db.rollback()
            finally:
                db.close()
