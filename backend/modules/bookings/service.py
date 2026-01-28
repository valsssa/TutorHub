"""
Booking service with state machine logic and conflict checking.
Implements core booking business logic per booking_detail.md spec.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from core.avatar_storage import build_avatar_url
from core.config import settings
from core.currency import calculate_platform_fee, calculate_platform_fee_dynamic
from core.utils import StringUtils
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

        # 2. Get tutor profile
        tutor_profile = self.db.query(TutorProfile).filter(TutorProfile.id == tutor_profile_id).first()
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
        conflicts = self.check_conflicts(tutor_profile_id, start_at, end_at)
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

        # 7. Determine initial status
        initial_status = "CONFIRMED" if tutor_profile.auto_confirm else "PENDING"

        # 8. Create booking (using actual schema fields)
        booking = Booking(
            tutor_profile_id=tutor_profile.id,
            student_id=student_id,
            subject_id=subject_id,
            package_id=package_id,
            start_time=start_at,
            end_time=end_at,
            status=initial_status,
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
        tutor_profile_id: int,
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
        tutor_profile = self.db.query(TutorProfile).filter(TutorProfile.id == tutor_profile_id).first()
        if not tutor_profile:
            return ""  # No tutor profile means no conflicts

        query = self.db.query(Booking).filter(
            Booking.tutor_profile_id == tutor_profile.id,
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

        # Check availability windows
        from models import TutorAvailability

        # Convert Python weekday (Mon=0, Sun=6) to JS convention (Sun=0, Sat=6)
        # This matches the convention used in availability_api.py
        python_weekday = start_at.weekday()  # Monday=0, Sunday=6
        day_of_week = (python_weekday + 1) % 7  # Convert to Sunday=0, Saturday=6
        start_time = start_at.time()
        end_time = end_at.time()

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
        now = datetime.now(UTC)

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
    student_profile = student.profile if student else None

    student_name = booking.student_name or (
        StringUtils.format_display_name(student.first_name, student.last_name, "Unknown")
        if student
        else "Unknown"
    )

    student_info = StudentInfoDTO(
        id=student.id if student else 0,
        name=student_name,
        avatar_url=build_avatar_url(
            student.avatar_key if student else None,
            default=settings.AVATAR_STORAGE_DEFAULT_URL,
        ),
        level=None,  # TODO: Add student level field if needed
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

    # Use booking fields directly (they are already denormalized/calculated)
    return BookingDTO(
        id=booking.id,
        lesson_type=booking.lesson_type or "REGULAR",
        status=booking.status or "PENDING",  # Keep uppercase status
        start_at=booking.start_time,
        end_at=booking.end_time,
        student_tz=student_tz,
        tutor_tz=tutor_tz,
        rate_cents=rate_cents,
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
    )
