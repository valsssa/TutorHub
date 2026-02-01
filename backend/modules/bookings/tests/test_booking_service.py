"""
Tests for booking service business logic.
Tests booking creation, conflict checking, state transitions.
Updated for four-field status system.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import get_password_hash
from models import Base, TutorProfile, User, UserProfile
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import (
    CancelledByRole,
    PaymentState,
    SessionOutcome,
    SessionState,
)
from modules.bookings.service import BookingService

# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()

    yield session

    session.close()


@pytest.fixture
def test_student(db_session):
    """Create a test student user."""
    student = User(
        email="student@test.com",
        hashed_password=get_password_hash("password"),
        role="student",
        timezone="America/New_York",
    )
    db_session.add(student)

    student_profile = UserProfile(user=student, first_name="Test", last_name="Student")
    db_session.add(student_profile)

    db_session.commit()
    db_session.refresh(student)
    return student


@pytest.fixture
def test_tutor(db_session):
    """Create a test tutor user."""
    tutor = User(
        email="tutor@test.com",
        hashed_password=get_password_hash("password"),
        role="tutor",
        timezone="Europe/London",
    )
    db_session.add(tutor)

    tutor_user_profile = UserProfile(user=tutor, first_name="Test", last_name="Tutor")
    db_session.add(tutor_user_profile)

    tutor_profile = TutorProfile(
        user=tutor,
        title="Math Tutor",
        hourly_rate=Decimal("50.00"),
        average_rating=Decimal("4.5"),
        auto_confirm=False,
        currency="USD",
    )
    db_session.add(tutor_profile)

    db_session.commit()
    db_session.refresh(tutor)
    return tutor


def _get_tutor_profile(session, tutor_user):
    return session.query(TutorProfile).filter(TutorProfile.user_id == tutor_user.id).first()


# ============================================================================
# State Machine Tests
# ============================================================================


class TestStateMachine:
    """Test booking state transitions using new four-field system."""

    def test_valid_session_state_transitions(self):
        """Test all valid session_state transitions."""
        # REQUESTED can go to SCHEDULED, CANCELLED, or EXPIRED
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "SCHEDULED") is True
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "CANCELLED") is True
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "EXPIRED") is True

        # SCHEDULED can go to ACTIVE or CANCELLED
        assert BookingStateMachine.can_transition_session_state("SCHEDULED", "ACTIVE") is True
        assert BookingStateMachine.can_transition_session_state("SCHEDULED", "CANCELLED") is True

        # ACTIVE can only go to ENDED
        assert BookingStateMachine.can_transition_session_state("ACTIVE", "ENDED") is True

    def test_invalid_session_state_transitions(self):
        """Test invalid session_state transitions."""
        # Cannot go backwards
        assert BookingStateMachine.can_transition_session_state("SCHEDULED", "REQUESTED") is False
        assert BookingStateMachine.can_transition_session_state("ACTIVE", "SCHEDULED") is False
        assert BookingStateMachine.can_transition_session_state("ENDED", "ACTIVE") is False

        # Cannot skip states
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "ACTIVE") is False
        assert BookingStateMachine.can_transition_session_state("REQUESTED", "ENDED") is False

    def test_terminal_session_states(self):
        """Terminal session states should have no valid transitions."""
        assert BookingStateMachine.is_terminal_session_state("ENDED") is True
        assert BookingStateMachine.is_terminal_session_state("CANCELLED") is True
        assert BookingStateMachine.is_terminal_session_state("EXPIRED") is True

        # Non-terminal states
        assert BookingStateMachine.is_terminal_session_state("REQUESTED") is False
        assert BookingStateMachine.is_terminal_session_state("SCHEDULED") is False
        assert BookingStateMachine.is_terminal_session_state("ACTIVE") is False

    def test_cancellable_states(self):
        """Only REQUESTED and SCHEDULED should be cancellable."""
        assert BookingStateMachine.is_cancellable("REQUESTED") is True
        assert BookingStateMachine.is_cancellable("SCHEDULED") is True

        # Cannot cancel these
        assert BookingStateMachine.is_cancellable("ACTIVE") is False
        assert BookingStateMachine.is_cancellable("ENDED") is False
        assert BookingStateMachine.is_cancellable("CANCELLED") is False

    def test_payment_state_transitions(self):
        """Test valid payment_state transitions."""
        assert BookingStateMachine.can_transition_payment_state("PENDING", "AUTHORIZED") is True
        assert BookingStateMachine.can_transition_payment_state("AUTHORIZED", "CAPTURED") is True
        assert BookingStateMachine.can_transition_payment_state("AUTHORIZED", "VOIDED") is True
        assert BookingStateMachine.can_transition_payment_state("CAPTURED", "REFUNDED") is True

    def test_dispute_state_transitions(self):
        """Test valid dispute_state transitions."""
        assert BookingStateMachine.can_transition_dispute_state("NONE", "OPEN") is True
        assert BookingStateMachine.can_transition_dispute_state("OPEN", "RESOLVED_UPHELD") is True
        assert BookingStateMachine.can_transition_dispute_state("OPEN", "RESOLVED_REFUNDED") is True

        # Cannot reopen resolved dispute
        assert BookingStateMachine.can_transition_dispute_state("RESOLVED_UPHELD", "OPEN") is False


# ============================================================================
# Booking Creation Tests
# ============================================================================


class TestBookingCreation:
    """Test booking creation with pricing and conflict checking."""

    def test_create_basic_booking(self, db_session, test_student, test_tutor):
        """Test creating a basic booking."""
        service = BookingService(db_session)

        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
            lesson_type="REGULAR",
        )

        assert booking is not None
        assert booking.student_id == test_student.id
        assert booking.lesson_type == "REGULAR"
        assert booking.rate_cents == 5000  # $50 * 100
        assert booking.platform_fee_cents == 1000  # 20% of 5000
        assert booking.tutor_earnings_cents == 4000  # 80% of 5000
        assert booking.student_tz == "America/New_York"
        assert booking.tutor_tz == "Europe/London"

    def test_create_booking_with_auto_confirm(self, db_session, test_student, test_tutor):
        """Test booking creation with auto-confirm enabled."""
        tutor_profile = _get_tutor_profile(db_session, test_tutor)
        tutor_profile.auto_confirm = True
        db_session.commit()

        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )

        # Check new status fields
        assert booking.session_state == SessionState.SCHEDULED.value
        assert booking.payment_state == PaymentState.AUTHORIZED.value
        assert booking.join_url is not None

    def test_create_booking_without_auto_confirm(self, db_session, test_student, test_tutor):
        """Test booking creation without auto-confirm (default REQUESTED state)."""
        tutor_profile = _get_tutor_profile(db_session, test_tutor)
        tutor_profile.auto_confirm = False
        db_session.commit()

        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )

        # Check new status fields
        assert booking.session_state == SessionState.REQUESTED.value
        assert booking.payment_state == PaymentState.PENDING.value
        assert booking.join_url is None  # No join URL until confirmed

    def test_create_booking_calculates_30min_rate(self, db_session, test_student, test_tutor):
        """Test pro-rated pricing for 30-minute session."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=30,
        )

        assert booking.rate_cents == 2500  # $50 * 0.5 * 100

    def test_create_trial_booking_with_special_price(self, db_session, test_student, test_tutor):
        """Test trial booking with special pricing."""
        tutor_profile = _get_tutor_profile(db_session, test_tutor)
        tutor_profile.trial_price_cents = 1000  # $10 trial
        db_session.commit()

        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=30,
            lesson_type="TRIAL",
        )

        assert booking.rate_cents == 1000  # Uses trial price
        assert booking.lesson_type == "TRIAL"

    def test_create_booking_in_past_fails(self, db_session, test_student, test_tutor):
        """Cannot create booking in the past."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() - timedelta(hours=1)  # Past

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            tutor_profile = _get_tutor_profile(db_session, test_tutor)
            service.create_booking(
                student_id=test_student.id,
                tutor_profile_id=tutor_profile.id,
                start_at=start_at,
                duration_minutes=60,
            )

        assert exc_info.value.status_code == 400


# ============================================================================
# Conflict Checking Tests
# ============================================================================


class TestConflictChecking:
    """Test booking conflict detection."""

    def test_no_conflict_empty_schedule(self, db_session, test_student, test_tutor):
        """No conflict when tutor schedule is empty."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        end_at = start_at + timedelta(hours=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        conflicts = service.check_conflicts(
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            end_at=end_at,
        )

        assert conflicts == ""

    def test_conflict_with_existing_booking(self, db_session, test_student, test_tutor):
        """Detect conflict with existing booking."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        # Create first booking
        _ = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        # Try to create overlapping booking
        conflicts = service.check_conflicts(
            tutor_profile_id=tutor_profile.id,
            start_at=start_at + timedelta(minutes=30),  # Overlaps
            end_at=start_at + timedelta(minutes=90),
        )

        assert conflicts != ""
        assert "Overlaps" in conflicts

    def test_no_conflict_adjacent_bookings(self, db_session, test_student, test_tutor):
        """Adjacent bookings should not conflict."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        # Create first booking
        _ = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        # Create adjacent booking (starts when first ends)
        conflicts = service.check_conflicts(
            tutor_profile_id=tutor_profile.id,
            start_at=start_at + timedelta(hours=1),
            end_at=start_at + timedelta(hours=2),
        )

        assert conflicts == ""

    def test_check_conflicts_with_locking(self, db_session, test_student, test_tutor):
        """Verify check_conflicts supports row-level locking to prevent race conditions."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        start_at + timedelta(hours=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        # Create first booking
        _ = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        # Check conflicts with locking enabled (use_lock=True)
        # This should acquire FOR UPDATE locks on overlapping bookings
        conflicts = service.check_conflicts(
            tutor_profile_id=tutor_profile.id,
            start_at=start_at + timedelta(minutes=30),
            end_at=start_at + timedelta(minutes=90),
            use_lock=True,
        )

        assert conflicts != ""
        assert "Overlaps" in conflicts

    def test_check_conflicts_without_locking_backward_compatible(self, db_session, test_student, test_tutor):
        """Verify check_conflicts works without locking (backward compatible)."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        # Default call without use_lock should still work
        conflicts = service.check_conflicts(
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
        )

        assert conflicts == ""


