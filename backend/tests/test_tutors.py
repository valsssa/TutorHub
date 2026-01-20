"""Tests for tutor endpoints."""

from io import BytesIO

from fastapi import status
from PIL import Image


class TestListTutors:
    """Test listing tutors."""

    def test_list_tutors_success(self, client, student_token, tutor_user):
        """Test successful listing of tutors."""
        response = client.get("/api/tutors", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "Expert Math Tutor"

    def test_list_tutors_with_rate_filter(self, client, student_token, tutor_user):
        """Test filtering tutors by rate."""
        response = client.get(
            "/api/tutors?min_rate=40&max_rate=60",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(40 <= float(t["hourly_rate"]) <= 60 for t in data)

    def test_list_tutors_requires_auth(self, client):
        """Test listing tutors requires authentication."""
        response = client.get("/api/tutors")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetTutorProfile:
    """Test getting tutor profile."""

    def test_get_tutor_profile_success(self, client, student_token, tutor_user):
        """Test successful retrieval of tutor profile."""
        response = client.get(
            f"/api/tutors/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Expert Math Tutor"
        assert float(data["hourly_rate"]) == 50.00

    def test_get_nonexistent_tutor(self, client, student_token):
        """Test getting nonexistent tutor."""
        response = client.get("/api/tutors/99999", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetMyTutorProfile:
    """Test tutor getting their own profile."""

    def test_tutor_get_own_profile(self, client, tutor_token, tutor_user):
        """Test tutor can get their own profile."""
        response = client.get("/api/tutors/me/profile", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Expert Math Tutor"

    def test_student_cannot_get_tutor_profile(self, client, student_token):
        """Test student cannot access tutor-only endpoint."""
        response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCreateUpdateTutorProfile:
    """Test creating and updating tutor profile."""

    def test_tutor_create_profile(self, client, db_session, test_subject):
        """Test tutor can create profile."""
        from auth import get_password_hash
        from models import User

        # Create new tutor without profile
        new_tutor = User(
            email="newtutor@test.com",
            hashed_password=get_password_hash("tutor123"),
            role="tutor",
            is_verified=True,
        )
        db_session.add(new_tutor)
        db_session.commit()

        # Login
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            data={"username": "newtutor@test.com", "password": "tutor123"},
        )
        token = response.json()["access_token"]

        # Create profile
        response = client.post(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "New Tutor Profile",
                "headline": "Expert in teaching",
                "bio": "I love teaching students!",
                "hourly_rate": 45.00,
                "experience_years": 5,
                "education": "Bachelor's Degree",
                "languages": ["English"],
                "subjects": [
                    {
                        "subject_id": test_subject.id,
                        "proficiency_level": "expert",
                        "years_experience": 5,
                    }
                ],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Tutor Profile"
        assert float(data["hourly_rate"]) == 45.00

    def test_tutor_update_profile(self, client, tutor_token, tutor_user, test_subject):
        """Test tutor can update their profile."""
        response = client.post(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "title": "Updated Title",
                "headline": "Updated headline",
                "bio": "Updated bio",
                "hourly_rate": 60.00,
                "experience_years": 12,
                "education": "PhD in Mathematics",
                "languages": ["English", "French"],
                "subjects": [
                    {
                        "subject_id": test_subject.id,
                        "proficiency_level": "expert",
                        "years_experience": 10,
                    }
                ],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert float(data["hourly_rate"]) == 60.00


class TestTutorPhoto:
    """Test tutor profile photo management."""

    def test_tutor_upload_photo(self, client, tutor_token, tutor_user, monkeypatch):
        """Uploading a tutor photo stores the image and updates profile."""
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
            "/api/tutors/me/photo",
            headers={"Authorization": f"Bearer {tutor_token}"},
            files={"profile_photo": ("photo.png", buffer.getvalue(), "image/png")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["profile_photo_url"] == f"https://example.com/tutors/{tutor_user.id}.webp"


class TestTutorSubmission:
    """Test tutor profile submission workflow."""

    @staticmethod
    def _prepare_profile(db_session, tutor_user):
        profile = tutor_user.tutor_profile
        profile.profile_photo_url = "https://cdn.example.com/photos/profile.jpg"
        profile.description = "A" * 420
        profile.profile_status = "incomplete"
        profile.rejection_reason = "Needs revision"
        db_session.commit()
        db_session.refresh(profile)
        return profile

    def test_update_description_keeps_status_incomplete(self, client, db_session, tutor_token, tutor_user):
        """Updating description should not auto-submit profile."""
        profile = self._prepare_profile(db_session, tutor_user)

        response = client.patch(
            "/api/tutors/me/description",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"description": f"   {'B' * 410}   "},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["profile_status"] == "incomplete"
        assert data["description"] == "B" * 410

        db_session.refresh(profile)
        assert profile.profile_status == "incomplete"
        assert profile.description == "B" * 410

    def test_submit_profile_idempotent_pending_status(self, client, db_session, tutor_token, tutor_user):
        """Submitting twice should remain pending without errors."""
        profile = self._prepare_profile(db_session, tutor_user)

        first = client.post(
            "/api/tutors/me/submit",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert first.status_code == status.HTTP_200_OK
        first_payload = first.json()
        assert first_payload["profile_status"] == "pending_approval"

        db_session.refresh(profile)
        assert profile.profile_status == "pending_approval"
        assert profile.rejection_reason is None

        second = client.post(
            "/api/tutors/me/submit",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert second.status_code == status.HTTP_200_OK
        second_payload = second.json()
        assert second_payload["profile_status"] == "pending_approval"

        db_session.refresh(profile)
        assert profile.profile_status == "pending_approval"
        assert profile.rejection_reason is None


class TestTutorAvailability:
    """Test tutor availability management."""

    def test_tutor_add_availability(self, client, tutor_token):
        """Test tutor can add availability via bulk update."""
        # First clear any existing availability
        client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"availability": [], "version": 1},
        )

        # Now add new availability
        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 1,  # Monday
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    }
                ],
                "version": 2,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # The response is a TutorProfileResponse which includes availabilities
        assert "availabilities" in data
        assert len(data["availabilities"]) == 1
        assert data["availabilities"][0]["day_of_week"] == 1
        assert data["availabilities"][0]["start_time"] == "09:00:00"

    def test_tutor_delete_availability(self, client, tutor_token, db_session, tutor_user):
        """Test tutor can delete availability."""
        # Create availability
        from datetime import time

        from models import TutorAvailability

        availability = TutorAvailability(
            tutor_profile_id=tutor_user.tutor_profile.id,
            day_of_week=2,
            start_time=time(10, 0),
            end_time=time(18, 0),
            is_recurring=True,
        )
        db_session.add(availability)
        db_session.commit()
        availability_id = availability.id

        # Delete it
        response = client.delete(
            f"/api/tutors/availability/{availability_id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_tutor_cannot_delete_other_tutor_availability(self, client, tutor_token, db_session):
        """Test tutor cannot delete another tutor's availability."""
        from auth import get_password_hash
        from models import TutorAvailability, TutorProfile, User

        # Create another tutor
        another_tutor = User(
            email="tutor3@test.com",
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

        # Create availability for another tutor
        from datetime import time

        availability = TutorAvailability(
            tutor_profile_id=another_profile.id,
            day_of_week=3,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
        )
        db_session.add(availability)
        db_session.commit()

        # Try to delete with first tutor's token
        response = client.delete(
            f"/api/tutors/availability/{availability.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
