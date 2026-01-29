"""
Background jobs for booking auto-transitions.

Jobs run on schedule to automatically transition booking states:
- expire_requests: REQUESTED → EXPIRED (every 5 min, 24h timeout)
- start_sessions: SCHEDULED → ACTIVE (every 1 min, at start_time)
- end_sessions: ACTIVE → ENDED (every 1 min, at end_time + grace)
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_

from database import SessionLocal
from models import Booking
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import SessionOutcome, SessionState

logger = logging.getLogger(__name__)

# Configuration
REQUEST_EXPIRY_HOURS = 24  # Requests expire after 24 hours
SESSION_END_GRACE_MINUTES = 5  # Grace period after end_time before auto-ending


async def expire_requests() -> None:
    """
    Expire booking requests that have been pending for more than 24 hours.

    Runs every 5 minutes.
    Transitions: REQUESTED → EXPIRED
    """
    logger.debug("Running expire_requests job")

    db = SessionLocal()
    try:
        cutoff_time = datetime.now(UTC) - timedelta(hours=REQUEST_EXPIRY_HOURS)

        # Find all REQUESTED bookings created before cutoff
        expired_bookings = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.session_state == SessionState.REQUESTED.value,
                    Booking.created_at < cutoff_time,
                )
            )
            .all()
        )

        count = 0
        for booking in expired_bookings:
            result = BookingStateMachine.expire_booking(booking)
            if result.success:
                booking.updated_at = datetime.now(UTC)
                count += 1
            else:
                logger.warning(
                    "Failed to expire booking %d: %s",
                    booking.id,
                    result.error_message,
                )

        if count > 0:
            db.commit()
            logger.info("Expired %d booking requests", count)

    except Exception as e:
        logger.error("Error in expire_requests job: %s", e)
        db.rollback()
    finally:
        db.close()


async def start_sessions() -> None:
    """
    Start scheduled sessions that have reached their start_time.

    Runs every 1 minute.
    Transitions: SCHEDULED → ACTIVE
    """
    logger.debug("Running start_sessions job")

    db = SessionLocal()
    try:
        now = datetime.now(UTC)

        # Find all SCHEDULED bookings where start_time has passed
        sessions_to_start = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.session_state == SessionState.SCHEDULED.value,
                    Booking.start_time <= now,
                )
            )
            .all()
        )

        count = 0
        for booking in sessions_to_start:
            result = BookingStateMachine.start_session(booking)
            if result.success:
                booking.updated_at = datetime.now(UTC)
                count += 1
            else:
                logger.warning(
                    "Failed to start session %d: %s",
                    booking.id,
                    result.error_message,
                )

        if count > 0:
            db.commit()
            logger.info("Started %d sessions", count)

    except Exception as e:
        logger.error("Error in start_sessions job: %s", e)
        db.rollback()
    finally:
        db.close()


async def end_sessions() -> None:
    """
    End active sessions that have passed their end_time plus grace period.

    Runs every 1 minute.
    Transitions: ACTIVE → ENDED
    """
    logger.debug("Running end_sessions job")

    db = SessionLocal()
    try:
        now = datetime.now(UTC)
        grace_cutoff = now - timedelta(minutes=SESSION_END_GRACE_MINUTES)

        # Find all ACTIVE bookings where end_time + grace has passed
        sessions_to_end = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.session_state == SessionState.ACTIVE.value,
                    Booking.end_time <= grace_cutoff,
                )
            )
            .all()
        )

        count = 0
        for booking in sessions_to_end:
            # Default to COMPLETED outcome for auto-ended sessions
            result = BookingStateMachine.end_session(booking, SessionOutcome.COMPLETED)
            if result.success:
                booking.updated_at = datetime.now(UTC)
                count += 1
            else:
                logger.warning(
                    "Failed to end session %d: %s",
                    booking.id,
                    result.error_message,
                )

        if count > 0:
            db.commit()
            logger.info("Ended %d sessions", count)

    except Exception as e:
        logger.error("Error in end_sessions job: %s", e)
        db.rollback()
    finally:
        db.close()
