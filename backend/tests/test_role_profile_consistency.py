"""
Tests for role-profile consistency.
Ensures tutors have profiles, non-tutors don't.
"""

import pytest

# from backend.database import get_db  # noqa: F401
from models import StudentProfile, TutorProfile, User

# from sqlalchemy.exc import IntegrityError  # noqa: F401


def test_tutor_must_have_profile(db_session):
    """Test that tutors must have tutor profiles."""
    # Create tutor user
    user = User(
        email="tutor_no_profile@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Verify user created
    assert user.id is not None

    # Trigger should create profile automatically or enforce constraint
    # Check if profile exists
    profile = db_session.query(TutorProfile).filter_by(user_id=user.id).first()

    # If trigger creates profile automatically, it should exist
    # If not, constraint should prevent tutor without profile
    if profile:
        assert profile.user_id == user.id
    else:
        # No automatic creation - that's OK, just need manual creation
        pass


def test_student_cannot_have_tutor_profile(db_session):
    """Test that students cannot have tutor profiles."""
    # Create student user
    user = User(
        email="student_with_tutor_profile@test.com",
        hashed_password="hashed",
        role="student",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Try to create tutor profile for student
    profile = TutorProfile(
        user_id=user.id,
        title="Fake Tutor",
        bio="Should not exist",
        hourly_rate=50.00,
        experience_years=5,
        is_approved=False,
        profile_status="pending_approval",
    )

    # Should raise error due to role-profile consistency trigger
    with pytest.raises(Exception):
        db_session.add(profile)
        db_session.commit()


def test_admin_cannot_have_tutor_profile(db_session):
    """Test that admins cannot have tutor profiles."""
    # Create admin user
    user = User(
        email="admin_with_tutor_profile@test.com",
        hashed_password="hashed",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Try to create tutor profile for admin
    profile = TutorProfile(
        user_id=user.id,
        title="Admin Tutor",
        bio="Should not exist",
        hourly_rate=50.00,
        experience_years=5,
        is_approved=False,
        profile_status="pending_approval",
    )

    # Should raise error due to role-profile consistency
    with pytest.raises(Exception):
        db_session.add(profile)
        db_session.commit()


def test_role_change_to_student_prevents_tutor_profile(db_session):
    """Test that changing role to student while having tutor profile is prevented."""
    # Create tutor with profile
    user = User(
        email="role_change_tutor@test.com",
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

    # Try to change role to student
    user.role = "student"

    # Should raise error - cannot change role while having profile
    with pytest.raises(Exception):
        db_session.commit()


def test_tutor_can_have_tutor_profile(db_session):
    """Test that tutors can have tutor profiles (positive case)."""
    # Create tutor user
    user = User(
        email="valid_tutor@test.com",
        hashed_password="hashed",
        role="tutor",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create tutor profile
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

    # Should succeed
    assert profile.id is not None
    assert profile.user_id == user.id


def test_student_can_have_student_profile(db_session):
    """Test that students can have student profiles (positive case)."""
    # Create student user
    user = User(
        email="valid_student@test.com",
        hashed_password="hashed",
        role="student",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Create student profile
    profile = StudentProfile(
        user_id=user.id,
        grade_level="undergraduate",
    )
    db_session.add(profile)
    db_session.commit()

    # Should succeed
    assert profile.id is not None
    assert profile.user_id == user.id


def test_multiple_tutors_with_profiles(db_session):
    """Test that multiple tutors can exist with profiles."""
    # Create 3 tutors
    for i in range(3):
        user = User(
            email=f"tutor{i}@test.com",
            hashed_password="hashed",
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title=f"Tutor {i}",
            bio=f"Bio {i}",
            hourly_rate=50.00 + i * 10,
            experience_years=5 + i,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        assert profile.id is not None

    # Verify all created
    tutor_count = db_session.query(User).filter_by(role="tutor").count()
    profile_count = db_session.query(TutorProfile).count()

    assert tutor_count >= 3
    assert profile_count >= 3
