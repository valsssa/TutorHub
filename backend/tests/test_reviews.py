"""Tests for review endpoints."""

from fastapi import status
from core.datetime_utils import utc_now

from tests.conftest import STUDENT_PASSWORD


class TestCreateReview:
    """Test review creation."""

    def test_student_create_review_success(self, client, student_token, test_booking, db_session):
        """Test student can create review for completed booking."""
        # Mark booking as completed
        test_booking.session_state = "ENDED"
        test_booking.session_outcome = "COMPLETED"
        db_session.commit()

        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "booking_id": test_booking.id,
                "rating": 5,
                "comment": "Excellent tutor! Very helpful and patient.",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent tutor! Very helpful and patient."

    def test_cannot_review_non_completed_booking(self, client, student_token, test_booking):
        """Test cannot review pending booking."""
        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"booking_id": test_booking.id, "rating": 5, "comment": "Great!"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "completed" in response.json()["detail"].lower()

    def test_cannot_review_other_student_booking(self, client, test_booking, db_session):
        """Test student cannot review another student's booking."""
        from auth import get_password_hash
        from models import User

        # Create another student
        another_student = User(
            email="student2@test.com",
            hashed_password=get_password_hash(STUDENT_PASSWORD),
            role="student",
            is_verified=True,
        )
        db_session.add(another_student)
        db_session.commit()

        # Login as another student
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "student2@test.com", "password": STUDENT_PASSWORD},
        )
        token = response.json()["access_token"]

        # Mark booking as completed
        test_booking.session_state = "ENDED"
        test_booking.session_outcome = "COMPLETED"
        db_session.commit()

        # Try to review
        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {token}"},
            json={"booking_id": test_booking.id, "rating": 5, "comment": "Great!"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_review_twice(self, client, student_token, test_booking, db_session):
        """Test cannot create duplicate review."""
        from models import Review  # noqa: F401

        # Mark booking as completed
        test_booking.session_state = "ENDED"
        test_booking.session_outcome = "COMPLETED"
        db_session.commit()

        # Create first review
        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"booking_id": test_booking.id, "rating": 5, "comment": "Great!"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Try to create second review
        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "booking_id": test_booking.id,
                "rating": 4,
                "comment": "Still great!",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_tutor_cannot_create_review(self, client, tutor_token, test_booking, db_session):
        """Test tutor cannot create review."""
        test_booking.session_state = "ENDED"
        test_booking.session_outcome = "COMPLETED"
        db_session.commit()

        response = client.post(
            "/api/v1/reviews",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "booking_id": test_booking.id,
                "rating": 5,
                "comment": "Great student!",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetTutorReviews:
    """Test getting tutor reviews."""

    def test_get_tutor_reviews_success(self, client, student_token, tutor_user, test_booking, db_session):
        """Test getting tutor reviews."""
        from models import Review

        # Mark booking as completed and create review
        test_booking.session_state = "ENDED"
        test_booking.session_outcome = "COMPLETED"
        db_session.commit()

        review = Review(
            booking_id=test_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=test_booking.student_id,
            rating=5,
            comment="Excellent!",
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["rating"] == 5
        assert data[0]["comment"] == "Excellent!"

    def test_only_public_reviews_shown(self, client, student_token, tutor_user, test_booking, test_subject, db_session):
        """Test only public reviews are shown."""
        from datetime import datetime, timedelta

        from models import Booking, Review

        # Create a second booking for the private review
        booking2 = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=test_booking.student_id,
            subject_id=test_subject.id,
            start_time=utc_now() + timedelta(days=2),
            end_time=utc_now() + timedelta(days=2, hours=1),
            topic="Second booking",
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            session_state="ENDED",
            session_outcome="COMPLETED",
            tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
            student_name="Test Student",
            subject_name=test_subject.name,
        )
        db_session.add(booking2)
        db_session.flush()

        # Create public review
        review1 = Review(
            booking_id=test_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=test_booking.student_id,
            rating=5,
            comment="Public review",
            is_public=True,
        )
        db_session.add(review1)

        # Create private review with the second booking
        review2 = Review(
            booking_id=booking2.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=test_booking.student_id,
            rating=3,
            comment="Private review",
            is_public=False,
        )
        db_session.add(review2)
        db_session.commit()

        response = client.get(
            f"/api/v1/tutors/{tutor_user.tutor_profile.id}/reviews",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only see public review
        comments = [r["comment"] for r in data]
        assert "Public review" in comments
        assert "Private review" not in comments