# ============================================================================
# Cancellation Tests
# ============================================================================


class TestCancellation:
    """Test booking cancellation logic with new status system."""

    def test_student_cancels_early(self, db_session, test_student, test_tutor):
        """Student cancels 24h before: allowed with refund."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=2)  # 48h away - well outside window
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        _ = service.cancel_booking(
            booking=booking,
            cancelled_by_role="STUDENT",
            reason="Need to reschedule",
        )
        db_session.refresh(booking)

        # Check new status fields
        assert booking.session_state == SessionState.CANCELLED.value
        assert booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert booking.cancelled_by_role == CancelledByRole.STUDENT.value

    def test_tutor_cancels_late_gets_strike(self, db_session, test_student, test_tutor):
        """Tutor cancels < 24h: gets penalty strike."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(hours=6)  # 6h away
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        # Set to SCHEDULED state (tutor accepted)
        booking.session_state = SessionState.SCHEDULED.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        db_session.commit()

        # Reuse tutor_profile from above for strike tracking
        initial_strikes = tutor_profile.cancellation_strikes or 0

        _ = service.cancel_booking(
            booking=booking,
            cancelled_by_role="TUTOR",
            reason="Emergency",
        )
        db_session.commit()

        db_session.refresh(tutor_profile)
        assert tutor_profile.cancellation_strikes == initial_strikes + 1

        # Check status
        db_session.refresh(booking)
        assert booking.session_state == SessionState.CANCELLED.value
        assert booking.cancelled_by_role == CancelledByRole.TUTOR.value
        assert booking.payment_state == PaymentState.REFUNDED.value  # Tutor cancel = refund


