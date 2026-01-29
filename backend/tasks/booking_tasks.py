"""
Celery tasks for booking auto-transitions.

Tasks run on schedule to automatically transition booking states:
- expire_requests: REQUESTED -> EXPIRED (every 5 min, 24h timeout)
- start_sessions: SCHEDULED -> ACTIVE (every 1 min, at start_time)
- end_sessions: ACTIVE -> ENDED (every 1 min, at end_time + grace)

Race Condition Prevention:
- Uses SELECT FOR UPDATE to acquire row-level locks before state transitions
- Transitions are idempotent, so concurrent updates don't cause errors
- Each booking is processed in its own transaction to minimize lock contention

Clock Skew Handling:
- Uses database server time for critical time comparisons
- Periodically checks and logs clock skew between app and database servers
- Ensures consistent timing even if app server clock drifts

Migration Note:
    This module migrates the APScheduler jobs from modules/bookings/jobs.py
    to Celery tasks for improved reliability and monitoring.
"""

import logging
from datetime import timedelta

from celery import shared_task
from sqlalchemy import and_
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Configuration (same as original APScheduler jobs)
REQUEST_EXPIRY_HOURS = 24  # Requests expire after 24 hours
SESSION_END_GRACE_MINUTES = 5  # Grace period after end_time before auto-ending


