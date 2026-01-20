"""
Booking service with state machine logic and conflict checking.
Implements core booking business logic per booking_detail.md spec.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from core.currency import calculate_platform_fee
from models import Booking, StudentPackage, TutorBlackout, TutorProfile, User
from modules.bookings.policy_engine import CancellationPolicy, NoShowPolicy
from modules.bookings.schemas import BookingDTO, StudentInfoDTO, TutorInfoDTO

# ============================================================================
# Booking State Machine
# ============================================================================

VALID_TRANSITIONS = {
    "PENDING": ["CONFIRMED", "CANCELLED_BY_STUDENT", "CANCELLED_BY_TUTOR"],
    "CONFIRMED": [
        "CANCELLED_BY_STUDENT",
        "CANCELLED_BY_TUTOR",
        "NO_SHOW_STUDENT",
        "NO_SHOW_TUTOR",
        "COMPLETED",
    ],
    "COMPLETED": ["REFUNDED"],  # Exception via admin only
    # Terminal states have no transitions
    "CANCELLED_BY_STUDENT": [],
    "CANCELLED_BY_TUTOR": [],
    "NO_SHOW_STUDENT": [],
    "NO_SHOW_TUTOR": [],
    "REFUNDED": [],
}


def can_transition(from_status: str, to_status: str) -> bool:
    """Check if state transition is valid."""
    allowed = VALID_TRANSITIONS.get(from_status.upper(), [])
    return to_status.upper() in allowed


# ============================================================================
# Booking Service
# ============================================================================


class BookingService:
    """Core booking business logic."""

    PLATFORM_FEE_PCT = Decimal("20.0")  # 20% platform fee
    MIN_GAP_MINUTES = 5  # Buffer between sessions

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Create Booking
    # ========================================================================

    def create_booking(
        self,
        student_id: int,
        tutor_id: int,
        start_at: datetime,
        duration_minutes: int,
        lesson_type: str = "REGULAR",
        subject_id: int | None = None,
        notes_student: str | None = None,
        package_id: int | None = None,
    ) -> Booking:
        """
        Create a new booking with conflict checking and price calculation.

        Raises:
            HTTPException: If validation fails or conflicts exist
        """
        # 1. Validate inputs
        end_at = start_at + timedelta(minutes=duration_minutes)
        now = datetime.utcnow()

        if start_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking start time must be in the future",
            )

        # 2. Get tutor profile
        tutor_profile = self.db.query(TutorProfile).join(User).filter(User.id == tutor_id).first()
        if not tutor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor not found",
            )

        # 3. Get student profile
        student = self.db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # 4. Check for conflicts
        conflicts = self.check_conflicts(tutor_id, start_at, end_at)
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tutor is not available at this time: {conflicts}",
            )

        # 5. Calculate pricing
        rate_cents, platform_fee_cents, tutor_earnings_cents = self._calculate_pricing(
            tutor_profile, duration_minutes, lesson_type
        )

        # 6. Get timezones
        student_tz = student.timezone or "UTC"
        tutor_tz = tutor_profile.user.timezone or "UTC"

        # 7. Determine initial status
        initial_status = "CONFIRMED" if tutor_profile.auto_confirm else "PENDING"

        # 8. Create booking
        booking = Booking(
            tutor_profile_id=tutor_profile.id,
            student_id=student_id,
            subject_id=subject_id,
            package_id=package_id,
            start_time=start_at,
            end_time=end_at,
            status=initial_status,
            lesson_type=lesson_type,
            student_tz=student_tz,
            tutor_tz=tutor_tz,
            notes_student=notes_student,
            rate_cents=rate_cents,
            currency=tutor_profile.currency,
            platform_fee_pct=self.PLATFORM_FEE_PCT,
            platform_fee_cents=platform_fee_cents,
            tutor_earnings_cents=tutor_earnings_cents,
            created_by="STUDENT",
            # Snapshot fields
            tutor_name=f"{tutor_profile.user.profile.first_name or ''} {tutor_profile.user.profile.last_name or ''}".strip()
            or tutor_profile.user.email,
            tutor_title=tutor_profile.title,
            student_name=f"{student.profile.first_name or ''} {student.profile.last_name or ''}".strip()
            or student.email,
        )

        # 9. If auto-confirm, generate join URL
        if initial_status == "CONFIRMED":
            booking.join_url = self._generate_join_url(booking.id)

        self.db.add(booking)
        self.db.flush()

        # 10. If using package, decrement credits
        if package_id:
            self._consume_package_credit(package_id)

        return booking

    # ========================================================================
    # Conflict Checking
    # ========================================================================

    def check_conflicts(
        self,
        tutor_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_booking_id: int | None = None,
    ) -> str:
        """
        Check for scheduling conflicts.

        Returns:
            Empty string if no conflicts, error message otherwise
        """
        # Check for overlapping bookings
        query = self.db.query(Booking).filter(
            Booking.tutor_profile_id == TutorProfile.id,
            TutorProfile.user_id == tutor_id,
            Booking.status.in_(["PENDING", "CONFIRMED"]),
            or_(
                and_(Booking.start_time <= start_at, Booking.end_time > start_at),
                and_(Booking.start_time < end_at, Booking.end_time >= end_at),
                and_(Booking.start_time >= start_at, Booking.end_time <= end_at),
            ),
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        existing = query.first()
        if existing:
            return f"Overlaps with existing booking at {existing.start_time}"

        # Check for blackout periods
        blackout = (
            self.db.query(TutorBlackout)
            .filter(
                TutorBlackout.tutor_id == tutor_id,
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

        # Check availability windows
        from models import TutorAvailability

        day_of_week = start_at.weekday()  # Monday=0, Sunday=6
        start_time = start_at.time()
        end_time = end_at.time()

        # Get tutor profile to access availabilities
        tutor_profile = self.db.query(TutorProfile).filter(TutorProfile.user_id == tutor_id).first()

        if tutor_profile:
            # Check if there's an availability slot covering this time
            availability = (
                self.db.query(TutorAvailability)
                .filter(
                    TutorAvailability.tutor_profile_id == tutor_profile.id,
                    TutorAvailability.day_of_week == day_of_week,
                    TutorAvailability.start_time <= start_time,
                    TutorAvailability.end_time >= end_time,
                )
                .first()
            )

            if not availability:
                return f"Tutor not available on {start_at.strftime('%A')} at {start_time.strftime('%H:%M')}"

        return ""

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
        now = datetime.utcnow()

        # Validate transition
        new_status = f"CANCELLED_BY_{cancelled_by_role}"
        if not can_transition(booking.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel booking with status {booking.status}",
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

        # Update booking
        booking.status = new_status
        booking.notes = (booking.notes or "") + f"\n[Cancelled: {decision.message}]"

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

    def mark_no_show(self, booking: Booking, reporter_role: str, notes: str | None = None) -> Booking:
        """Mark a booking as no-show."""
        now = datetime.utcnow()

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

        # Set status
        new_status = f"NO_SHOW_{'STUDENT' if reporter_role == 'TUTOR' else 'TUTOR'}"

        if not can_transition(booking.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark no-show for booking with status {booking.status}",
            )

        booking.status = new_status
        if notes:
            booking.notes = (booking.notes or "") + f"\n[No-show: {notes}]"

        # Apply penalties
        if decision.apply_strike_to_tutor and booking.tutor_profile:
            tutor_profile = booking.tutor_profile
            tutor_profile.cancellation_strikes = (tutor_profile.cancellation_strikes or 0) + 1

        return booking

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _calculate_pricing(
        self, tutor_profile: TutorProfile, duration_minutes: int, lesson_type: str
    ) -> tuple[int, int, int]:
        """
        Calculate rate, platform fee, and tutor earnings.

        Returns:
            (rate_cents, platform_fee_cents, tutor_earnings_cents)
        """
        # Get hourly rate in cents
        hourly_rate_cents = int(tutor_profile.hourly_rate * 100)

        # Special handling for trials
        if lesson_type == "TRIAL" and tutor_profile.trial_price_cents:
            rate_cents = tutor_profile.trial_price_cents
        else:
            # Calculate pro-rated amount
            rate_cents = int(hourly_rate_cents * (duration_minutes / 60))

        # Calculate fees using centralized currency module
        platform_fee_cents, tutor_earnings_cents = calculate_platform_fee(
            rate_cents, Decimal(str(self.PLATFORM_FEE_PCT))
        )

        return rate_cents, platform_fee_cents, tutor_earnings_cents

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
        """Decrement package sessions_remaining."""
        package = self.db.query(StudentPackage).filter(StudentPackage.id == package_id).first()
        if package and package.sessions_remaining > 0:
            package.sessions_remaining -= 1
            package.sessions_used += 1

    def _restore_package_credit(self, package_id: int) -> None:
        """Restore package credit on cancellation."""
        package = self.db.query(StudentPackage).filter(StudentPackage.id == package_id).first()
        if package:
            package.sessions_remaining += 1
            package.sessions_used = max(0, package.sessions_used - 1)


# ============================================================================
# DTO Conversion Utilities (Shared)
# ============================================================================


def booking_to_dto(booking: Booking, db: Session) -> BookingDTO:
    """
    Convert booking model to DTO with tutor and student info.

    Centralized utility to prevent duplication across router files.
    Used by: router.py, presentation/api.py, presentation/api_enhanced.py
    """
    # Get tutor info
    tutor_profile = booking.tutor_profile
    tutor_user = tutor_profile.user if tutor_profile else None
    tutor_user_profile = tutor_user.profile if tutor_user else None

    tutor_name = booking.tutor_name or (
        f"{tutor_user_profile.first_name or ''} {tutor_user_profile.last_name or ''}".strip()
        if tutor_user_profile
        else tutor_user.email
        if tutor_user
        else "Unknown"
    )

    tutor_info = TutorInfoDTO(
        id=tutor_user.id if tutor_user else 0,
        name=tutor_name,
        avatar_url=tutor_user_profile.avatar_url if tutor_user_profile else None,
        rating_avg=tutor_profile.average_rating if tutor_profile else Decimal("0.00"),
        title=booking.tutor_title or (tutor_profile.title if tutor_profile else None),
    )

    # Get student info
    student = booking.student
    student_profile = student.profile if student else None

    student_name = booking.student_name or (
        f"{student_profile.first_name or ''} {student_profile.last_name or ''}".strip()
        if student_profile
        else student.email
        if student
        else "Unknown"
    )

    student_info = StudentInfoDTO(
        id=student.id if student else 0,
        name=student_name,
        avatar_url=student_profile.avatar_url if student_profile else None,
        level=None,  # TODO: Add student level field if needed
    )

    # Use booking fields directly (they are already denormalized/calculated)
    return BookingDTO(
        id=booking.id,
        lesson_type=booking.lesson_type or "REGULAR",
        status=booking.status or "pending",
        start_at=booking.start_time,
        end_at=booking.end_time,
        student_tz=booking.student_tz or "UTC",
        tutor_tz=booking.tutor_tz or "UTC",
        rate_cents=booking.rate_cents or 0,
        currency=booking.currency or "USD",
        platform_fee_pct=booking.platform_fee_pct or Decimal("20.0"),
        platform_fee_cents=booking.platform_fee_cents or 0,
        tutor_earnings_cents=booking.tutor_earnings_cents or 0,
        join_url=booking.join_url,
        notes_student=booking.notes_student or booking.notes,
        notes_tutor=booking.notes_tutor,
        tutor=tutor_info,
        student=student_info,
        subject_name=booking.subject_name or (booking.subject.name if booking.subject else None),
        topic=booking.topic,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )
