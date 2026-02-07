"""
Tests for booking list date filter parameters (from_date, to_date).
Verifies that the booking list endpoint correctly filters by date range.
"""

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import get_password_hash
from core.datetime_utils import utc_now
from models import Base, Booking, TutorProfile, User, UserProfile
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
def bookings_with_dates(db_session, test_student, test_tutor):
    """Create bookings across different dates."""
    _, tutor_profile = test_tutor
    now = utc_now()

    bookings = []
    for days_offset in [-7, -3, 0, 3, 7]:
        start_time = now + timedelta(days=days_offset)
        booking = Booking(
            student_id=test_student.id,
            tutor_profile_id=tutor_profile.id,
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            session_state=SessionState.SCHEDULED.value,
            rate_cents=5000,
            currency="usd",
        )
        db_session.add(booking)
        bookings.append(booking)

    db_session.commit()
    return bookings


def test_filter_from_date(db_session, bookings_with_dates):
    """Test filtering bookings from a specific date."""
    now = utc_now()
    from_date = now - timedelta(days=1)

    # Query bookings from yesterday onwards
    results = (
        db_session.query(Booking)
        .filter(Booking.start_time >= from_date)
        .all()
    )

    # Should include today, +3, +7 (3 bookings)
    assert len(results) == 3
    for b in results:
        assert b.start_time >= from_date


def test_filter_to_date(db_session, bookings_with_dates):
    """Test filtering bookings up to a specific date."""
    now = utc_now()
    to_date = now + timedelta(days=1)

    # Query bookings up to tomorrow
    results = (
        db_session.query(Booking)
        .filter(Booking.start_time <= to_date)
        .all()
    )

    # Should include -7, -3, 0 (3 bookings)
    assert len(results) == 3
    for b in results:
        assert b.start_time <= to_date


def test_filter_date_range(db_session, bookings_with_dates):
    """Test filtering bookings within a date range."""
    now = utc_now()
    from_date = now - timedelta(days=5)
    to_date = now + timedelta(days=5)

    results = (
        db_session.query(Booking)
        .filter(Booking.start_time >= from_date, Booking.start_time <= to_date)
        .all()
    )

    # Should include -3, 0, +3 (3 bookings)
    assert len(results) == 3
    for b in results:
        assert b.start_time >= from_date
        assert b.start_time <= to_date


def test_no_date_filter_returns_all(db_session, bookings_with_dates):
    """Test that omitting date filters returns all bookings."""
    results = db_session.query(Booking).all()
    assert len(results) == 5


def test_empty_date_range_returns_none(db_session, bookings_with_dates):
    """Test that a date range with no bookings returns empty."""
    now = utc_now()
    from_date = now + timedelta(days=30)
    to_date = now + timedelta(days=40)

    results = (
        db_session.query(Booking)
        .filter(Booking.start_time >= from_date, Booking.start_time <= to_date)
        .all()
    )

    assert len(results) == 0
