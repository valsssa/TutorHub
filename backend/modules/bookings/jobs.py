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
from datetime import datetime, timedelta

from core.datetime_utils import utc_now

from sqlalchemy import and_
from sqlalchemy.exc import OperationalError

from core.clock_skew import get_db_time, get_job_skew_monitor
from core.distributed_lock import distributed_lock
from core.tracing import trace_background_job
from database import SessionLocal
from models import Booking
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import SessionOutcome, SessionState

logger = logging.getLogger(__name__)

# Configuration
REQUEST_EXPIRY_HOURS = 24  # Requests expire after 24 hours
SESSION_START_BUFFER_MINUTES = 2  # Buffer before auto-starting (prevents cancel race condition)
SESSION_END_GRACE_MINUTES = 5  # Grace period after end_time before auto-ending
ZOOM_RETRY_BATCH_SIZE = 10  # Maximum bookings to process per retry run
ZOOM_RETRY_MAX_ATTEMPTS = 5  # Stop retrying after this many job runs

# Distributed lock timeouts (should be longer than expected job duration)
EXPIRE_REQUESTS_LOCK_TIMEOUT = 300  # 5 minutes
START_SESSIONS_LOCK_TIMEOUT = 120  # 2 minutes
END_SESSIONS_LOCK_TIMEOUT = 120  # 2 minutes
RETRY_ZOOM_MEETINGS_LOCK_TIMEOUT = 180  # 3 minutes


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
                # Check clock skew periodically and use database time for consistency
                skew_monitor = get_job_skew_monitor()
                skew_monitor.check_and_warn(db)

                # Use database time for critical time comparisons to avoid clock skew issues
                now = get_db_time(db)
                cutoff_time = now - timedelta(hours=REQUEST_EXPIRY_HOURS)

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

    Race Condition Prevention:
    - Adds a 2-minute buffer before auto-starting sessions
    - This grace period allows students to cancel right up until the start time
    - Without the buffer, a student could pass the is_cancellable() check but have
      the cancel fail because the job transitioned the booking to ACTIVE
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
                # Check clock skew periodically and use database time for consistency
                skew_monitor = get_job_skew_monitor()
                skew_monitor.check_and_warn(db)

                # Use database time for critical time comparisons to avoid clock skew issues
                now = get_db_time(db)

                # Find IDs of SCHEDULED bookings where start_time + buffer has passed
                # The buffer prevents race conditions with cancellation requests:
                # - Student checks is_cancellable() at 10:00:00 (passes, booking is SCHEDULED)
                # - Job runs at 10:00:01 and transitions to ACTIVE
                # - Student's cancel request fails because booking is now ACTIVE
                # With a 2-minute buffer, the job waits until 10:02:00 to transition,
                # giving users a grace period to complete their cancellation
                start_cutoff = now - timedelta(minutes=SESSION_START_BUFFER_MINUTES)
                booking_ids = (
                    db.query(Booking.id)
                    .filter(
                        and_(
                            Booking.session_state == SessionState.SCHEDULED.value,
                            Booking.start_time <= start_cutoff,
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


def _determine_session_outcome_from_attendance(booking: Booking) -> SessionOutcome:
    """
    Determine the appropriate session outcome based on attendance tracking.

    This function examines the tutor_joined_at and student_joined_at timestamps
    to determine how the session should be categorized:

    - Neither joined -> NOT_HELD (session didn't happen, void payment)
    - Only student joined -> NO_SHOW_TUTOR (tutor absent, refund student)
    - Only tutor joined -> NO_SHOW_STUDENT (student absent, tutor earns payment)
    - Both joined -> COMPLETED (session happened normally)

    Args:
        booking: The booking to evaluate

    Returns:
        SessionOutcome: The appropriate outcome based on attendance
    """
    tutor_joined = booking.tutor_joined_at is not None
    student_joined = booking.student_joined_at is not None

    if not tutor_joined and not student_joined:
        # Neither party joined - session didn't happen
        return SessionOutcome.NOT_HELD
    elif not tutor_joined:
        # Student was present but tutor didn't show
        return SessionOutcome.NO_SHOW_TUTOR
    elif not student_joined:
        # Tutor was present but student didn't show
        return SessionOutcome.NO_SHOW_STUDENT
    else:
        # Both parties joined - successful session
        return SessionOutcome.COMPLETED


async def end_sessions() -> None:
    """
    End active sessions that have passed their end_time plus grace period.

    Runs every 1 minute.
    Transitions: ACTIVE -> ENDED

    Attendance-Based Outcome Determination:
    The outcome is determined based on whether participants actually joined:
    - Neither joined -> NOT_HELD (void payment, flag for review)
    - Only student joined -> NO_SHOW_TUTOR (refund student)
    - Only tutor joined -> NO_SHOW_STUDENT (tutor earns payment)
    - Both joined -> COMPLETED (normal completion, capture payment)

    Payment Handling:
    - For pay-per-session bookings (package_id is NULL): captures the pre-authorized
      payment. The booking's original payment method is preserved.
    - For package bookings (package_id is set): the package credit was already
      deducted when the booking was created. No additional payment action needed.

    IMPORTANT: This job does NOT retroactively apply packages to sessions. If a
    student purchases a package during an active session, that session continues
    to use its original payment method (pay-per-session). The package only applies
    to future bookings created after the purchase.

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

                count = 0
                skipped = 0
                not_held_count = 0
                no_show_tutor_count = 0
                no_show_student_count = 0

                for (booking_id,) in booking_ids:
                    try:
                        # Lock and fetch the booking
                        booking = BookingStateMachine.get_booking_with_lock(
                            db, booking_id, nowait=True
                        )

                        if not booking:
                            continue

                        # Determine outcome based on attendance tracking
                        outcome = _determine_session_outcome_from_attendance(booking)

                        # Log special cases for monitoring
                        if outcome == SessionOutcome.NOT_HELD:
                            logger.warning(
                                "Session %d: Neither party joined - marking as NOT_HELD",
                                booking_id,
                            )
                            not_held_count += 1
                        elif outcome == SessionOutcome.NO_SHOW_TUTOR:
                            logger.info(
                                "Session %d: Tutor did not join (attendance-based) - "
                                "marking as NO_SHOW_TUTOR",
                                booking_id,
                            )
                            no_show_tutor_count += 1
                        elif outcome == SessionOutcome.NO_SHOW_STUDENT:
                            logger.info(
                                "Session %d: Student did not join (attendance-based) - "
                                "marking as NO_SHOW_STUDENT",
                                booking_id,
                            )
                            no_show_student_count += 1

                        result = BookingStateMachine.end_session(booking, outcome)

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
                        "End sessions job: ended %d sessions (completed: %d, "
                        "not_held: %d, no_show_tutor: %d, no_show_student: %d), "
                        "skipped %d",
                        count,
                        count - not_held_count - no_show_tutor_count - no_show_student_count,
                        not_held_count,
                        no_show_tutor_count,
                        no_show_student_count,
                        skipped,
                    )

            except Exception as e:
                logger.error("Error in end_sessions job: %s", e)
                db.rollback()
            finally:
                db.close()


async def retry_zoom_meetings() -> None:
    """
    Retry creating Zoom meetings for bookings that failed during confirmation.

    Runs every 5 minutes.
    Processes bookings with zoom_meeting_pending=True that are still in SCHEDULED or ACTIVE state.

    Uses row-level locking to prevent race conditions.
    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:retry_zoom_meetings", timeout=RETRY_ZOOM_MEETINGS_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "retry_zoom_meetings job already running on another instance, skipping"
            )
            return

        with trace_background_job("retry_zoom_meetings", interval="5min"):
            logger.debug("Running retry_zoom_meetings job")

            db = SessionLocal()
            try:
                from modules.integrations.zoom_router import ZoomError, zoom_client

                # Check clock skew periodically and use database time for consistency
                skew_monitor = get_job_skew_monitor()
                skew_monitor.check_and_warn(db)

                # Use database time for critical time comparisons to avoid clock skew issues
                now = get_db_time(db)

                # Find bookings needing Zoom meeting retry
                # Only process SCHEDULED or ACTIVE bookings (not past sessions)
                booking_ids = (
                    db.query(Booking.id)
                    .filter(
                        and_(
                            Booking.zoom_meeting_pending == True,  # noqa: E712
                            Booking.session_state.in_([
                                SessionState.SCHEDULED.value,
                                SessionState.ACTIVE.value,
                            ]),
                            Booking.start_time > now - timedelta(hours=2),  # Skip old sessions
                        )
                    )
                    .limit(ZOOM_RETRY_BATCH_SIZE)
                    .all()
                )

                if not booking_ids:
                    return

                success_count = 0
                failure_count = 0

                for (booking_id,) in booking_ids:
                    try:
                        # Lock and fetch the booking
                        booking = BookingStateMachine.get_booking_with_lock(
                            db, booking_id, nowait=True
                        )

                        if not booking:
                            continue

                        # Skip if no longer pending (processed by another instance or API)
                        if not booking.zoom_meeting_pending:
                            continue

                        # Skip if session already ended or cancelled
                        if booking.session_state not in [
                            SessionState.SCHEDULED.value,
                            SessionState.ACTIVE.value,
                        ]:
                            booking.zoom_meeting_pending = False
                            db.commit()
                            continue

                        # Build meeting topic
                        topic = f"EduStream: {booking.subject_name or 'Tutoring Session'}"
                        if booking.student_name:
                            topic += f" with {booking.student_name}"

                        duration_minutes = int(
                            (booking.end_time - booking.start_time).total_seconds() / 60
                        )

                        # Get tutor email for logging
                        tutor_email = None
                        if booking.tutor_profile and booking.tutor_profile.user:
                            tutor_email = booking.tutor_profile.user.email

                        # Get student email for logging
                        student_email = None
                        if booking.student:
                            student_email = booking.student.email

                        try:
                            meeting = await zoom_client.create_meeting(
                                topic=topic,
                                start_time=booking.start_time,
                                duration_minutes=duration_minutes,
                                tutor_email=tutor_email,
                                student_email=student_email,
                                max_retries=1,  # Fewer retries in batch job
                            )

                            # Update booking with Zoom meeting details
                            booking.join_url = meeting["join_url"]
                            booking.meeting_url = meeting.get("start_url")
                            booking.zoom_meeting_id = str(meeting["id"])
                            booking.zoom_meeting_pending = False
                            booking.updated_at = utc_now()

                            db.commit()
                            success_count += 1
                            logger.info(
                                "Retry succeeded: Created Zoom meeting %s for booking %d",
                                meeting["id"],
                                booking_id,
                            )

                        except ZoomError as e:
                            # Zoom still failing - leave pending for next retry
                            logger.warning(
                                "Retry failed for booking %d: %s",
                                booking_id,
                                e.message,
                            )
                            failure_count += 1
                            db.rollback()

                    except OperationalError:
                        # Lock could not be acquired
                        logger.debug(
                            "Skipping Zoom retry for booking %d - locked",
                            booking_id,
                        )
                        db.rollback()
                        continue

                    except Exception as e:
                        logger.error(
                            "Unexpected error retrying Zoom for booking %d: %s",
                            booking_id,
                            e,
                        )
                        db.rollback()
                        continue

                if success_count > 0 or failure_count > 0:
                    logger.info(
                        "Zoom retry job: succeeded %d, failed %d",
                        success_count,
                        failure_count,
                    )

            except Exception as e:
                logger.error("Error in retry_zoom_meetings job: %s", e)
                db.rollback()
            finally:
                db.close()
