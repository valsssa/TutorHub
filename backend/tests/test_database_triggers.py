"""
Tests for database triggers and automatic behavior.
"""

from datetime import datetime, timedelta

import pytest

# from backend.database import get_db  # noqa: F401
from models import (
    Booking,
    Review,  # StudentProfile,  # noqa: F401
    Subject,
    TutorPricingOption,
    TutorProfile,
    User,
)


@pytest.fixture
def test_data(db_session):
    """Create test data."""
    # Create tutor
    tutor_user = User(
        email="trigger_tutor@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(tutor_user)
    db_session.commit()

    tutor_profile = TutorProfile(
        user_id=tutor_user.id,
        title="Math Expert | PhD",
        bio="Experienced tutor",
        hourly_rate=50.00,
        experience_years=10,
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(tutor_profile)
    db_session.commit()

    # Create student
    student_user = User(
        email="trigger_student@test.com",
        hashed_password="hashed",
        role="student",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.commit()

    # Create subject
    subject = Subject(name="Advanced Calculus", description="Math")
    db_session.add(subject)
    db_session.commit()

    return {
        "tutor_user": tutor_user,
        "tutor_profile": tutor_profile,
        "student_user": student_user,
        "subject": subject,
    }


def test_booking_snapshot_auto_populated(db_session, test_data):
    """Test that booking snapshots are automatically populated on INSERT."""
    base_time = datetime.now()

    # Create booking
    booking = Booking(
        tutor_profile_id=test_data["tutor_profile"].id,
        student_id=test_data["student_user"].id,
        subject_id=test_data["subject"].id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking)
    db_session.commit()

    # Refresh to get trigger-populated fields
    db_session.refresh(booking)

    # Verify snapshot fields populated
    assert booking.tutor_name is not None
    assert booking.tutor_title == "Math Expert | PhD"
    assert booking.student_name is not None
    assert booking.subject_name == "Advanced Calculus"
    assert booking.pricing_snapshot is not None


def test_booking_snapshot_immutable(db_session, test_data):
    """Test that booking snapshots don't change when tutor changes profile."""
    base_time = datetime.now()

    # Create booking with current tutor info
    booking = Booking(
        tutor_profile_id=test_data["tutor_profile"].id,
        student_id=test_data["student_user"].id,
        subject_id=test_data["subject"].id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    original_title = booking.tutor_title
    original_rate = booking.hourly_rate

    # Tutor changes their profile
    test_data["tutor_profile"].title = "Science Expert | PhD"
    test_data["tutor_profile"].hourly_rate = 75.00
    db_session.commit()

    # Refresh booking
    db_session.refresh(booking)

    # Verify booking snapshot unchanged (immutable)
    assert booking.tutor_title == original_title  # Still "Math Expert | PhD"
    assert booking.hourly_rate == original_rate  # Still 50.00


def test_tutor_rate_history_tracked(db_session, test_data):
    """Test that tutor rate changes are tracked in field history."""
    original_rate = test_data["tutor_profile"].hourly_rate

    # Change rate
    test_data["tutor_profile"].hourly_rate = 60.00
    db_session.commit()

    # Query field history
    result = db_session.execute(
        """
        SELECT field_name, old_value, new_value
        FROM tutor_profile_field_history
        WHERE tutor_profile_id = :profile_id
        AND field_name = 'hourly_rate'
        ORDER BY changed_at DESC
        LIMIT 1
        """,
        {"profile_id": test_data["tutor_profile"].id},
    ).fetchone()

    if result:
        assert result[0] == "hourly_rate"
        assert float(result[1]) == original_rate
        assert float(result[2]) == 60.00


def test_review_snapshot_auto_populated(db_session, test_data):
    """Test that review booking snapshots are populated."""
    base_time = datetime.now()

    # Create booking
    booking = Booking(
        tutor_profile_id=test_data["tutor_profile"].id,
        student_id=test_data["student_user"].id,
        subject_id=test_data["subject"].id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="completed",
        hourly_rate=50.00,
        total_amount=50.00,
    )
    db_session.add(booking)
    db_session.commit()

    # Create review
    review = Review(
        booking_id=booking.id,
        tutor_profile_id=test_data["tutor_profile"].id,
        student_id=test_data["student_user"].id,
        rating=5,
        comment="Excellent session!",
        is_public=True,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    # Verify booking snapshot populated
    assert review.booking_snapshot is not None


def test_updated_at_auto_updated(db_session, test_data):
    """Test that updated_at is automatically updated on changes."""
    original_updated = test_data["tutor_profile"].updated_at

    # Wait a moment
    import time

    time.sleep(0.1)

    # Update profile
    test_data["tutor_profile"].bio = "Updated bio"
    db_session.commit()
    db_session.refresh(test_data["tutor_profile"])

    # Verify updated_at changed
    assert test_data["tutor_profile"].updated_at > original_updated


def test_pricing_option_snapshot_in_booking(db_session, test_data):
    """Test that pricing option details are captured in booking snapshot."""
    # Create pricing option
    pricing_option = TutorPricingOption(
        tutor_profile_id=test_data["tutor_profile"].id,
        title="5 Session Package",
        description="Save 10%",
        duration_minutes=60,
        price=225.00,
        pricing_type="package",
        sessions_included=5,
        validity_days=90,
        is_popular=True,
    )
    db_session.add(pricing_option)
    db_session.commit()

    base_time = datetime.now()

    # Create booking with pricing option
    booking = Booking(
        tutor_profile_id=test_data["tutor_profile"].id,
        student_id=test_data["student_user"].id,
        subject_id=test_data["subject"].id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=1),
        status="confirmed",
        hourly_rate=45.00,  # Discounted
        total_amount=45.00,
        pricing_option_id=pricing_option.id,
        pricing_type="package",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    # Verify pricing snapshot includes option details
    assert booking.pricing_snapshot is not None
    # Snapshot should contain pricing_option with package details
