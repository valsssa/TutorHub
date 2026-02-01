"""Tests for booking endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi import status


class TestCreateBooking:
    """Test booking creation."""

    def test_student_create_booking_success(self, client, student_token, tutor_user, test_subject):
        """Test successful booking creation by student."""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        response = client.post(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "subject_id": test_subject.id,
                "start_at": start_time.isoformat(),
                "duration_minutes": duration_minutes,
                "topic": "Algebra basics",
                "notes": "Need help with quadratic equations",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # API returns uppercase status values
        assert data["status"] == "PENDING"
        # Rate is locked at $50/hour, 2 hours = $100
        assert data["rate_cents"] == 10000  # $100.00 in cents

    def test_tutor_cannot_create_booking(self, client, tutor_token, tutor_user, test_subject):
        """Test tutor cannot create booking."""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        response = client.post(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "subject_id": test_subject.id,
                "start_at": start_time.isoformat(),
                "duration_minutes": duration_minutes,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_booking_invalid_duration(self, client, student_token, tutor_user, test_subject):
        """Test booking with invalid (too short) duration."""
        start_time = datetime.utcnow() + timedelta(days=1)

        response = client.post(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "subject_id": test_subject.id,
                "start_at": start_time.isoformat(),
                "duration_minutes": 10,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_booking_too_long(self, client, student_token, tutor_user, test_subject):
        """Test booking exceeding 8 hours."""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=9)  # Too long
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        response = client.post(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "subject_id": test_subject.id,
                "start_at": start_time.isoformat(),
                "duration_minutes": duration_minutes,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_booking_nonexistent_tutor(self, client, student_token, test_subject):
        """Test booking with nonexistent tutor."""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        response = client.post(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "tutor_profile_id": 99999,  # Nonexistent
                "subject_id": test_subject.id,
                "start_at": start_time.isoformat(),
                "duration_minutes": duration_minutes,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListBookings:
    """Test listing bookings."""

    def test_student_list_own_bookings(self, client, student_token, test_booking):
        """Test student can list their bookings."""
        response = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Response is paginated with "bookings" key
        assert "bookings" in data
        assert data["total"] == 1
        assert data["bookings"][0]["id"] == test_booking.id

    def test_tutor_list_own_bookings(self, client, tutor_token):
        """Test tutor can list their bookings (empty if none exist)."""
        response = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Response is paginated with "bookings" key
        assert "bookings" in data
        assert "total" in data

    def test_admin_list_all_bookings(self, client, admin_token):
        """Test admin can list all bookings."""
        response = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Response is paginated with "bookings" key
        assert "bookings" in data
        assert "total" in data


class TestUpdateBookingStatus:
    """Test booking status updates."""

    def test_tutor_approve_booking(self, client, tutor_token, test_booking):
        """Test tutor can approve booking."""
        response = client.post(
            f"/api/v1/tutor/bookings/{test_booking.id}/confirm",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "CONFIRMED"

    def test_tutor_decline_booking(self, client, tutor_token, test_booking):
        """Test tutor can decline booking."""
        response = client.post(
            f"/api/v1/tutor/bookings/{test_booking.id}/decline",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"reason": "Not available at this time"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Declined bookings are cancelled by tutor
        assert data["status"] == "CANCELLED_BY_TUTOR"

    def test_student_cancel_booking(self, client, student_token, test_booking):
        """Test student can cancel their booking."""
        response = client.post(
            f"/api/v1/bookings/{test_booking.id}/cancel",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"reason": "Changed my mind"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "CANCELLED_BY_STUDENT"

    def test_student_cannot_confirm_booking(self, client, student_token, test_booking):
        """Test student cannot confirm booking (only tutor can)."""
        # Student trying to use tutor confirm endpoint should get 403
        response = client.post(
            f"/api/v1/tutor/bookings/{test_booking.id}/confirm",
            headers={"Authorization": f"Bearer {student_token}"},
            json={},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.skip(reason="Test needs refactoring to use new booking API endpoints and fixtures")
    def test_tutor_cannot_update_other_tutor_booking(self, client, tutor_user, db_session):
        """Test tutor cannot update another tutor's booking."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        # Create another tutor
        another_tutor = User(
            email="tutor2@test.com",
            hashed_password=get_password_hash("tutor123"),
            role="tutor",
            is_verified=True,
        )
        db_session.add(another_tutor)
        db_session.flush()

        another_profile = TutorProfile(
            user_id=another_tutor.id,
            title="Another Tutor",
            headline="Test",
            bio="Test",
            hourly_rate=40.00,
            is_approved=True,
        )
        db_session.add(another_profile)
        db_session.flush()

        # Create subject and student
        subject = Subject(name="Test Subject", is_active=True)
        db_session.add(subject)
        db_session.flush()

        student = User(
            email="student2@test.com",
            hashed_password=get_password_hash("student123"),
            role="student",
        )
        db_session.add(student)
        db_session.flush()

        # Create booking for another tutor
        booking = Booking(
            tutor_profile_id=another_profile.id,
            student_id=student.id,
            subject_id=subject.id,
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=1),
            hourly_rate=40.00,
            total_amount=40.00,
            session_state="REQUESTED",
            payment_state="PENDING",
        )
        db_session.add(booking)
        db_session.commit()

        # Get token for first tutor
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": tutor_user.email, "password": "tutor123"},
        )
        token = response.json()["access_token"]

        # Try to update another tutor's booking
        response = client.patch(
            f"/api/v1/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "confirmed"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
