"""
Tests for booking conflict prevention.
Ensures tutors can't have overlapping bookings.
"""

from datetime import datetime, timedelta

import pytest

# from backend.database import get_db  # noqa: F401
from models import Booking, Subject, TutorProfile, User

# from sqlalchemy.exc import IntegrityError  # noqa: F401


@pytest.fixture
def test_tutor(db_session):
    """Create test tutor."""
    user = User(
        email="conflict_tutor@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    profile = TutorProfile(
        user_id=user.id,
        title="Math Tutor",
        bio="Test bio",
        hourly_rate=50.00,
        experience_years=5,
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(profile)
    db_session.commit()

    return profile


@pytest.fixture
def test_student(db_session):
    """Create test student."""
    user = User(
        email="conflict_student@test.com",
        hashed_password="hashed",
        role="student",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_subject(db_session):
    """Create test subject."""
    subject = Subject(name="Mathematics", description="Math subject")
    db_session.add(subject)
    db_session.commit()
    return subject


def test_can_create_non_overlapping_bookings(db_session, test_tutor, test_student, test_subject):
    """Test that non-overlapping bookings can be created."""
    base_time = datetime.now()

    # Booking 1: 10:00-11:00
    booking1 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: 12:00-13:00 (2 hours later, no overlap)
    booking2 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time + timedelta(hours=2),
        end_time=base_time + timedelta(hours=3),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking2)
    db_session.commit()

    # Should succeed
    assert booking1.id is not None
    assert booking2.id is not None


def test_overlapping_bookings_rejected(db_session, test_tutor, test_student, test_subject):
    """Test that overlapping bookings are rejected."""
    base_time = datetime.now()

    # Booking 1: 10:00-12:00
    booking1 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=2),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=100.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: 11:00-13:00 (overlaps with booking1)
    booking2 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time + timedelta(hours=1),
        end_time=base_time + timedelta(hours=3),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=100.00,
    )

    # Should raise IntegrityError due to conflict
    with pytest.raises(Exception) as exc_info:
        db_session.add(booking2)
        db_session.commit()

    assert "booking conflict" in str(exc_info.value).lower() or "overlaps" in str(exc_info.value).lower()


def test_cancelled_bookings_allow_overlap(db_session, test_tutor, test_student, test_subject):
    """Test that cancelled bookings don't block same time slot."""
    base_time = datetime.now()

    # Booking 1: 10:00-11:00, cancelled
    booking1 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="cancelled",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: 10:00-11:00, confirmed (same time as cancelled)
    booking2 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking2)
    db_session.commit()

    # Should succeed because booking1 is cancelled
    assert booking2.id is not None


def test_different_tutors_same_time(db_session, test_student, test_subject):
    """Test that different tutors can book same time slot."""
    base_time = datetime.now()

    # Create second tutor
    user2 = User(
        email="tutor2@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(user2)
    db_session.commit()

    profile2 = TutorProfile(
        user_id=user2.id,
        title="Science Tutor",
        bio="Test bio",
        hourly_rate=40.00,
        experience_years=3,
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(profile2)
    db_session.commit()

    # Get first tutor
    user1 = User(
        email="tutor1@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(user1)
    db_session.commit()

    profile1 = TutorProfile(
        user_id=user1.id,
        title="Math Tutor",
        bio="Test bio",
        hourly_rate=50.00,
        experience_years=5,
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(profile1)
    db_session.commit()

    # Booking 1: Tutor 1, 10:00-11:00
    booking1 = Booking(
        tutor_profile_id=profile1.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: Tutor 2, 10:00-11:00 (same time, different tutor)
    booking2 = Booking(
        tutor_profile_id=profile2.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=40.00,
        total_amount=40.00,
    )
    db_session.add(booking2)
    db_session.commit()

    # Should succeed because different tutors
    assert booking1.id is not None
    assert booking2.id is not None


def test_exact_end_time_matches_next_start(db_session, test_tutor, test_student, test_subject):
    """Test that back-to-back bookings (end=start) are allowed."""
    base_time = datetime.now()

    # Booking 1: 10:00-11:00
    booking1 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: 11:00-12:00 (starts exactly when booking1 ends)
    booking2 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time + timedelta(hours=1),
        end_time=base_time + timedelta(hours=2),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking2)
    db_session.commit()

    # Should succeed (no overlap, back-to-back is OK)
    assert booking1.id is not None
    assert booking2.id is not None


def test_pending_bookings_also_checked(db_session, test_tutor, test_student, test_subject):
    """Test that pending bookings also prevent conflicts."""
    base_time = datetime.now()

    # Booking 1: 10:00-11:00, pending
    booking1 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="pending",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking1)
    db_session.commit()

    # Booking 2: 10:00-11:00, confirmed (overlaps with pending)
    booking2 = Booking(
        tutor_profile_id=test_tutor.id,
        student_id=test_student.id,
        subject_id=test_subject.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )

    # Should raise error (pending bookings also block)
    with pytest.raises(Exception) as exc_info:
        db_session.add(booking2)
        db_session.commit()

    assert "booking conflict" in str(exc_info.value).lower() or "overlaps" in str(exc_info.value).lower()
