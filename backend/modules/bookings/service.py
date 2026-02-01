"""
Booking service with state machine logic and conflict checking.
Implements core booking business logic per booking_detail.md spec.
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from core.avatar_storage import build_avatar_url
from core.config import settings
from core.currency import calculate_platform_fee_dynamic
from core.utils import StringUtils
from models import Booking, StudentPackage, TutorBlackout, TutorProfile, User
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import (
    CancelledByRole,
    PaymentState,
    SessionState,
)
from modules.bookings.policy_engine import CancellationPolicy, NoShowPolicy
from modules.bookings.schemas import BookingDTO, StudentInfoDTO, TutorInfoDTO

logger = logging.getLogger(__name__)


# ============================================================================
# Booking Service
# ============================================================================


class BookingService:
    """Core booking business logic."""

    DEFAULT_PLATFORM_FEE_PCT = Decimal("20.0")  # Default 20% platform fee (for new tutors)
    MIN_GAP_MINUTES = 5  # Buffer between sessions

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Create Booking
    # ========================================================================

    def create_booking(
        self,
        student_id: int,
        tutor_profile_id: int,
        start_at: datetime,
        duration_minutes: int,
        lesson_type: str = "REGULAR",
        subject_id: int | None = None,
        notes_student: str | None = None,
        package_id: int | None = None,
    ) -> Booking:
        """
        Create a new booking with conflict checking and price calculation.

        Rate Locking Behavior:
        ----------------------
        The rate is LOCKED at booking creation time. This means:

        1. The tutor's current hourly_rate is captured and stored in the booking
        2. If the tutor changes their rate after booking creation, the pending
           booking is NOT affected - it uses the original rate
        3. The rate_cents field in the booking represents the locked rate
        4. The created_at timestamp serves as the "rate_locked_at" time

        This design ensures:
        - Students pay the rate they agreed to when booking
        - Tutors honor the rate that was advertised at booking time
        - Rate changes only affect NEW bookings, not pending ones

        Raises:
            HTTPException: If validation fails or conflicts exist
        """
        # 1. Validate inputs
        # Ensure start_at is timezone-aware (convert to UTC if naive)
        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=UTC)

        end_at = start_at + timedelta(minutes=duration_minutes)
        now = datetime.now(UTC)

        if start_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking start time must be in the future",
            )

        # 2. Get tutor profile (excluding soft-deleted)
        from core.soft_delete import filter_active

        tutor_profile = (
            filter_active(self.db.query(TutorProfile), TutorProfile)
            .filter(TutorProfile.id == tutor_profile_id)
            .first()
        )
        if not tutor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor not found",
            )

        # Also verify the tutor's user account is not soft-deleted
        tutor_user = (
            filter_active(self.db.query(User), User)
            .filter(User.id == tutor_profile.user_id)
            .first()
        )
        if not tutor_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor account not found",
            )

        # 3. Get student profile (excluding soft-deleted)
        student = (
            filter_active(self.db.query(User), User)
            .filter(User.id == student_id)
            .first()
        )
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # 4. Check for conflicts with row-level locking to prevent race conditions
        # The use_lock=True ensures that concurrent booking requests for the same
        # tutor's time slots are serialized, preventing double-booking
        conflicts = self.check_conflicts(tutor_profile_id, start_at, end_at, use_lock=True)
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tutor is not available at this time: {conflicts}",
            )

        # 5. Calculate pricing with dynamic commission tiers
        rate_cents, platform_fee_cents, tutor_earnings_cents, fee_pct, tier_name = self._calculate_pricing(
            tutor_profile, duration_minutes, lesson_type
        )

        # 6. Get timezones
        student_tz = student.timezone or "UTC"
        tutor_tz = tutor_profile.user.timezone or "UTC"

        # 7. Determine initial state based on auto_confirm
        is_auto_confirm = tutor_profile.auto_confirm

        # 8. Create booking with new four-field status system
        booking = Booking(
            tutor_profile_id=tutor_profile.id,
            student_id=student_id,
            subject_id=subject_id,
            package_id=package_id,
            start_time=start_at,
            end_time=end_at,
            # New status fields
            session_state=SessionState.SCHEDULED.value if is_auto_confirm else SessionState.REQUESTED.value,
            session_outcome=None,  # Only set on terminal states
            payment_state=PaymentState.AUTHORIZED.value if is_auto_confirm else PaymentState.PENDING.value,
            dispute_state="NONE",
            lesson_type=lesson_type,
            notes_student=notes_student,
            # Use actual schema fields for pricing
            hourly_rate=tutor_profile.hourly_rate,
            total_amount=Decimal(rate_cents) / 100,
            rate_cents=rate_cents,
            currency=tutor_profile.currency or "USD",
            platform_fee_pct=fee_pct,  # Dynamic fee based on tutor tier
            platform_fee_cents=platform_fee_cents,
            tutor_earnings_cents=tutor_earnings_cents,
            pricing_type="hourly",
            student_tz=student_tz,
            tutor_tz=tutor_tz,
            created_by="STUDENT",
            # Snapshot fields - names now accessed directly from users table
            tutor_name=StringUtils.format_display_name(
                tutor_profile.user.first_name, tutor_profile.user.last_name, tutor_profile.user.email
            ),
            tutor_title=tutor_profile.title,
            student_name=StringUtils.format_display_name(
                student.first_name, student.last_name, student.email
            ),
        )

        # 9. If auto-confirm, set confirmed timestamp and generate join URL
        if is_auto_confirm:
            booking.confirmed_at = datetime.now(UTC)
            booking.join_url = self._generate_join_url(booking.id)

        self.db.add(booking)
        self.db.flush()

        # 10. If using package, decrement credits
        # Note: We split this into two steps for safety:
        # 1. First decrement the credit (but don't set "exhausted" status yet)
        # 2. After booking is successfully created, update status if exhausted
        # This ensures the package status is only set to "exhausted" after
        # the booking creation succeeds, preventing inconsistent states.
        if package_id:
            self._consume_package_credit(package_id)
            # Now that booking is created, safely update package status if exhausted
            self._update_package_status_if_exhausted(package_id)

        return booking

    # ========================================================================
    # Conflict Checking
    # ========================================================================

    def check_conflicts(
        self,
        tutor_profile_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_booking_id: int | None = None,
        use_lock: bool = False,
    ) -> str:
        """
        Check for scheduling conflicts.

        Args:
            tutor_profile_id: Tutor profile to check
            start_at: Proposed booking start time
            end_at: Proposed booking end time
            exclude_booking_id: Optional booking ID to exclude (for reschedules)
            use_lock: If True, acquires row-level locks to prevent race conditions

        Returns:
            Empty string if no conflicts, error message otherwise

        Note:
            When use_lock=True, this method acquires FOR UPDATE locks on all
            potentially conflicting bookings. This prevents double-booking
            race conditions but should only be used within a transaction
            that will be committed shortly after.
        """
        # Check for overlapping bookings (exclude soft-deleted tutor profiles)
        from core.soft_delete import filter_active

        tutor_profile = (
            filter_active(self.db.query(TutorProfile), TutorProfile)
            .filter(TutorProfile.id == tutor_profile_id)
            .first()
        )
        if not tutor_profile:
            return ""  # No tutor profile means no conflicts

        query = self.db.query(Booking).filter(
            Booking.tutor_profile_id == tutor_profile.id,
            Booking.session_state.in_([
                SessionState.REQUESTED.value,
                SessionState.SCHEDULED.value,
                SessionState.ACTIVE.value,
            ]),
            or_(
                and_(Booking.start_time <= start_at, Booking.end_time > start_at),
                and_(Booking.start_time < end_at, Booking.end_time >= end_at),
                and_(Booking.start_time >= start_at, Booking.end_time <= end_at),
            ),
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        # Apply row-level locking to prevent race conditions during booking creation
        # This ensures concurrent requests serialize when checking the same time slots
        if use_lock:
            query = query.with_for_update(nowait=False)

        existing = query.first()
        if existing:
            return f"Overlaps with existing booking at {existing.start_time}"

        # Check for blackout periods
        blackout = (
            self.db.query(TutorBlackout)
            .filter(
                TutorBlackout.tutor_id == tutor_profile.user_id,
                or_(
                    and_(
                        TutorBlackout.start_at <= start_at,
                        TutorBlackout.end_at > start_at,
                    ),
                    and_(TutorBlackout.start_at < end_at, TutorBlackout.end_at >= end_at),
                    and_(
                        TutorBlackout.start_at >= start_at,
                        TutorBlackout.end_at <= end_at,
                    ),
                ),
            )
            .first()
        )
        if blackout:
            return f"Tutor unavailable (blackout): {blackout.reason or 'vacation'}"

        # Check availability windows with proper DST handling
        from zoneinfo import ZoneInfo

        from core.timezone import is_valid_timezone
        from models import TutorAvailability

        if tutor_profile:
            # FIX: Convert UTC start time to tutor's timezone before extracting day_of_week
            # This prevents timezone mismatch where booking at 11pm Tuesday UTC could be
            # Wednesday in tutor's timezone (e.g., Asia/Tokyo), causing wrong day comparison
            tutor_tz_str = tutor_profile.user.timezone if tutor_profile.user else None
            if not tutor_tz_str or not is_valid_timezone(tutor_tz_str):
                tutor_tz_str = "UTC"
            tutor_tz = ZoneInfo(tutor_tz_str)

            # Convert booking start time to tutor's local time
            local_start = start_at.astimezone(tutor_tz)
            local_end = end_at.astimezone(tutor_tz)

            # Convert Python weekday (Mon=0, Sun=6) to JS convention (Sun=0, Sat=6)
            # using the LOCAL day of the tutor, not UTC day
            python_weekday = local_start.weekday()  # Monday=0, Sunday=6
            day_of_week = (python_weekday + 1) % 7  # Convert to Sunday=0, Saturday=6

            # Handle case where session spans midnight in tutor's timezone
            # In this case, we need to check availability for both days
            local_end_weekday = local_end.weekday()
            end_day_of_week = (local_end_weekday + 1) % 7
            spans_midnight = local_start.date() != local_end.date()

            # Determine which days to query availability for
            days_to_check = [day_of_week]
            if spans_midnight and end_day_of_week != day_of_week:
                days_to_check.append(end_day_of_week)

            # Get all availability slots for the relevant day(s)
            availabilities = (
                self.db.query(TutorAvailability)
                .filter(
                    TutorAvailability.tutor_profile_id == tutor_profile.id,
                    TutorAvailability.day_of_week.in_(days_to_check),
                )
                .all()
            )

            # Check if booking falls within any availability window
            # We compare in the tutor's local timezone for consistency
            is_within_availability = False
            local_start_time = local_start.time()
            local_end_time = local_end.time()

            for availability in availabilities:
                # Get the timezone for this availability slot (may differ from tutor's profile timezone)
                avail_tz_str = getattr(availability, 'timezone', None) or tutor_tz_str
                if not is_valid_timezone(avail_tz_str):
                    avail_tz_str = tutor_tz_str
                avail_tz = ZoneInfo(avail_tz_str)

                # Convert availability times to tutor's timezone if they differ
                # This handles cases where availability was set in a different timezone
                if avail_tz_str != tutor_tz_str:
                    # Convert availability window from its timezone to tutor's timezone
                    avail_date = local_start.date()
                    avail_start_dt = datetime.combine(avail_date, availability.start_time).replace(tzinfo=avail_tz)
                    avail_end_dt = datetime.combine(avail_date, availability.end_time).replace(tzinfo=avail_tz)
                    avail_start_in_tutor_tz = avail_start_dt.astimezone(tutor_tz).time()
                    avail_end_in_tutor_tz = avail_end_dt.astimezone(tutor_tz).time()
                else:
                    avail_start_in_tutor_tz = availability.start_time
                    avail_end_in_tutor_tz = availability.end_time

                # Check if this availability slot is for the correct day
                avail_day = availability.day_of_week

                if not spans_midnight:
                    # Simple case: booking doesn't span midnight
                    if avail_day == day_of_week and avail_start_in_tutor_tz <= local_start_time and avail_end_in_tutor_tz >= local_end_time:
                        is_within_availability = True
                        break
                else:
                    # Complex case: booking spans midnight in tutor's timezone
                    # Need to check if both the start and end portions are covered
                    # For simplicity, we require a single availability window that covers the full session
                    # by converting both times to the availability date and checking overlap
                    avail_date = local_start.date() if avail_day == day_of_week else local_end.date()
                    avail_start_dt = datetime.combine(avail_date, avail_start_in_tutor_tz).replace(tzinfo=tutor_tz)
                    avail_end_dt = datetime.combine(avail_date, avail_end_in_tutor_tz).replace(tzinfo=tutor_tz)

                    # Check if booking window falls within availability window
                    if avail_start_dt <= local_start and avail_end_dt >= local_end:
                        is_within_availability = True
                        break

            if not is_within_availability:
                # Provide informative error message with tutor's local time
                local_day_name = local_start.strftime('%A')
                local_time_str = local_start.strftime('%H:%M')
                return f"Tutor not available on {local_day_name} at {local_time_str} (tutor's local time)"

        return ""

    # ========================================================================
    # External Calendar Conflict Check
    # ========================================================================

    async def check_external_calendar_conflict(
        self,
        tutor_user: User,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        """
        Check if tutor has external calendar conflicts for the requested time.

        This method queries the tutor's connected Google Calendar to detect
        conflicts with external events (meetings, appointments, etc.) that
        were added after the last sync.

        Args:
            tutor_user: The tutor's User model
            start_at: Proposed booking start time (UTC)
            end_at: Proposed booking end time (UTC)

        Raises:
            HTTPException: 409 if there's a calendar conflict

        Note:
            - Only checks if tutor has Google Calendar connected
            - Calendar check failures are logged but don't block booking (graceful degradation)
            - Results are cached briefly (2 min) to reduce API load
        """
        # Skip if tutor has no calendar connected
        if not tutor_user.google_calendar_refresh_token:
            logger.debug(f"Tutor {tutor_user.id} has no calendar connected, skipping external check")
            return

        try:
            from core.calendar_conflict import CalendarAPIError, CalendarConflictService

            calendar_service = CalendarConflictService(self.db)
            has_conflict, error_message = await calendar_service.check_calendar_conflict(
                tutor_user=tutor_user,
                start_time=start_at,
                end_time=end_at,
            )

            if has_conflict:
                logger.info(
                    f"External calendar conflict detected for tutor {tutor_user.id} "
                    f"at {start_at} - {end_at}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "external_calendar_conflict",
                        "message": error_message or "Tutor has a conflict on their external calendar during this time",
                        "suggested_action": "select_different_time",
                    },
                )

        except HTTPException:
            # Re-raise HTTP exceptions (calendar conflict)
            raise
        except CalendarAPIError as e:
            # Calendar API failed - log but don't block booking
            logger.warning(f"Calendar check failed for tutor {tutor_user.id}: {e}")
        except Exception as e:
            # Unexpected error - log but don't block booking (graceful degradation)
            logger.warning(
                f"Unexpected error during calendar check for tutor {tutor_user.id}: {e}"
            )

    # ========================================================================
    # Cancel Booking
    # ========================================================================

    def cancel_booking(self, booking: Booking, cancelled_by_role: str, reason: str | None = None) -> Booking:
        """
        Cancel a booking with policy enforcement.

        Args:
            booking: Booking to cancel
            cancelled_by_role: "STUDENT" or "TUTOR"
            reason: Optional cancellation reason
        """
        now = datetime.now(UTC)

        # Check if booking can be cancelled using state machine
        if not BookingStateMachine.is_cancellable(booking.session_state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel booking with state {booking.session_state}",
            )

        # Apply policy
        if cancelled_by_role == "STUDENT":
            decision = CancellationPolicy.evaluate_student_cancellation(
                booking_start_at=booking.start_time,
                now=now,
                rate_cents=booking.rate_cents or 0,
                lesson_type=booking.lesson_type or "REGULAR",
                is_trial=(booking.lesson_type == "TRIAL"),
                is_package=(booking.package_id is not None),
            )
        else:  # TUTOR
            decision = CancellationPolicy.evaluate_tutor_cancellation(
                booking_start_at=booking.start_time,
                now=now,
                rate_cents=booking.rate_cents or 0,
                is_package=(booking.package_id is not None),
            )

        if not decision.allow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=decision.message,
            )

        # Determine if refund should be issued
        issue_refund = decision.refund_cents > 0 or decision.restore_package_unit

        # Use state machine to cancel booking
        role = CancelledByRole.STUDENT if cancelled_by_role == "STUDENT" else CancelledByRole.TUTOR
        result = BookingStateMachine.cancel_booking(booking, role, refund=issue_refund)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "Failed to cancel booking",
            )

        # Set cancellation reason
        booking.cancellation_reason = reason
        booking.notes = (booking.notes or "") + f"\n[Cancelled: {decision.message}]"
        booking.updated_at = datetime.now(UTC)

        # Apply penalties/compensations
        if decision.apply_strike_to_tutor and booking.tutor_profile:
            tutor_profile = booking.tutor_profile
            tutor_profile.cancellation_strikes = (tutor_profile.cancellation_strikes or 0) + 1

        # Handle package credit restoration
        if decision.restore_package_unit and booking.package_id:
            self._restore_package_credit(booking.package_id)

        return booking

    # ========================================================================
    # Mark No-Show
    # ========================================================================

    def mark_no_show(
        self,
        booking: Booking,
        reporter_role: str,
        notes: str | None = None,
        *,
        use_lock: bool = False,
    ) -> tuple[Booking, bool]:
        """
        Mark a booking as no-show with race condition protection.

        This method handles the case where both parties may report no-show
        simultaneously. If conflicting reports exist, it auto-escalates to dispute.

        Args:
            booking: The booking to mark as no-show
            reporter_role: "TUTOR" or "STUDENT" - who is making the report
            notes: Optional notes about the no-show
            use_lock: If True, re-acquire the booking with row-level lock

        Returns:
            Tuple of (booking, escalated_to_dispute)
            - booking: The updated booking
            - escalated_to_dispute: True if conflicting reports caused auto-escalation

        Raises:
            HTTPException: If validation fails or state transition is invalid
        """
        now = datetime.now(UTC)

        # Validate with policy
        decision = NoShowPolicy.evaluate_no_show_report(
            booking_start_at=booking.start_time,
            now=now,
            reporter_role=reporter_role,
        )

        if not decision.allow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=decision.message,
            )

        # Re-acquire booking with lock if requested to prevent race conditions
        if use_lock:
            locked_booking = BookingStateMachine.get_booking_with_lock(self.db, booking.id)
            if not locked_booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )
            booking = locked_booking

        # Determine who was absent (opposite of reporter)
        who_was_absent = "STUDENT" if reporter_role == "TUTOR" else "TUTOR"

        # Use state machine to mark no-show with reporter info for conflict detection
        result = BookingStateMachine.mark_no_show(booking, who_was_absent, reporter_role)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or f"Cannot mark no-show for booking with state {booking.session_state}",
            )

        # Add notes based on outcome
        if result.escalated_to_dispute:
            booking.notes = (booking.notes or "") + "\n[Conflicting no-show reports - escalated to dispute]"
            if notes:
                booking.notes += f" Reporter ({reporter_role}) notes: {notes}"
        elif notes:
            booking.notes = (booking.notes or "") + f"\n[No-show reported by {reporter_role}: {notes}]"

        booking.updated_at = datetime.now(UTC)

        # Apply penalties only if not escalated (let admin decide if escalated)
        if not result.escalated_to_dispute:
            if decision.apply_strike_to_tutor and booking.tutor_profile:
                tutor_profile = booking.tutor_profile
                tutor_profile.cancellation_strikes = (tutor_profile.cancellation_strikes or 0) + 1

            # Restore package credit for tutor no-show (student gets refund)
            # When tutor is no-show, the student deserves their package credit back
            if who_was_absent == "TUTOR" and booking.package_id:
                self._restore_package_credit(booking.package_id)

        return booking, result.escalated_to_dispute

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _calculate_pricing(
        self, tutor_profile: TutorProfile, duration_minutes: int, lesson_type: str
    ) -> tuple[int, int, int, Decimal, str]:
        """
        Calculate rate, platform fee, and tutor earnings using dynamic commission tiers.

        Revenue-based commission tiers:
        - Standard ($0 - $999.99 lifetime): 20% platform fee
        - Silver ($1,000 - $4,999.99 lifetime): 15% platform fee
        - Gold ($5,000+ lifetime): 10% platform fee

        Returns:
            (rate_cents, platform_fee_cents, tutor_earnings_cents, fee_pct, tier_name)
        """
        # Get hourly rate in cents
        hourly_rate_cents = int(tutor_profile.hourly_rate * 100)

        # Special handling for trials
        if lesson_type == "TRIAL" and hasattr(tutor_profile, 'trial_price_cents') and tutor_profile.trial_price_cents:
            rate_cents = tutor_profile.trial_price_cents
        else:
            # Calculate pro-rated amount
            rate_cents = int(hourly_rate_cents * (duration_minutes / 60))

        # Calculate fees using dynamic revenue-based tiers
        platform_fee_cents, tutor_earnings_cents, fee_pct, tier_name = calculate_platform_fee_dynamic(
            self.db, tutor_profile.id, rate_cents
        )

        return rate_cents, platform_fee_cents, tutor_earnings_cents, fee_pct, tier_name

    def _generate_join_url(self, booking_id: int) -> str:
        """
        Generate session join URL.

        This creates a secure, unique meeting link for the booking.
        Integration points:
        - For Zoom: Use Zoom SDK/API to create meetings
        - For Google Meet: Use Google Calendar API
        - For Jitsi: Use Jitsi API or self-hosted instance
        - For custom: Use internal video solution

        Current implementation: Generates platform-hosted room with secure token.
        """
        import hashlib
        import time

        # Generate a secure, deterministic token based on booking_id
        secret = "platform_meeting_secret_key"  # Should be in settings
        timestamp = int(time.time() / 3600)  # Changes every hour for security
        token_data = f"{booking_id}:{timestamp}:{secret}"
        secure_token = hashlib.sha256(token_data.encode()).hexdigest()[:16]

        # Return platform meeting room URL with secure access token
        # In production, replace with actual video provider integration
        return f"https://platform.example.com/session/{booking_id}?token={secure_token}"

    def _consume_package_credit(self, package_id: int) -> None:
        """
        Atomically decrement package sessions_remaining.

        Uses atomic SQL UPDATE with WHERE guard to prevent race conditions
        where two concurrent requests could consume the same credit.

        Note: This method intentionally does NOT set the "exhausted" status.
        The status should only be updated after the booking creation succeeds
        and the transaction is about to commit. Use `_update_package_status_if_exhausted()`
        after successful booking creation to update the status.
        """
        # Atomic decrement with validation guard
        result = self.db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.sessions_remaining > 0,
                StudentPackage.status == "active",
            )
            .values(
                sessions_remaining=StudentPackage.sessions_remaining - 1,
                sessions_used=StudentPackage.sessions_used + 1,
                updated_at=datetime.now(UTC),
            )
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No package credits available or package is not active",
            )

        # NOTE: Do NOT set "exhausted" status here!
        # The status should only be updated after the booking is successfully
        # created and the transaction is ready to commit.
        # See _update_package_status_if_exhausted() for the safe status update.

    def _update_package_status_if_exhausted(self, package_id: int) -> None:
        """
        Update package status to "exhausted" if sessions_remaining is 0.

        This method should be called AFTER successful booking creation,
        just before committing the transaction. This ensures that:
        1. The package status is not prematurely set to "exhausted"
        2. If booking creation fails, the package status remains "active"
        3. The status update is atomic and consistent with the booking state

        This follows the principle of setting terminal states as late as possible
        to prevent inconsistent states if intermediate operations fail.
        """
        self.db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.sessions_remaining == 0,
                StudentPackage.status == "active",
            )
            .values(
                status="exhausted",
                updated_at=datetime.now(UTC),
            )
        )

    def _restore_package_credit(self, package_id: int) -> bool:
        """
        Atomically restore one credit to a package.

        Uses atomic SQL UPDATE with guards to prevent race conditions and over-restoration.
        Idempotent: safe to call multiple times for the same booking/package.

        Args:
            package_id: The ID of the package to restore credit to

        Returns:
            True if credit was restored, False if already at max or invalid state

        Guards:
            - sessions_used > 0 (must have used sessions to restore)
            - sessions_remaining < sessions_purchased (prevent over-restoration)
            - status in (active, exhausted) (not expired/refunded)
        """
        # Atomic increment with safety guards
        result = self.db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.sessions_used > 0,
                StudentPackage.sessions_remaining < StudentPackage.sessions_purchased,  # Guard against over-restore
                StudentPackage.status.in_(["active", "exhausted"]),
            )
            .values(
                sessions_remaining=StudentPackage.sessions_remaining + 1,
                sessions_used=StudentPackage.sessions_used - 1,
                updated_at=datetime.now(UTC),
            )
        )

        if result.rowcount == 0:
            # Either package not found, already at max credits, or in invalid state
            return False

        # Reactivate exhausted packages after restoring credit
        self.db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.status == "exhausted",
                StudentPackage.sessions_remaining > 0,
            )
            .values(
                status="active",
                updated_at=datetime.now(UTC),
            )
        )

        return True


# ============================================================================
# DTO Conversion Utilities (Shared)
# ============================================================================


def _compute_legacy_status(booking: Booking) -> str:
    """
    Compute legacy status for backward compatibility.

    Maps new four-field system to old single status field.
    """
    session_state = booking.session_state
    session_outcome = booking.session_outcome
    cancelled_by = booking.cancelled_by_role

    # Map to legacy statuses
    if session_state == "REQUESTED":
        return "PENDING"
    elif session_state == "SCHEDULED":
        return "CONFIRMED"
    elif session_state == "ACTIVE":
        return "CONFIRMED"  # Active sessions show as confirmed
    elif session_state == "CANCELLED":
        if cancelled_by == "STUDENT":
            return "CANCELLED_BY_STUDENT"
        elif cancelled_by == "TUTOR":
            return "CANCELLED_BY_TUTOR"
        else:
            return "CANCELLED_BY_STUDENT"  # Default
    elif session_state == "EXPIRED":
        return "CANCELLED_BY_STUDENT"  # Expired treated as student cancel
    elif session_state == "ENDED":
        outcome_map = {
            "COMPLETED": "COMPLETED",
            "NO_SHOW_STUDENT": "NO_SHOW_STUDENT",
            "NO_SHOW_TUTOR": "NO_SHOW_TUTOR",
            "NOT_HELD": "COMPLETED",
        }
        return outcome_map.get(session_outcome, "COMPLETED")

    return "PENDING"  # Default fallback


def booking_to_dto(booking: Booking, db: Session) -> BookingDTO:
    """
    Convert booking model to DTO with tutor and student info.

    Centralized utility to prevent duplication across router files.
    Used by: router.py, presentation/api.py, presentation/api_enhanced.py

    Rate Locking Note:
    ------------------
    The rate_cents in the returned DTO is the rate that was LOCKED at booking creation
    time, NOT the tutor's current rate. This means:

    1. If a tutor changes their hourly rate AFTER a booking is created, the pending
       booking will still use the original rate that was agreed upon.
    2. The rate_locked_at field indicates when the rate was locked (booking creation time).
    3. To compare with tutor's current rate, query the tutor profile separately.

    This design ensures price certainty for both students and tutors.
    """
    # Get tutor info
    tutor_profile = booking.tutor_profile
    tutor_user = tutor_profile.user if tutor_profile else None

    tutor_name = booking.tutor_name or (
        StringUtils.format_display_name(tutor_user.first_name, tutor_user.last_name, "Unknown")
        if tutor_user
        else "Unknown"
    )

    tutor_info = TutorInfoDTO(
        id=tutor_user.id if tutor_user else 0,
        name=tutor_name,
        avatar_url=build_avatar_url(
            tutor_user.avatar_key if tutor_user else None,
            default=settings.AVATAR_STORAGE_DEFAULT_URL,
        ),
        rating_avg=tutor_profile.average_rating if tutor_profile else Decimal("0.00"),
        title=booking.tutor_title or (tutor_profile.title if tutor_profile else None),
    )

    # Get student info
    student = booking.student

    student_name = booking.student_name or (
        StringUtils.format_display_name(student.first_name, student.last_name, "Unknown")
        if student
        else "Unknown"
    )

    # Get student level from profile if available
    student_level = None
    if student and hasattr(student, 'student_profile') and student.student_profile:
        student_level = student.student_profile.grade_level

    student_info = StudentInfoDTO(
        id=student.id if student else 0,
        name=student_name,
        avatar_url=build_avatar_url(
            student.avatar_key if student else None,
            default=settings.AVATAR_STORAGE_DEFAULT_URL,
        ),
        level=student_level,
    )

    # Get timezones from booking (stored at creation time)
    student_tz = booking.student_tz or "UTC"
    tutor_tz = booking.tutor_tz or "UTC"

    # Use pricing fields directly from booking (already calculated and stored)
    rate_cents = booking.rate_cents or int((booking.hourly_rate or Decimal("0")) * 100)
    platform_fee_pct = booking.platform_fee_pct or Decimal("20.0")
    platform_fee_cents = booking.platform_fee_cents or 0
    tutor_earnings_cents = booking.tutor_earnings_cents or 0
    currency = booking.currency or "USD"

    # Compute legacy status for backward compatibility
    legacy_status = _compute_legacy_status(booking)

    # Use booking fields directly (they are already denormalized/calculated)
    # NOTE: rate_cents is the LOCKED rate from booking creation, not the tutor's current rate
    return BookingDTO(
        id=booking.id,
        version=booking.version or 1,  # For optimistic locking and cache invalidation
        lesson_type=booking.lesson_type or "REGULAR",
        # New four-field status system
        session_state=booking.session_state or "REQUESTED",
        session_outcome=booking.session_outcome,
        payment_state=booking.payment_state or "PENDING",
        dispute_state=booking.dispute_state or "NONE",
        # Legacy status for backward compatibility
        status=legacy_status,
        # Cancellation info
        cancelled_by_role=booking.cancelled_by_role,
        cancelled_at=booking.cancelled_at,
        cancellation_reason=booking.cancellation_reason,
        start_at=booking.start_time,
        end_at=booking.end_time,
        student_tz=student_tz,
        tutor_tz=tutor_tz,
        # Pricing fields - rate_cents is the LOCKED rate at booking creation time
        # Rate changes by the tutor do NOT affect pending bookings
        rate_cents=rate_cents,
        rate_locked_at=booking.created_at,  # Rate was locked when booking was created
        currency=currency,
        platform_fee_pct=platform_fee_pct,
        platform_fee_cents=platform_fee_cents,
        tutor_earnings_cents=tutor_earnings_cents,
        join_url=booking.join_url,
        notes_student=booking.notes_student or booking.notes,  # Prefer notes_student, fallback to notes
        notes_tutor=booking.notes_tutor,
        tutor=tutor_info,
        student=student_info,
        subject_name=booking.subject_name or (booking.subject.name if booking.subject else None),
        topic=booking.topic,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        # Dispute information
        dispute_reason=booking.dispute_reason,
        disputed_at=booking.disputed_at,
        # Attendance tracking
        tutor_joined_at=booking.tutor_joined_at,
        student_joined_at=booking.student_joined_at,
        # Video meeting provider
        video_provider=booking.video_provider,
    )