# ============================================================================
# No-Show Tests
# ============================================================================


class TestNoShow:
    """Test no-show marking logic with new status system."""

    def test_mark_student_no_show_after_grace(self, db_session, test_student, test_tutor):
        """Tutor marks student no-show after 10min grace."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() - timedelta(minutes=15)  # Started 15 min ago
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        # Set to SCHEDULED state (tutor accepted, session time passed)
        booking.session_state = SessionState.SCHEDULED.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        db_session.commit()

        marked = service.mark_no_show(
            booking=booking,
            reporter_role="TUTOR",
            notes="Student didn't join",
        )

        # Check new status fields
        assert marked.session_state == SessionState.ENDED.value
        assert marked.session_outcome == SessionOutcome.NO_SHOW_STUDENT.value
        assert marked.payment_state == PaymentState.CAPTURED.value  # Tutor gets paid

    def test_mark_tutor_no_show_after_grace(self, db_session, test_student, test_tutor):
        """Student marks tutor no-show after 10min grace."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() - timedelta(minutes=15)  # Started 15 min ago
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        # Set to SCHEDULED state (tutor accepted, session time passed)
        booking.session_state = SessionState.SCHEDULED.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        db_session.commit()

        marked = service.mark_no_show(
            booking=booking,
            reporter_role="STUDENT",
            notes="Tutor didn't join",
        )

        # Check new status fields
        assert marked.session_state == SessionState.ENDED.value
        assert marked.session_outcome == SessionOutcome.NO_SHOW_TUTOR.value
        assert marked.payment_state == PaymentState.REFUNDED.value  # Student gets refund


