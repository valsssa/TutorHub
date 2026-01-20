"""
Booking policy engine per booking_detail.md spec.
Implements cancellation rules, reschedule policies, and refund calculations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# ============================================================================
# Policy Decision Data Classes
# ============================================================================


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""

    allow: bool
    reason_code: str
    refund_cents: int = 0
    tutor_compensation_cents: int = 0
    apply_strike_to_tutor: bool = False
    restore_package_unit: bool = False
    message: str = ""


# ============================================================================
# Cancellation Policy
# ============================================================================


class CancellationPolicy:
    """Implements cancellation rules and refund logic."""

    # Policy constants (configurable)
    FREE_CANCEL_WINDOW_HOURS = 12
    TUTOR_CANCEL_PENALTY_CENTS = 500  # $5 compensation
    MINIMUM_GRACE_MINUTES = 10

    @classmethod
    def evaluate_student_cancellation(
        cls,
        booking_start_at: datetime,
        now: datetime,
        rate_cents: int,
        lesson_type: str,
        is_trial: bool,
        is_package: bool,
    ) -> PolicyDecision:
        """
        Evaluate student cancellation request.

        Rules:
        - >= 12h before: full refund
        - < 12h before: no refund (or partial if configured)
        - Already started: no refund
        - Trial lessons: same rules
        - Package: restore credit if >= 12h
        """
        time_until_start = booking_start_at - now

        # Already started or in the past
        if time_until_start.total_seconds() <= 0:
            return PolicyDecision(
                allow=False,
                reason_code="ALREADY_STARTED",
                message="Cannot cancel a session that has already started",
            )

        hours_until_start = time_until_start.total_seconds() / 3600

        # Free cancellation window (>= 12 hours)
        if hours_until_start >= cls.FREE_CANCEL_WINDOW_HOURS:
            return PolicyDecision(
                allow=True,
                reason_code="OK",
                refund_cents=rate_cents if not is_package else 0,
                restore_package_unit=is_package,
                message=f"Cancelled with full {'refund' if not is_package else 'package credit restoration'}",
            )

        # Inside 12h window - no refund (or partial if configured)
        # For now: no refund, no package restoration
        return PolicyDecision(
            allow=True,
            reason_code="LATE_CANCEL",
            refund_cents=0,
            restore_package_unit=False,
            message=f"Cancelled within {cls.FREE_CANCEL_WINDOW_HOURS}h window. No refund available.",
        )

    @classmethod
    def evaluate_tutor_cancellation(
        cls,
        booking_start_at: datetime,
        now: datetime,
        rate_cents: int,
        is_package: bool,
    ) -> PolicyDecision:
        """
        Evaluate tutor cancellation request.

        Rules:
        - >= 12h before: full refund to student, no penalty to tutor
        - < 12h before: full refund + compensation, penalty strike to tutor
        - Already started: not allowed
        """
        time_until_start = booking_start_at - now

        # Already started
        if time_until_start.total_seconds() <= 0:
            return PolicyDecision(
                allow=False,
                reason_code="ALREADY_STARTED",
                message="Cannot cancel a session that has already started",
            )

        hours_until_start = time_until_start.total_seconds() / 3600

        # Early cancellation (>= 12 hours)
        if hours_until_start >= cls.FREE_CANCEL_WINDOW_HOURS:
            return PolicyDecision(
                allow=True,
                reason_code="OK",
                refund_cents=rate_cents if not is_package else 0,
                restore_package_unit=is_package,
                tutor_compensation_cents=0,
                apply_strike_to_tutor=False,
                message="Tutor cancelled with sufficient notice",
            )

        # Late cancellation (< 12 hours) - penalty
        return PolicyDecision(
            allow=True,
            reason_code="TUTOR_LATE_CANCEL",
            refund_cents=rate_cents if not is_package else 0,
            restore_package_unit=is_package,
            tutor_compensation_cents=cls.TUTOR_CANCEL_PENALTY_CENTS,
            apply_strike_to_tutor=True,
            message=f"Tutor cancelled within {cls.FREE_CANCEL_WINDOW_HOURS}h. Student compensated.",
        )


# ============================================================================
# Reschedule Policy
# ============================================================================


class ReschedulePolicy:
    """Implements rescheduling rules."""

    RESCHEDULE_WINDOW_HOURS = 12

    @classmethod
    def evaluate_reschedule(
        cls,
        booking_start_at: datetime,
        now: datetime,
        new_start_at: datetime,
    ) -> PolicyDecision:
        """
        Evaluate reschedule request.

        Rules:
        - >= 12h before original time: allowed
        - < 12h before: treated as cancellation + new booking
        - New time must be in the future
        """
        time_until_start = booking_start_at - now

        # Already started or past
        if time_until_start.total_seconds() <= 0:
            return PolicyDecision(
                allow=False,
                reason_code="ALREADY_STARTED",
                message="Cannot reschedule a session that has already started",
            )

        # New time must be in the future
        if new_start_at <= now:
            return PolicyDecision(
                allow=False,
                reason_code="INVALID_NEW_TIME",
                message="New session time must be in the future",
            )

        hours_until_start = time_until_start.total_seconds() / 3600

        # Within reschedule window
        if hours_until_start >= cls.RESCHEDULE_WINDOW_HOURS:
            return PolicyDecision(
                allow=True,
                reason_code="OK",
                message="Reschedule allowed",
            )

        # Too close to session - must cancel instead
        return PolicyDecision(
            allow=False,
            reason_code="WINDOW_EXPIRED",
            message=f"Cannot reschedule within {cls.RESCHEDULE_WINDOW_HOURS}h of session. Please cancel and rebook.",
        )


# ============================================================================
# No-Show Policy
# ============================================================================


class NoShowPolicy:
    """Implements no-show detection and handling rules."""

    GRACE_PERIOD_MINUTES = 10
    MAX_REPORT_WINDOW_HOURS = 24

    @classmethod
    def evaluate_no_show_report(
        cls,
        booking_start_at: datetime,
        now: datetime,
        reporter_role: Literal["STUDENT", "TUTOR"],
    ) -> PolicyDecision:
        """
        Evaluate whether a no-show can be reported.

        Rules:
        - Can only report after grace period (10 min after start)
        - Must report within 24h of start time
        - Tutor reports student no-show: tutor earns, student loses credit
        - Student reports tutor no-show: student refunded, tutor penalized
        """
        time_since_start = now - booking_start_at
        minutes_since_start = time_since_start.total_seconds() / 60

        # Too early - within grace period
        if minutes_since_start < cls.GRACE_PERIOD_MINUTES:
            return PolicyDecision(
                allow=False,
                reason_code="GRACE_PERIOD",
                message=f"Wait at least {cls.GRACE_PERIOD_MINUTES} minutes after start time",
            )

        # Too late - beyond report window
        hours_since_start = time_since_start.total_seconds() / 3600
        if hours_since_start > cls.MAX_REPORT_WINDOW_HOURS:
            return PolicyDecision(
                allow=False,
                reason_code="REPORT_WINDOW_EXPIRED",
                message=f"No-show reports must be filed within {cls.MAX_REPORT_WINDOW_HOURS}h",
            )

        # Valid report
        if reporter_role == "TUTOR":
            return PolicyDecision(
                allow=True,
                reason_code="OK",
                message="Student no-show confirmed. Tutor will be paid.",
            )
        else:  # STUDENT
            return PolicyDecision(
                allow=True,
                reason_code="OK",
                apply_strike_to_tutor=True,
                message="Tutor no-show confirmed. Refund issued.",
            )


# ============================================================================
# Grace Edit Policy
# ============================================================================


class GraceEditPolicy:
    """Allows quick fixes immediately after booking creation."""

    GRACE_PERIOD_MINUTES = 5
    MIN_ADVANCE_BOOKING_HOURS = 24

    @classmethod
    def can_edit_in_grace(
        cls,
        booking_created_at: datetime,
        booking_start_at: datetime,
        now: datetime,
    ) -> bool:
        """
        Check if booking can be edited in grace period.

        Rules:
        - Within 5 minutes of creation
        - Start time is at least 24h away
        """
        time_since_creation = now - booking_created_at
        time_until_start = booking_start_at - now

        within_grace = time_since_creation.total_seconds() < (cls.GRACE_PERIOD_MINUTES * 60)
        enough_advance = time_until_start.total_seconds() >= (cls.MIN_ADVANCE_BOOKING_HOURS * 3600)

        return within_grace and enough_advance
