"""Tests for student profile endpoints."""

from fastapi import status


class TestGetStudentProfile:
    """Test getting student profile."""

    def test_student_get_profile(self, client, student_token, student_user, db_session):
        """Test student can get their profile."""
        response = client.get(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == student_user.id

    def test_student_profile_auto_create(self, client, student_token, student_user, db_session):
        """Test student profile is created if it doesn't exist."""
        from models import StudentProfile

        # Ensure no profile exists
        profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == student_user.id).first()
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.get(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == student_user.id

        # Verify profile was created in database
        profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == student_user.id).first()
        assert profile is not None

    def test_tutor_cannot_access_student_profile(self, client, tutor_token):
        """Test tutor cannot access student profile endpoint."""
        response = client.get(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_access_student_profile(self, client, admin_token):
        """Test admin cannot access student profile endpoint."""
        response = client.get(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_student_profile_unauthorized(self, client):
        """Test getting student profile without auth fails."""
        response = client.get("/api/v1/profile/student/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateStudentProfile:
    """Test updating student profile."""

    def test_update_student_profile(self, client, student_token, student_user, db_session):
        """Test student can update their profile."""
        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "grade_level": "10th Grade",
                "school_name": "Test University",
                "learning_goals": "Improve math skills",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["grade_level"] == "10th Grade"
        assert data["school_name"] == "Test University"
        assert data["learning_goals"] == "Improve math skills"

    def test_update_creates_profile_if_not_exists(self, client, student_token, student_user, db_session):
        """Test update creates profile if it doesn't exist."""
        from models import StudentProfile

        # Ensure no profile exists
        profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == student_user.id).first()
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"grade_level": "12th Grade"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["grade_level"] == "12th Grade"

        # Verify profile was created
        profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == student_user.id).first()
        assert profile is not None

    def test_update_partial_fields(self, client, student_token, student_user, db_session):
        """Test partial update doesn't overwrite unspecified fields."""
        from models import StudentProfile

        # Create profile with multiple fields
        profile = StudentProfile(
            user_id=student_user.id,
            grade_level="10th Grade",
            school_name="Original University",
            learning_goals="Original Goals",
            interests="Math, Science",
        )
        db_session.add(profile)
        db_session.commit()

        # Update only one field
        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"school_name": "New University"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Updated field
        assert data["school_name"] == "New University"
        # Unchanged fields
        assert data["grade_level"] == "10th Grade"
        assert data["learning_goals"] == "Original Goals"

    def test_update_all_fields(self, client, student_token, student_user, db_session):
        """Test updating all student profile fields."""
        full_data = {
            "grade_level": "12th Grade",
            "school_name": "Test High School",
            "learning_goals": "Master ML algorithms",
            "interests": "AI, Data Science, Python",
            "bio": "Passionate about technology",
        }

        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json=full_data,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for key, value in full_data.items():
            assert data[key] == value

    def test_tutor_cannot_update_student_profile(self, client, tutor_token):
        """Test tutor cannot update student profile."""
        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"grade_level": "12th Grade"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_student_profile_unauthorized(self, client):
        """Test updating student profile without auth fails."""
        response = client.patch("/api/v1/profile/student/me", json={"grade_level": "12th Grade"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_with_empty_strings(self, client, student_token, student_user, db_session):
        """Test updating with empty strings clears the field."""
        from models import StudentProfile

        # Create profile with interests
        profile = StudentProfile(user_id=student_user.id, interests="Math, Science")
        db_session.add(profile)
        db_session.commit()

        # Clear interests
        response = client.patch(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"interests": ""},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["interests"] is None or data["interests"] == ""