@shared_task(
    bind=True,
    name="tasks.booking_tasks.expire_requests",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def expire_requests(self) -> dict:
    """
    Expire booking requests that have been pending for more than 24 hours.

    Runs every 5 minutes via Celery Beat.
    Transitions: REQUESTED -> EXPIRED

    Uses row-level locking to prevent race conditions with concurrent
    tutor accepts/declines.

    Returns:
        dict: Summary of processed bookings
    """
    # Import inside task to avoid circular imports and ensure fresh DB session
    from core.clock_skew import get_db_time, get_job_skew_monitor
    from database import SessionLocal
    from models import Booking
    from modules.bookings.domain.state_machine import BookingStateMachine
    from modules.bookings.domain.status import SessionState

    logger.debug("Running expire_requests task")

    db = SessionLocal()
    result = {"expired": 0, "skipped": 0, "errors": 0}

    try:
        # Check clock skew periodically and use database time for consistency
        skew_monitor = get_job_skew_monitor()
        skew_monitor.check_and_warn(db)

        # Use database time for critical time comparisons to avoid clock skew issues
        now = get_db_time(db)
        cutoff_time = now - timedelta(hours=REQUEST_EXPIRY_HOURS)

        # Find IDs of REQUESTED bookings created before cutoff
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

        for (booking_id,) in booking_ids:
            try:
                # Lock and fetch the booking with SELECT FOR UPDATE NOWAIT
                booking = BookingStateMachine.get_booking_with_lock(
                    db, booking_id, nowait=True
                )

                if not booking:
                    continue

                # Idempotent transition - handles race where tutor accepted
                transition_result = BookingStateMachine.expire_booking(booking)
                if transition_result.success:
                    if transition_result.already_in_target_state:
                        result["skipped"] += 1
                    else:
                        result["expired"] += 1
                    db.commit()
                else:
                    logger.warning(
                        "Failed to expire booking %d: %s",
                        booking_id,
                        transition_result.error_message,
                    )
                    result["errors"] += 1
                    db.rollback()

            except OperationalError:
                # Lock could not be acquired (row is being modified by API)
                logger.debug(
                    "Skipping booking %d - locked by another transaction",
                    booking_id,
                )
                db.rollback()
                continue

        if result["expired"] > 0 or result["skipped"] > 0:
            logger.info(
                "Expire task: expired %d bookings, skipped %d (already transitioned)",
                result["expired"],
                result["skipped"],
            )

    except Exception as e:
        logger.error("Error in expire_requests task: %s", e)
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()

    return result


@shared_task(
    bind=True,
    name="tasks.booking_tasks.start_sessions",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def start_sessions(self) -> dict:
    """
    Start scheduled sessions that have reached their start_time.

    Runs every 1 minute via Celery Beat.
    Transitions: SCHEDULED -> ACTIVE

    Uses row-level locking to prevent race conditions.

    Returns:
        dict: Summary of processed sessions
    """
    from core.clock_skew import get_db_time, get_job_skew_monitor
    from database import SessionLocal
    from models import Booking
    from modules.bookings.domain.state_machine import BookingStateMachine
    from modules.bookings.domain.status import SessionState

    logger.debug("Running start_sessions task")

    db = SessionLocal()
    result = {"started": 0, "skipped": 0, "errors": 0}

    try:
        # Check clock skew periodically and use database time for consistency
        skew_monitor = get_job_skew_monitor()
        skew_monitor.check_and_warn(db)

        # Use database time for critical time comparisons to avoid clock skew issues
        now = get_db_time(db)

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

        for (booking_id,) in booking_ids:
            try:
                # Lock and fetch the booking
                booking = BookingStateMachine.get_booking_with_lock(
                    db, booking_id, nowait=True
                )

                if not booking:
                    continue

                transition_result = BookingStateMachine.start_session(booking)
                if transition_result.success:
                    if transition_result.already_in_target_state:
                        result["skipped"] += 1
                    else:
                        result["started"] += 1
                    db.commit()
                else:
                    logger.warning(
                        "Failed to start session %d: %s",
                        booking_id,
                        transition_result.error_message,
                    )
                    result["errors"] += 1
                    db.rollback()

            except OperationalError:
                logger.debug(
                    "Skipping session start for booking %d - locked",
                    booking_id,
                )
                db.rollback()
                continue

        if result["started"] > 0 or result["skipped"] > 0:
            logger.info(
                "Start sessions task: started %d sessions, skipped %d",
                result["started"],
                result["skipped"],
            )

    except Exception as e:
        logger.error("Error in start_sessions task: %s", e)
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()

    return result


@shared_task(
    bind=True,
    name="tasks.booking_tasks.end_sessions",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def end_sessions(self) -> dict:
    """
    End active sessions that have passed their end_time plus grace period.

    Runs every 1 minute via Celery Beat.
    Transitions: ACTIVE -> ENDED

    Uses row-level locking to prevent race conditions with manual
    no-show marking or other session end operations.

    Returns:
        dict: Summary of processed sessions
    """
    from core.clock_skew import get_db_time, get_job_skew_monitor
    from database import SessionLocal
    from models import Booking
    from modules.bookings.domain.state_machine import BookingStateMachine
    from modules.bookings.domain.status import SessionOutcome, SessionState

    logger.debug("Running end_sessions task")

    db = SessionLocal()
    result = {"ended": 0, "skipped": 0, "errors": 0}

    try:
        # Check clock skew periodically and use database time for consistency
        skew_monitor = get_job_skew_monitor()
        skew_monitor.check_and_warn(db)

        # Use database time for critical time comparisons to avoid clock skew issues
        now = get_db_time(db)
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

        for (booking_id,) in booking_ids:
            try:
                # Lock and fetch the booking
                booking = BookingStateMachine.get_booking_with_lock(
                    db, booking_id, nowait=True
                )

                if not booking:
                    continue

                # Default to COMPLETED outcome for auto-ended sessions
                transition_result = BookingStateMachine.end_session(
                    booking, SessionOutcome.COMPLETED
                )
                if transition_result.success:
                    if transition_result.already_in_target_state:
                        result["skipped"] += 1
                    else:
                        result["ended"] += 1
                    db.commit()
                else:
                    logger.warning(
                        "Failed to end session %d: %s",
                        booking_id,
                        transition_result.error_message,
                    )
                    result["errors"] += 1
                    db.rollback()

            except OperationalError:
                logger.debug(
                    "Skipping session end for booking %d - locked",
                    booking_id,
                )
                db.rollback()
                continue

        if result["ended"] > 0 or result["skipped"] > 0:
            logger.info(
                "End sessions task: ended %d sessions, skipped %d",
                result["ended"],
                result["skipped"],
            )

    except Exception as e:
        logger.error("Error in end_sessions task: %s", e)
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()

    return result
