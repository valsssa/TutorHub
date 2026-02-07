"""
Response Time Tracking Service

Tracks tutor response times to booking requests for:
- Individual tutor metrics
- Platform-wide analytics
- Admin dashboard reporting
"""

import logging
from datetime import datetime, timedelta

from core.datetime_utils import utc_now

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Booking, TutorMetrics, TutorResponseLog

logger = logging.getLogger(__name__)


class ResponseTrackingService:
    """Service for tracking and calculating tutor response times."""

    def __init__(self, db: Session):
        self.db = db

    def log_booking_created(self, booking: Booking) -> TutorResponseLog | None:
        """Log when a booking is created (start of response time tracking)."""
        if not booking.tutor_profile_id or not booking.student_id:
            return None

        log_entry = TutorResponseLog(
            booking_id=booking.id,
            tutor_profile_id=booking.tutor_profile_id,
            student_id=booking.student_id,
            booking_created_at=booking.created_at or utc_now(),
        )
        self.db.add(log_entry)
        self.db.flush()

        logger.debug(f"Created response log for booking {booking.id}")
        return log_entry

    def log_tutor_response(
        self,
        booking: Booking,
        response_action: str,  # 'confirmed', 'cancelled', 'ignored', 'auto_confirmed'
    ) -> TutorResponseLog | None:
        """Log when a tutor responds to a booking request."""
        if not booking.tutor_profile_id:
            return None

        # Find existing log entry
        log_entry = (
            self.db.query(TutorResponseLog)
            .filter(
                TutorResponseLog.booking_id == booking.id,
                TutorResponseLog.tutor_responded_at.is_(None),
            )
            .first()
        )

        now = utc_now()

        if log_entry:
            log_entry.tutor_responded_at = now
            log_entry.response_action = response_action
            # Calculate response time in minutes
            if log_entry.booking_created_at:
                delta = now - log_entry.booking_created_at
                log_entry.response_time_minutes = int(delta.total_seconds() / 60)
        else:
            # Create new entry if one doesn't exist
            log_entry = TutorResponseLog(
                booking_id=booking.id,
                tutor_profile_id=booking.tutor_profile_id,
                student_id=booking.student_id,
                booking_created_at=booking.created_at or now,
                tutor_responded_at=now,
                response_action=response_action,
                response_time_minutes=(
                    int((now - booking.created_at).total_seconds() / 60) if booking.created_at else 0
                ),
            )
            self.db.add(log_entry)

        self.db.flush()

        logger.info(
            f"Logged tutor response for booking {booking.id}: {response_action} "
            f"(response time: {log_entry.response_time_minutes} minutes)"
        )

        # Update tutor metrics asynchronously (for now, just update)
        self._update_tutor_metrics(booking.tutor_profile_id)

        return log_entry

    def _update_tutor_metrics(self, tutor_profile_id: int) -> None:
        """Update tutor's aggregate response metrics."""
        # Calculate average response time for this tutor
        avg_response = (
            self.db.query(func.avg(TutorResponseLog.response_time_minutes))
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.response_time_minutes.isnot(None),
            )
            .scalar()
        )

        # Calculate 24h response rate
        cutoff = utc_now() - timedelta(hours=24)
        total_24h = (
            self.db.query(TutorResponseLog)
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.booking_created_at >= cutoff,
            )
            .count()
        )
        responded_24h = (
            self.db.query(TutorResponseLog)
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.booking_created_at >= cutoff,
                TutorResponseLog.tutor_responded_at.isnot(None),
            )
            .count()
        )
        response_rate_24h = (responded_24h / total_24h * 100) if total_24h > 0 else 100

        # Get or create metrics record
        metrics = (
            self.db.query(TutorMetrics).filter(TutorMetrics.tutor_profile_id == tutor_profile_id).first()
        )

        if metrics:
            metrics.avg_response_time_minutes = int(avg_response or 0)
            metrics.response_rate_24h = round(response_rate_24h, 2)
            metrics.updated_at = utc_now()
            metrics.last_calculated = utc_now()
        else:
            metrics = TutorMetrics(
                tutor_profile_id=tutor_profile_id,
                avg_response_time_minutes=int(avg_response or 0),
                response_rate_24h=round(response_rate_24h, 2),
            )
            self.db.add(metrics)

        self.db.flush()

    def get_platform_average_response_time(self) -> float | None:
        """Get platform-wide average response time in hours."""
        result = (
            self.db.query(func.avg(TutorResponseLog.response_time_minutes))
            .filter(TutorResponseLog.response_time_minutes.isnot(None))
            .scalar()
        )

        if result is None:
            return None

        # Convert minutes to hours
        return round(float(result) / 60, 2)

    def get_tutor_response_stats(self, tutor_profile_id: int) -> dict:
        """Get response statistics for a specific tutor."""
        # Average response time
        avg_response = (
            self.db.query(func.avg(TutorResponseLog.response_time_minutes))
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.response_time_minutes.isnot(None),
            )
            .scalar()
        )

        # Total responses
        total_responses = (
            self.db.query(TutorResponseLog)
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.tutor_responded_at.isnot(None),
            )
            .count()
        )

        # Response breakdown by action
        action_counts = dict(
            self.db.query(TutorResponseLog.response_action, func.count(TutorResponseLog.id))
            .filter(
                TutorResponseLog.tutor_profile_id == tutor_profile_id,
                TutorResponseLog.response_action.isnot(None),
            )
            .group_by(TutorResponseLog.response_action)
            .all()
        )

        return {
            "avg_response_time_minutes": int(avg_response or 0),
            "avg_response_time_hours": round(float(avg_response or 0) / 60, 2),
            "total_responses": total_responses,
            "confirmed": action_counts.get("confirmed", 0),
            "cancelled": action_counts.get("cancelled", 0),
            "auto_confirmed": action_counts.get("auto_confirmed", 0),
            "ignored": action_counts.get("ignored", 0),
        }


def get_response_tracking_service(db: Session) -> ResponseTrackingService:
    """Factory function for response tracking service."""
    return ResponseTrackingService(db)
