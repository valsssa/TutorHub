"""
Comprehensive tests for the Tutor Profile module.

Tests cover:
- Profile creation and updates
- Subject management (add, remove, update proficiency)
- Education and certification management
- Pricing options (hourly, packages)
- Availability management
- Blackout period handling
- Profile visibility (approved vs pending)
- Search ranking factors
- Profile photo upload
- Authorization (only tutor can edit own profile)
- Validation (required fields, formats)
- State transitions (pending -> approved)
"""

from datetime import UTC, datetime, time, timedelta

from core.datetime_utils import utc_now
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi import status
from PIL import Image
from sqlalchemy.orm import Session

from auth import get_password_hash
from models import (
    Subject,
    TutorAvailability,
    TutorBlackout,
    TutorCertification,
    TutorEducation,
    TutorPricingOption,
    TutorProfile,
    TutorSubject,
    User,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tutor_without_profile(db_session: Session) -> User:
    """Create a tutor user without an existing profile."""
    user = User(
        email="newtutor@test.com",
        hashed_password=get_password_hash("tutor123"),
        role="tutor",
        is_verified=True,
        is_active=True,
        first_name="New",
        last_name="Tutor",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tutor_without_profile_token(client, tutor_without_profile: User) -> str:
    """Get auth token for tutor without profile."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": tutor_without_profile.email, "password": "tutor123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def second_tutor(db_session: Session) -> User:
    """Create a second tutor for authorization tests."""
    user = User(
        email="tutor2@test.com",
        hashed_password=get_password_hash("tutor123"),
        role="tutor",
        is_verified=True,
        is_active=True,
        first_name="Second",
        last_name="Tutor",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()

    profile = TutorProfile(
        user_id=user.id,
        title="Second Tutor Profile",
        headline="Secondary tutor",
        bio="Another tutor for testing",
        hourly_rate=Decimal("45.00"),
        experience_years=5,
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_tutor_token(client, second_tutor: User) -> str:
    """Get auth token for second tutor."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": second_tutor.email, "password": "tutor123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def multiple_subjects(db_session: Session) -> list[Subject]:
    """Create multiple test subjects."""
    subjects = [
        Subject(name="Mathematics", description="Math tutoring", category="STEM", is_active=True),
        Subject(name="Physics", description="Physics tutoring", category="STEM", is_active=True),
        Subject(name="Chemistry", description="Chemistry tutoring", category="STEM", is_active=True),
        Subject(name="English", description="English tutoring", category="Languages", is_active=True),
    ]
    for subject in subjects:
        db_session.add(subject)
    db_session.commit()
    for subject in subjects:
        db_session.refresh(subject)
    return subjects


@pytest.fixture
def tutor_with_complete_profile(db_session: Session, multiple_subjects: list[Subject]) -> User:
    """Create a tutor with a complete profile ready for approval."""
    user = User(
        email="completetutor@test.com",
        hashed_password=get_password_hash("tutor123"),
        role="tutor",
        is_verified=True,
        is_active=True,
        first_name="Complete",
        last_name="Tutor",
        avatar_key="https://example.com/photo.jpg",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()

    profile = TutorProfile(
        user_id=user.id,
        title="Complete Professional Tutor",
        headline="15 years teaching experience",
        bio="I am passionate about education and have helped hundreds of students.",
        description="A" * 450,  # Min 400 chars required for submission
        hourly_rate=Decimal("75.00"),
        experience_years=15,
        education="PhD in Education",
        languages=["en", "es"],
        is_approved=False,
        profile_status="incomplete",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add subjects
    subject_rel = TutorSubject(
        tutor_profile_id=profile.id,
        subject_id=multiple_subjects[0].id,
        proficiency_level="c2",
        years_experience=10,
    )
    db_session.add(subject_rel)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def complete_tutor_token(client, tutor_with_complete_profile: User) -> str:
    """Get auth token for complete tutor."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": tutor_with_complete_profile.email, "password": "tutor123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


# ============================================================================
# Profile Creation and Retrieval Tests
# ============================================================================


class TestTutorProfileCreation:
    """Test tutor profile creation and auto-initialization."""

    def test_get_my_profile_creates_profile_lazily(
        self, client, tutor_without_profile_token, tutor_without_profile
    ):
        """Test that accessing /me/profile creates a profile if one doesn't exist."""
        response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_without_profile_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == tutor_without_profile.id
        assert data["profile_status"] == "incomplete"
        assert data["is_approved"] is False

    def test_get_my_profile_returns_existing_profile(self, client, tutor_token, tutor_user):
        """Test that existing profile is returned correctly."""
        response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == tutor_user.id
        assert "subjects" in data
        assert "availabilities" in data
        assert "certifications" in data
        assert "educations" in data
        assert "pricing_options" in data


class TestProfileAuthorization:
    """Test authorization for profile operations."""

    def test_student_cannot_access_tutor_profile_endpoint(self, client, student_token):
        """Test that students cannot access tutor-only endpoints."""
        response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_my_profile(self, client):
        """Test that unauthenticated users cannot access protected endpoints."""
        response = client.get("/api/v1/tutors/me/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_tutor_can_only_update_own_profile(
        self, client, tutor_token, second_tutor, db_session
    ):
        """Test that tutors can only update their own profiles."""
        # Tutor trying to update about section - only affects own profile
        response = client.patch(
            "/api/v1/tutors/me/about",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "title": "Trying to update another profile",
                "experience_years": 5,
            },
        )
        # Should succeed but only update own profile
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Trying to update another profile"

        # Second tutor's profile should be unchanged
        db_session.refresh(second_tutor)
        second_profile = (
            db_session.query(TutorProfile)
            .filter(TutorProfile.user_id == second_tutor.id)
            .first()
        )
        assert second_profile.title == "Second Tutor Profile"


# ============================================================================
# About Section Tests
# ============================================================================


class TestAboutSection:
    """Test updating the about/title/headline section."""

    def test_update_about_success(self, client, tutor_token):
        """Test successful about section update."""
        response = client.patch(
            "/api/v1/tutors/me/about",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "title": "Senior Mathematics Tutor",
                "headline": "20 years of excellence in teaching",
                "bio": "I love helping students succeed in math.",
                "experience_years": 20,
                "languages": ["en", "es", "fr"],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Senior Mathematics Tutor"
        assert data["headline"] == "20 years of excellence in teaching"
        assert data["experience_years"] == 20

    def test_update_about_title_validation(self, client, tutor_token):
        """Test title validation (min 5 chars)."""
        response = client.patch(
            "/api/v1/tutors/me/about",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "title": "Hi",  # Too short
                "experience_years": 5,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_about_invalid_language_code(self, client, tutor_token):
        """Test that invalid language codes are rejected."""
        response = client.patch(
            "/api/v1/tutors/me/about",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "title": "Valid Title Here",
                "experience_years": 5,
                "languages": ["english"],  # Should be 'en', not 'english'
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Subject Management Tests
# ============================================================================


class TestSubjectManagement:
    """Test subject add, remove, and update operations."""

    def test_replace_subjects_success(self, client, tutor_token, multiple_subjects):
        """Test replacing all subjects."""
        response = client.put(
            "/api/v1/tutors/me/subjects",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "subject_id": multiple_subjects[0].id,
                    "proficiency_level": "c2",
                    "years_experience": 10,
                },
                {
                    "subject_id": multiple_subjects[1].id,
                    "proficiency_level": "c1",
                    "years_experience": 5,
                },
            ],
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["subjects"]) == 2
        subject_ids = [s["subject_id"] for s in data["subjects"]]
        assert multiple_subjects[0].id in subject_ids
        assert multiple_subjects[1].id in subject_ids

    def test_replace_subjects_clears_old_subjects(
        self, client, tutor_token, multiple_subjects, db_session, tutor_user
    ):
        """Test that replacing subjects removes old ones."""
        # Add initial subjects
        profile = tutor_user.tutor_profile
        for subject in multiple_subjects[:2]:
            ts = TutorSubject(
                tutor_profile_id=profile.id,
                subject_id=subject.id,
                proficiency_level="b2",
            )
            db_session.add(ts)
        db_session.commit()

        # Replace with single subject
        response = client.put(
            "/api/v1/tutors/me/subjects",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "subject_id": multiple_subjects[2].id,
                    "proficiency_level": "c1",
                    "years_experience": 3,
                }
            ],
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["subjects"]) == 1
        assert data["subjects"][0]["subject_id"] == multiple_subjects[2].id

    def test_update_subject_proficiency_level(self, client, tutor_token, multiple_subjects):
        """Test updating subject proficiency level."""
        # Add subject
        client.put(
            "/api/v1/tutors/me/subjects",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "subject_id": multiple_subjects[0].id,
                    "proficiency_level": "b2",
                    "years_experience": 5,
                }
            ],
        )

        # Update proficiency
        response = client.put(
            "/api/v1/tutors/me/subjects",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "subject_id": multiple_subjects[0].id,
                    "proficiency_level": "c2",
                    "years_experience": 8,
                }
            ],
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["subjects"][0]["proficiency_level"] == "c2"
        assert data["subjects"][0]["years_experience"] == 8

    def test_invalid_proficiency_level_rejected(self, client, tutor_token, multiple_subjects):
        """Test that invalid CEFR levels are rejected."""
        response = client.put(
            "/api/v1/tutors/me/subjects",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "subject_id": multiple_subjects[0].id,
                    "proficiency_level": "expert",  # Not a valid CEFR level
                    "years_experience": 5,
                }
            ],
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Education Management Tests
# ============================================================================


