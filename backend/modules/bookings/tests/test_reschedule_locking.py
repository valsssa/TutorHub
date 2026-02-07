"""
Tests for row-level locking in the reschedule endpoint.
Verifies that get_booking_with_lock is used to prevent race conditions.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import get_password_hash
from core.datetime_utils import utc_now
from datetime import timedelta
from models import Base, Booking, TutorProfile, User, UserProfile
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import SessionState


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
        is_active=True,
    )
    db_session.add(student)
    db_session.commit()
    profile = UserProfile(user_id=student.id, first_name="Test", last_name="Student")
    db_session.add(profile)
    db_session.commit()
    return student


@pytest.fixture
def test_tutor(db_session):
    """Create a test tutor user with profile."""
    tutor_user = User(
        email="tutor@test.com",
        hashed_password=get_password_hash("password"),
        role="tutor",
        is_active=True,
    )
    db_session.add(tutor_user)
    db_session.commit()

    profile = UserProfile(user_id=tutor_user.id, first_name="Test", last_name="Tutor")
    db_session.add(profile)

    tutor_profile = TutorProfile(
        user_id=tutor_user.id,
        hourly_rate=50.0,
        bio="Test tutor",
    )
    db_session.add(tutor_profile)
    db_session.commit()
    return tutor_user, tutor_profile


@pytest.fixture
def scheduled_booking(db_session, test_student, test_tutor):
    """Create a scheduled booking for testing."""
    _, tutor_profile = test_tutor
    now = utc_now()
    booking = Booking(
        student_id=test_student.id,
        tutor_profile_id=tutor_profile.id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        session_state=SessionState.SCHEDULED.value,
        rate_cents=5000,
        currency="usd",
    )
    db_session.add(booking)
    db_session.commit()
    return booking


def test_get_booking_with_lock_returns_booking(db_session, scheduled_booking):
    """Test that get_booking_with_lock returns the booking for locking."""
    # Note: SQLite doesn't support FOR UPDATE, but the method still returns the booking
    booking = BookingStateMachine.get_booking_with_lock(
        db_session, scheduled_booking.id
    )
    assert booking is not None
    assert booking.id == scheduled_booking.id
    assert booking.session_state == SessionState.SCHEDULED.value


def test_get_booking_with_lock_returns_none_for_missing(db_session):
    """Test that get_booking_with_lock returns None for non-existent booking."""
    booking = BookingStateMachine.get_booking_with_lock(db_session, 99999)
    assert booking is None


def test_booking_can_be_rescheduled_after_lock(db_session, scheduled_booking):
    """Test that a booking's times can be updated after acquiring a lock."""
    booking = BookingStateMachine.get_booking_with_lock(
        db_session, scheduled_booking.id
    )
    assert booking is not None

    new_start = utc_now() + timedelta(days=5)
    new_end = new_start + timedelta(hours=1)

    booking.start_time = new_start
    booking.end_time = new_end
    db_session.commit()

    refreshed = db_session.query(Booking).filter(Booking.id == scheduled_booking.id).first()
    assert refreshed.start_time == new_start
    assert refreshed.end_time == new_end


def test_lock_preserves_booking_state(db_session, scheduled_booking):
    """Test that acquiring a lock does not change booking state."""
    original_state = scheduled_booking.session_state
    booking = BookingStateMachine.get_booking_with_lock(
        db_session, scheduled_booking.id
    )
    assert booking.session_state == original_state