# ============================================================================
# State Machine Method Tests
# ============================================================================


class TestStateMachineMethods:
    """Test BookingStateMachine helper methods."""

    def test_accept_booking(self, db_session, test_student, test_tutor):
        """Test accepting a booking request."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        assert booking.session_state == SessionState.REQUESTED.value

        result = BookingStateMachine.accept_booking(booking)

        assert result.success is True
        assert booking.session_state == SessionState.SCHEDULED.value
        assert booking.payment_state == PaymentState.AUTHORIZED.value
        assert booking.confirmed_at is not None

    def test_decline_booking(self, db_session, test_student, test_tutor):
        """Test declining a booking request."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        result = BookingStateMachine.decline_booking(booking)

        assert result.success is True
        assert booking.session_state == SessionState.CANCELLED.value
        assert booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert booking.payment_state == PaymentState.VOIDED.value
        assert booking.cancelled_by_role == CancelledByRole.TUTOR.value

    def test_expire_booking(self, db_session, test_student, test_tutor):
        """Test expiring a booking request (24h timeout)."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        db_session.commit()

        result = BookingStateMachine.expire_booking(booking)

        assert result.success is True
        assert booking.session_state == SessionState.EXPIRED.value
        assert booking.session_outcome == SessionOutcome.NOT_HELD.value
        assert booking.payment_state == PaymentState.VOIDED.value

    def test_start_session(self, db_session, test_student, test_tutor):
        """Test starting a scheduled session."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        booking.session_state = SessionState.SCHEDULED.value
        db_session.commit()

        result = BookingStateMachine.start_session(booking)

        assert result.success is True
        assert booking.session_state == SessionState.ACTIVE.value

    def test_end_session(self, db_session, test_student, test_tutor):
        """Test ending an active session."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(days=1)
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        booking.session_state = SessionState.ACTIVE.value
        booking.payment_state = PaymentState.AUTHORIZED.value
        db_session.commit()

        result = BookingStateMachine.end_session(booking, SessionOutcome.COMPLETED)

        assert result.success is True
        assert booking.session_state == SessionState.ENDED.value
        assert booking.session_outcome == SessionOutcome.COMPLETED.value
        assert booking.payment_state == PaymentState.CAPTURED.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
