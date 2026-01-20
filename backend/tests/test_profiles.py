"""Tests for user profile endpoints."""

from fastapi import status


class TestGetProfile:
    """Test getting user profile."""

    def test_get_profile_creates_if_not_exists(self, client, student_token, student_user, db_session):
        """Test that getting profile creates one if it doesn't exist."""
        from models import UserProfile

        # Ensure no profile exists
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == student_user.id).first()
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.get("/api/profile/me", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == student_user.id

        # Verify profile was created
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == student_user.id).first()
        assert profile is not None

    def test_get_existing_profile(self, client, student_token, student_user, db_session):
        """Test getting existing profile returns data."""
        from models import UserProfile

        # Create profile with data
        profile = UserProfile(
            user_id=student_user.id,
            full_name="John Doe",
            phone_number="+1234567890",
            date_of_birth="2000-01-01",
            address="123 Main St",
            city="Test City",
            country="Test Country",
            timezone="UTC",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get("/api/profile/me", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "John Doe"
        assert data["phone_number"] == "+1234567890"
        assert data["city"] == "Test City"

    def test_get_profile_unauthorized(self, client):
        """Test getting profile without auth fails."""
        response = client.get("/api/profile/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateProfile:
    """Test updating user profile."""

    def test_update_profile_creates_if_not_exists(self, client, student_token, student_user, db_session):
        """Test updating profile creates one if it doesn't exist."""
        from models import UserProfile

        # Ensure no profile exists
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == student_user.id).first()
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"full_name": "Jane Smith", "phone_number": "+9876543210"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Jane Smith"
        assert data["phone_number"] == "+9876543210"

        # Verify profile was created
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == student_user.id).first()
        assert profile is not None
        assert profile.full_name == "Jane Smith"

    def test_update_existing_profile(self, client, student_token, student_user, db_session):
        """Test updating existing profile."""
        from models import UserProfile

        # Create initial profile
        profile = UserProfile(user_id=student_user.id, full_name="Original Name", city="Original City")
        db_session.add(profile)
        db_session.commit()

        response = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "full_name": "Updated Name",
                "city": "Updated City",
                "country": "New Country",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["city"] == "Updated City"
        assert data["country"] == "New Country"

        # Verify in database
        db_session.refresh(profile)
        assert profile.full_name == "Updated Name"
        assert profile.city == "Updated City"

    def test_update_profile_partial(self, client, student_token, student_user, db_session):
        """Test partial profile update doesn't overwrite unspecified fields."""
        from models import UserProfile

        # Create profile with multiple fields
        profile = UserProfile(
            user_id=student_user.id,
            full_name="John Doe",
            phone_number="+1234567890",
            city="Test City",
            country="Test Country",
        )
        db_session.add(profile)
        db_session.commit()

        # Update only one field
        response = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"city": "New City"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["city"] == "New City"
        # Other fields should remain unchanged
        assert data["full_name"] == "John Doe"
        assert data["phone_number"] == "+1234567890"
        assert data["country"] == "Test Country"

    def test_update_profile_unauthorized(self, client):
        """Test updating profile without auth fails."""
        response = client.put("/api/profile/me", json={"full_name": "Test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_with_all_fields(self, client, student_token, student_user, db_session):
        """Test updating profile with all available fields."""
        from models import UserProfile

        # Ensure clean state
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == student_user.id).first()
        if profile:
            db_session.delete(profile)
            db_session.commit()

        full_data = {
            "full_name": "Complete Name",
            "phone_number": "+1234567890",
            "date_of_birth": "1990-05-15",
            "address": "456 Test Ave",
            "city": "TestVille",
            "state": "TestState",
            "postal_code": "12345",
            "country": "TestLand",
            "bio": "This is my bio",
            "profile_photo_url": "https://example.com/photo.jpg",
            "timezone": "America/New_York",
        }

        response = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json=full_data,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for key, value in full_data.items():
            assert data[key] == value

    def test_update_profile_invalid_data(self, client, student_token):
        """Test updating profile with invalid data fails gracefully."""
        # Test with excessively long name
        response = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"full_name": "x" * 500},  # Too long
        )
        # Should either reject or truncate
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]
