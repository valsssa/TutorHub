"""Tests for tutors search response format.

Verifies that tutor search results include all required fields for the frontend,
including rating/review data and properly structured subjects.
"""

from decimal import Decimal

import pytest
from fastapi import status


class TestTutorSearchResponseFormat:
    """Test tutor search response includes all required fields."""

    def test_tutor_search_includes_rating_fields(self, client, db_session):
        """Verify tutor search results include average_rating and total_reviews fields."""
        from models import TutorProfile, User

        # Create approved tutor with rating
        tutor_user = User(
            email="rated_tutor@test.com",
            hashed_password="hash",
            role="tutor",
            first_name="Rated",
            last_name="Tutor",
        )
        db_session.add(tutor_user)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor_user.id,
            title="Rated Tutor",
            headline="Expert teacher",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
            average_rating=Decimal("4.8"),
            total_reviews=15,
            total_sessions=25,
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get("/api/v1/tutors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "items" in data
        assert len(data["items"]) >= 1

        # Find our test tutor
        test_tutor = next(
            (t for t in data["items"] if t["title"] == "Rated Tutor"),
            None,
        )
        assert test_tutor is not None

        # Verify rating fields are present
        assert "average_rating" in test_tutor
        assert "total_reviews" in test_tutor
        assert "total_sessions" in test_tutor

        # Verify rating values
        assert float(test_tutor["average_rating"]) == pytest.approx(4.8, rel=0.01)
        assert test_tutor["total_reviews"] == 15
        assert test_tutor["total_sessions"] == 25

    def test_tutor_search_subjects_are_objects(self, client, db_session):
        """Verify tutor search results have subjects as objects with id and name."""
        from models import Subject, TutorProfile, TutorSubject, User

        # Create subject
        subject = Subject(name="Mathematics", is_active=True)
        db_session.add(subject)
        db_session.commit()

        # Create approved tutor
        tutor_user = User(
            email="subjects_tutor@test.com",
            hashed_password="hash",
            role="tutor",
            first_name="Subject",
            last_name="Tutor",
        )
        db_session.add(tutor_user)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor_user.id,
            title="Subjects Tutor",
            hourly_rate=Decimal("60.00"),
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Add subject to tutor
        tutor_subject = TutorSubject(
            tutor_profile_id=profile.id,
            subject_id=subject.id,
            proficiency_level="c2",
            years_experience=5,
        )
        db_session.add(tutor_subject)
        db_session.commit()

        response = client.get("/api/v1/tutors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Find our test tutor
        test_tutor = next(
            (t for t in data["items"] if t["title"] == "Subjects Tutor"),
            None,
        )
        assert test_tutor is not None

        # Verify subjects field structure
        assert "subjects" in test_tutor
        assert len(test_tutor["subjects"]) >= 1

        # Subjects should be objects with id and name
        first_subject = test_tutor["subjects"][0]
        assert isinstance(first_subject, dict)
        assert "id" in first_subject
        assert "name" in first_subject
        assert first_subject["id"] == subject.id
        assert first_subject["name"] == "Mathematics"

    def test_tutor_search_includes_all_public_fields(self, client, db_session):
        """Verify tutor search results include all public profile fields."""
        from models import TutorProfile, User

        tutor_user = User(
            email="complete_tutor@test.com",
            hashed_password="hash",
            role="tutor",
            first_name="Complete",
            last_name="Profile",
        )
        db_session.add(tutor_user)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor_user.id,
            title="Complete Profile Tutor",
            headline="Full profile for testing",
            bio="Detailed biography here",
            hourly_rate=Decimal("75.00"),
            experience_years=10,
            is_approved=True,
            profile_status="approved",
            average_rating=Decimal("4.5"),
            total_reviews=20,
            total_sessions=50,
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get("/api/v1/tutors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        test_tutor = next(
            (t for t in data["items"] if t["title"] == "Complete Profile Tutor"),
            None,
        )
        assert test_tutor is not None

        # Verify all expected public fields are present
        required_fields = [
            "id",
            "user_id",
            "title",
            "headline",
            "bio",
            "hourly_rate",
            "experience_years",
            "average_rating",
            "total_reviews",
            "total_sessions",
            "subjects",
        ]

        for field in required_fields:
            assert field in test_tutor, f"Missing required field: {field}"

    def test_tutor_search_zero_rating_defaults(self, client, db_session):
        """Verify tutors with no ratings have proper default values."""
        from models import TutorProfile, User

        tutor_user = User(
            email="new_tutor@test.com",
            hashed_password="hash",
            role="tutor",
            first_name="New",
            last_name="Tutor",
        )
        db_session.add(tutor_user)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor_user.id,
            title="New Tutor No Reviews",
            hourly_rate=Decimal("40.00"),
            is_approved=True,
            profile_status="approved",
            # Default values: average_rating=0, total_reviews=0
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get("/api/v1/tutors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        test_tutor = next(
            (t for t in data["items"] if t["title"] == "New Tutor No Reviews"),
            None,
        )
        assert test_tutor is not None

        # Verify zero values are returned correctly
        assert float(test_tutor["average_rating"]) == 0.0
        assert test_tutor["total_reviews"] == 0
        assert test_tutor["total_sessions"] == 0

    def test_tutor_public_profile_includes_rating(self, client, db_session):
        """Verify single tutor public profile includes rating fields."""
        from models import TutorProfile, User

        tutor_user = User(
            email="single_tutor@test.com",
            hashed_password="hash",
            role="tutor",
            first_name="Single",
            last_name="Profile",
        )
        db_session.add(tutor_user)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor_user.id,
            title="Single Profile Tutor",
            hourly_rate=Decimal("55.00"),
            is_approved=True,
            profile_status="approved",
            average_rating=Decimal("4.9"),
            total_reviews=30,
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(f"/api/v1/tutors/{profile.id}/public")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "average_rating" in data
        assert "total_reviews" in data
        assert float(data["average_rating"]) == pytest.approx(4.9, rel=0.01)
        assert data["total_reviews"] == 30
