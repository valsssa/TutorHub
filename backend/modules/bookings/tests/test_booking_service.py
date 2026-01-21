"""
Tests for booking service business logic.
Tests booking creation, conflict checking, state transitions.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import get_password_hash
from models import Base, TutorProfile, User, UserProfile
from modules.bookings.service import BookingService, can_transition

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
    """Test booking state transitions."""

    def test_valid_transitions(self):
        """Test all valid state transitions."""
        assert can_transition("PENDING", "CONFIRMED") is True
        assert can_transition("PENDING", "CANCELLED_BY_STUDENT") is True
        assert can_transition("CONFIRMED", "COMPLETED") is True
        assert can_transition("CONFIRMED", "NO_SHOW_STUDENT") is True
        assert can_transition("CONFIRMED", "NO_SHOW_TUTOR") is True

    def test_invalid_transitions(self):
        """Test invalid state transitions."""
        assert can_transition("COMPLETED", "PENDING") is False
        assert can_transition("CANCELLED_BY_STUDENT", "CONFIRMED") is False
        assert can_transition("NO_SHOW_STUDENT", "COMPLETED") is False

    def test_terminal_states_no_transitions(self):
        """Terminal states should have no valid transitions (except refund for completed)."""
        assert can_transition("CANCELLED_BY_STUDENT", "ANYTHING") is False
        assert can_transition("NO_SHOW_STUDENT", "ANYTHING") is False


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

        assert booking.status == "CONFIRMED"
        assert booking.join_url is not None

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


# ============================================================================
# Cancellation Tests
# ============================================================================


class TestCancellation:
    """Test booking cancellation logic."""

    def test_student_cancels_early(self, db_session, test_student, test_tutor):
        """Student cancels 24h before: allowed with refund."""
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

        _ = service.cancel_booking(
            booking=booking,
            cancelled_by_role="STUDENT",
            reason="Need to reschedule",
        )
        db_session.refresh(booking)

        assert booking.status == "CANCELLED_BY_STUDENT"

    def test_tutor_cancels_late_gets_strike(self, db_session, test_student, test_tutor):
        """Tutor cancels < 12h: gets penalty strike."""
        service = BookingService(db_session)
        start_at = datetime.utcnow() + timedelta(hours=6)  # 6h away
        tutor_profile = _get_tutor_profile(db_session, test_tutor)

        booking = service.create_booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_at=start_at,
            duration_minutes=60,
        )
        booking.status = "CONFIRMED"
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


# ============================================================================
# No-Show Tests
# ============================================================================


class TestNoShow:
    """Test no-show marking logic."""

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
        booking.status = "CONFIRMED"
        db_session.commit()

        marked = service.mark_no_show(
            booking=booking,
            reporter_role="TUTOR",
            notes="Student didn't join",
        )

        assert marked.status == "NO_SHOW_STUDENT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