class TestEducationManagement:
    """Test education entry management."""

    def test_replace_education_success(self, client, tutor_token):
        """Test replacing education entries."""
        import json

        response = client.put(
            "/api/v1/tutors/me/education",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "education": json.dumps([
                    {
                        "institution": "MIT",
                        "degree": "Bachelor of Science",
                        "field_of_study": "Mathematics",
                        "start_year": 2015,
                        "end_year": 2019,
                        "description": "Focus on applied mathematics",
                    },
                    {
                        "institution": "Stanford",
                        "degree": "Master of Science",
                        "field_of_study": "Education",
                        "start_year": 2019,
                        "end_year": 2021,
                    },
                ])
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["educations"]) == 2

    def test_education_year_validation(self, client, tutor_token):
        """Test that end_year cannot be before start_year."""
        import json

        response = client.put(
            "/api/v1/tutors/me/education",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "education": json.dumps([
                    {
                        "institution": "University",
                        "degree": "BS",
                        "field_of_study": "Math",
                        "start_year": 2020,
                        "end_year": 2018,  # Invalid: before start
                    }
                ])
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_education_institution_required(self, client, tutor_token):
        """Test that institution is required."""
        import json

        response = client.put(
            "/api/v1/tutors/me/education",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "education": json.dumps([
                    {
                        "degree": "BS",
                        "field_of_study": "Math",
                        # Missing institution
                    }
                ])
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Certification Management Tests
# ============================================================================


class TestCertificationManagement:
    """Test certification management."""

    def test_replace_certifications_success(self, client, tutor_token):
        """Test replacing certifications."""
        import json

        response = client.put(
            "/api/v1/tutors/me/certifications",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "certifications": json.dumps([
                    {
                        "name": "Teaching Certificate",
                        "issuing_organization": "State Board of Education",
                        "issue_date": "2020-01-15",
                        "credential_id": "CERT-12345",
                    },
                    {
                        "name": "CPR Certification",
                        "issuing_organization": "Red Cross",
                        "issue_date": "2024-01-01",
                        "expiration_date": "2026-01-01",
                    },
                ])
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["certifications"]) == 2

    def test_certification_expiration_validation(self, client, tutor_token):
        """Test that expiration_date cannot be before issue_date."""
        import json

        response = client.put(
            "/api/v1/tutors/me/certifications",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "certifications": json.dumps([
                    {
                        "name": "Certificate",
                        "issuing_organization": "Org",
                        "issue_date": "2025-01-01",
                        "expiration_date": "2024-01-01",  # Invalid: before issue
                    }
                ])
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_certification_name_required(self, client, tutor_token):
        """Test that certification name is required."""
        import json

        response = client.put(
            "/api/v1/tutors/me/certifications",
            headers={"Authorization": f"Bearer {tutor_token}"},
            data={
                "certifications": json.dumps([
                    {
                        "issuing_organization": "Org",
                        # Missing name
                    }
                ])
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Pricing Options Tests
# ============================================================================


class TestPricingOptions:
    """Test pricing options management."""

    def test_update_hourly_rate(self, client, tutor_token, db_session, tutor_user):
        """Test updating hourly rate."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.patch(
            "/api/v1/tutors/me/pricing",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "hourly_rate": "75.00",
                "pricing_options": [],
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert Decimal(data["hourly_rate"]) == Decimal("75.00")

    def test_add_pricing_packages(self, client, tutor_token, db_session, tutor_user):
        """Test adding pricing packages."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.patch(
            "/api/v1/tutors/me/pricing",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "hourly_rate": "50.00",
                "pricing_options": [
                    {
                        "title": "Single Session",
                        "description": "One hour tutoring session",
                        "duration_minutes": 60,
                        "price": "50.00",
                    },
                    {
                        "title": "5-Pack Sessions",
                        "description": "Five one-hour sessions at a discount",
                        "duration_minutes": 300,
                        "price": "225.00",
                    },
                ],
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["pricing_options"]) == 2

    def test_pricing_optimistic_locking(self, client, tutor_token, db_session, tutor_user):
        """Test that stale version causes conflict error."""
        db_session.refresh(tutor_user.tutor_profile)
        stale_version = 0  # Definitely wrong

        response = client.patch(
            "/api/v1/tutors/me/pricing",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "hourly_rate": "75.00",
                "pricing_options": [],
                "version": stale_version,
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "modified by another request" in response.json()["detail"]

    def test_invalid_hourly_rate_rejected(self, client, tutor_token, db_session, tutor_user):
        """Test that invalid hourly rates are rejected."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.patch(
            "/api/v1/tutors/me/pricing",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "hourly_rate": "-10.00",  # Invalid: negative
                "pricing_options": [],
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Availability Management Tests
# ============================================================================


class TestAvailabilityManagement:
    """Test availability slot management."""

    def test_replace_availability_success(self, client, tutor_token, db_session, tutor_user):
        """Test replacing availability slots."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.put(
            "/api/v1/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 1,  # Monday
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    },
                    {
                        "day_of_week": 3,  # Wednesday
                        "start_time": "10:00:00",
                        "end_time": "16:00:00",
                        "is_recurring": True,
                    },
                ],
                "timezone": "America/New_York",
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["availabilities"]) == 2

    def test_availability_end_time_validation(self, client, tutor_token, db_session, tutor_user):
        """Test that end_time must be after start_time."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.put(
            "/api/v1/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 1,
                        "start_time": "17:00:00",
                        "end_time": "09:00:00",  # Invalid: before start
                        "is_recurring": True,
                    }
                ],
                "timezone": "UTC",
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_availability_day_of_week_validation(self, client, tutor_token, db_session, tutor_user):
        """Test that day_of_week must be 0-6."""
        db_session.refresh(tutor_user.tutor_profile)
        current_version = tutor_user.tutor_profile.version or 1

        response = client.put(
            "/api/v1/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 7,  # Invalid: must be 0-6
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "UTC",
                "version": current_version,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_availability_optimistic_locking(self, client, tutor_token, db_session, tutor_user):
        """Test availability optimistic locking."""
        response = client.put(
            "/api/v1/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 1,
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "UTC",
                "version": 0,  # Stale version
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT


# ============================================================================
# Availability API Tests (availability_api.py endpoints)
# ============================================================================


class TestAvailabilityAPI:
    """Test availability API endpoints."""

    def test_get_my_availability(self, client, tutor_token, db_session, tutor_user):
        """Test getting own availability."""
        # Add some availability first
        availability = TutorAvailability(
            tutor_profile_id=tutor_user.tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()

        response = client.get(
            "/api/v1/tutors/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

    def test_create_availability_success(self, client, tutor_token):
        """Test creating single availability slot."""
        response = client.post(
            "/api/v1/tutors/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "day_of_week": 2,  # Tuesday
                "start_time": "10:00:00",
                "end_time": "18:00:00",
                "is_recurring": True,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["day_of_week"] == 2

    def test_create_availability_overlap_rejected(self, client, tutor_token, db_session, tutor_user):
        """Test that overlapping availability is rejected."""
        # Create initial availability
        availability = TutorAvailability(
            tutor_profile_id=tutor_user.tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()

        # Try to create overlapping slot
        response = client.post(
            "/api/v1/tutors/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "day_of_week": 1,  # Same day
                "start_time": "15:00:00",  # Overlaps with 9-17
                "end_time": "19:00:00",
                "is_recurring": True,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "overlaps" in response.json()["detail"].lower()

    def test_delete_availability_success(self, client, tutor_token, db_session, tutor_user):
        """Test deleting availability slot."""
        availability = TutorAvailability(
            tutor_profile_id=tutor_user.tutor_profile.id,
            day_of_week=5,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()
        availability_id = availability.id

        response = client.delete(
            f"/api/v1/tutors/availability/{availability_id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_other_tutor_availability(
        self, client, tutor_token, db_session, second_tutor
    ):
        """Test that tutors cannot delete another tutor's availability."""
        second_profile = (
            db_session.query(TutorProfile)
            .filter(TutorProfile.user_id == second_tutor.id)
            .first()
        )
        availability = TutorAvailability(
            tutor_profile_id=second_profile.id,
            day_of_week=4,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()

        response = client.delete(
            f"/api/v1/tutors/availability/{availability.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_bulk_availability_success(self, client, tutor_token):
        """Test bulk availability creation."""
        response = client.post(
            "/api/v1/tutors/availability/bulk",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
                {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
                {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
            ],
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["count"] == 3


# ============================================================================
# Blackout Period Tests
# ============================================================================


class TestBlackoutPeriods:
    """Test blackout period management."""

    def test_create_blackout_success(self, client, tutor_token):
        """Test creating a blackout period."""
        start_dt = utc_now() + timedelta(days=7)
        end_dt = start_dt + timedelta(days=3)

        response = client.post(
            "/api/v1/tutors/blackouts",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "reason": "Holiday vacation",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "blackout" in data
        assert data["blackout"]["reason"] == "Holiday vacation"

    def test_create_blackout_invalid_time_range(self, client, tutor_token):
        """Test that end must be after start."""
        start_dt = utc_now() + timedelta(days=10)
        end_dt = start_dt - timedelta(days=1)  # Invalid: before start

        response = client.post(
            "/api/v1/tutors/blackouts",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "reason": "Invalid blackout",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_my_blackouts(self, client, tutor_token, db_session, tutor_user):
        """Test getting own blackouts."""
        blackout = TutorBlackout(
            tutor_id=tutor_user.id,
            start_at=utc_now() + timedelta(days=14),
            end_at=utc_now() + timedelta(days=17),
            reason="Conference",
        )
        db_session.add(blackout)
        db_session.commit()

        response = client.get(
            "/api/v1/tutors/blackouts",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

    def test_delete_blackout_success(self, client, tutor_token, db_session, tutor_user):
        """Test deleting a blackout period."""
        blackout = TutorBlackout(
            tutor_id=tutor_user.id,
            start_at=utc_now() + timedelta(days=20),
            end_at=utc_now() + timedelta(days=22),
            reason="To be deleted",
        )
        db_session.add(blackout)
        db_session.commit()
        blackout_id = blackout.id

        response = client.delete(
            f"/api/v1/tutors/blackouts/{blackout_id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_other_tutor_blackout(
        self, client, tutor_token, db_session, second_tutor
    ):
        """Test that tutors cannot delete another tutor's blackout."""
        blackout = TutorBlackout(
            tutor_id=second_tutor.id,
            start_at=utc_now() + timedelta(days=25),
            end_at=utc_now() + timedelta(days=27),
            reason="Other tutor's blackout",
        )
        db_session.add(blackout)
        db_session.commit()

        response = client.delete(
            f"/api/v1/tutors/blackouts/{blackout.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Profile Visibility Tests
# ============================================================================


class TestProfileVisibility:
    """Test profile visibility based on approval status."""

    def test_approved_profile_visible_in_list(self, client, student_token, tutor_user):
        """Test that approved profiles appear in public listing."""
        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # tutor_user fixture creates an approved profile
        tutor_ids = [t["id"] for t in data["items"]]
        assert tutor_user.tutor_profile.id in tutor_ids

    def test_unapproved_profile_not_in_list(
        self, client, student_token, db_session, tutor_without_profile
    ):
        """Test that unapproved profiles do not appear in public listing."""
        # Create unapproved profile
        profile = TutorProfile(
            user_id=tutor_without_profile.id,
            title="Unapproved Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        tutor_ids = [t["id"] for t in data["items"]]
        assert profile.id not in tutor_ids

    def test_get_public_profile_by_id(self, client, student_token, tutor_user):
        """Test getting public profile by ID."""
        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/public",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tutor_user.tutor_profile.id

    def test_get_nonexistent_tutor_profile(self, client, student_token):
        """Test 404 for nonexistent tutor profile."""
        response = client.get(
            "/api/v1/tutors/99999/public",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Search and Filtering Tests
# ============================================================================


class TestSearchAndFiltering:
    """Test tutor search and filtering functionality."""

    def test_filter_by_rate_range(self, client, student_token, db_session, tutor_user):
        """Test filtering tutors by hourly rate range."""
        response = client.get(
            "/api/v1/tutors?min_rate=40&max_rate=60",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for tutor in data["items"]:
            rate = float(tutor["hourly_rate"])
            assert 40 <= rate <= 60

    def test_filter_by_min_rating(self, client, student_token, db_session, tutor_user):
        """Test filtering tutors by minimum rating."""
        # Update tutor's rating
        tutor_user.tutor_profile.average_rating = Decimal("4.5")
        db_session.commit()

        response = client.get(
            "/api/v1/tutors?min_rating=4.0",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for tutor in data["items"]:
            assert float(tutor["average_rating"]) >= 4.0

    def test_search_by_query(self, client, student_token, tutor_user):
        """Test searching tutors by text query."""
        response = client.get(
            "/api/v1/tutors?search_query=Expert",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should find the tutor with "Expert" in title
        assert len(data["items"]) >= 1

    def test_sort_by_rating(self, client, student_token, db_session):
        """Test sorting tutors by rating."""
        response = client.get(
            "/api/v1/tutors?sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["items"]) > 1:
            ratings = [float(t["average_rating"]) for t in data["items"]]
            assert ratings == sorted(ratings, reverse=True)

    def test_sort_by_rate_asc(self, client, student_token):
        """Test sorting tutors by rate ascending."""
        response = client.get(
            "/api/v1/tutors?sort_by=rate_asc",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["items"]) > 1:
            rates = [float(t["hourly_rate"]) for t in data["items"]]
            assert rates == sorted(rates)

    def test_pagination(self, client, student_token):
        """Test pagination parameters."""
        response = client.get(
            "/api/v1/tutors?page=1&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


# ============================================================================
# Profile State Transition Tests
# ============================================================================


class TestProfileStateTransitions:
    """Test profile approval workflow state transitions."""

    def test_submit_for_review_success(self, client, complete_tutor_token, db_session):
        """Test submitting a complete profile for review."""
        response = client.post(
            "/api/v1/tutors/me/submit",
            headers={"Authorization": f"Bearer {complete_tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["profile_status"] == "pending_approval"

    def test_submit_incomplete_profile_rejected(self, client, tutor_without_profile_token):
        """Test that incomplete profiles cannot be submitted."""
        # First access the profile to create it
        client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_without_profile_token}"},
        )

        response = client.post(
            "/api/v1/tutors/me/submit",
            headers={"Authorization": f"Bearer {tutor_without_profile_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "photo" in response.json()["detail"].lower() or "title" in response.json()["detail"].lower()

    def test_submit_idempotent(self, client, complete_tutor_token):
        """Test that submitting twice is idempotent."""
        # First submission
        response1 = client.post(
            "/api/v1/tutors/me/submit",
            headers={"Authorization": f"Bearer {complete_tutor_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second submission should also succeed
        response2 = client.post(
            "/api/v1/tutors/me/submit",
            headers={"Authorization": f"Bearer {complete_tutor_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["profile_status"] == "pending_approval"


# ============================================================================
# Profile Photo Upload Tests
# ============================================================================


class TestProfilePhotoUpload:
    """Test profile photo upload functionality."""

    def test_upload_photo_success(self, client, tutor_token, tutor_user, monkeypatch):
        """Test uploading a profile photo."""
        from modules.tutor_profile.application import services as tutor_services

        async def fake_store_profile_photo(user_id, upload, existing_url=None):
            content = await upload.read()
            assert content
            return f"https://example.com/tutors/{user_id}.webp"

        monkeypatch.setattr(tutor_services, "store_profile_photo", fake_store_profile_photo)
        monkeypatch.setattr(tutor_services, "delete_file", lambda url: None)

        buffer = BytesIO()
        Image.new("RGB", (400, 400), color=(10, 120, 200)).save(buffer, format="PNG")
        buffer.seek(0)

        response = client.patch(
            "/api/v1/tutors/me/photo",
            headers={"Authorization": f"Bearer {tutor_token}"},
            files={"profile_photo": ("photo.png", buffer.getvalue(), "image/png")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["profile_photo_url"] == f"https://example.com/tutors/{tutor_user.id}.webp"


# ============================================================================
# Description and Video Tests
# ============================================================================


class TestDescriptionAndVideo:
    """Test description and video URL updates."""

    def test_update_description_success(self, client, tutor_token):
        """Test updating long description."""
        long_description = "A" * 450  # Min 400 chars

        response = client.patch(
            "/api/v1/tutors/me/description",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"description": long_description},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == long_description

    def test_update_description_too_short(self, client, tutor_token):
        """Test that short descriptions are rejected."""
        response = client.patch(
            "/api/v1/tutors/me/description",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"description": "Too short"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_video_success(self, client, tutor_token):
        """Test updating video URL."""
        response = client.patch(
            "/api/v1/tutors/me/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "youtube.com" in data["video_url"]

    def test_update_video_invalid_platform(self, client, tutor_token):
        """Test that non-approved video platforms are rejected."""
        response = client.patch(
            "/api/v1/tutors/me/video",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"video_url": "https://randomvideo.com/video123"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Available Slots Tests
# ============================================================================


class TestAvailableSlots:
    """Test available slots endpoint."""

    def test_get_available_slots(self, client, student_token, db_session, tutor_user):
        """Test getting available slots for a tutor."""
        # Add availability
        availability = TutorAvailability(
            tutor_profile_id=tutor_user.tutor_profile.id,
            day_of_week=1,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()

        # Get slots for next week
        start_date = (utc_now() + timedelta(days=1)).isoformat()
        end_date = (utc_now() + timedelta(days=8)).isoformat()

        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/available-slots",
            params={"start_date": start_date, "end_date": end_date},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        # Should return list of slots (may be empty if no Mondays in range)
        assert isinstance(response.json(), list)

    def test_get_available_slots_date_range_limit(self, client, student_token, tutor_user):
        """Test that date range cannot exceed 30 days."""
        start_date = utc_now().isoformat()
        end_date = (utc_now() + timedelta(days=35)).isoformat()

        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/available-slots",
            params={"start_date": start_date, "end_date": end_date},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "30 days" in response.json()["detail"]


# ============================================================================
# Reviews Endpoint Test
# ============================================================================


class TestTutorReviews:
    """Test tutor reviews endpoint."""

    def test_get_tutor_reviews(self, client, student_token, tutor_user):
        """Test getting reviews for a tutor."""
        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
