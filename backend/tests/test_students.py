"""Tests for student profile endpoints."""

from fastapi import status


class TestGetStudentProfile:
    """Test getting student profile."""

    def test_student_get_profile(self, client, student_token, student_user, db_session):
        """Test student can get their profile."""
        response = client.get(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == student_user.id

    def test_student_profile_auto_create(
        self, client, student_token, student_user, db_session
    ):
        """Test student profile is created if it doesn't exist."""
        from models import StudentProfile

        # Ensure no profile exists
        profile = (
            db_session.query(StudentProfile)
            .filter(StudentProfile.user_id == student_user.id)
            .first()
        )
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.get(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == student_user.id

        # Verify profile was created in database
        profile = (
            db_session.query(StudentProfile)
            .filter(StudentProfile.user_id == student_user.id)
            .first()
        )
        assert profile is not None

    def test_tutor_cannot_access_student_profile(self, client, tutor_token):
        """Test tutor cannot access student profile endpoint."""
        response = client.get(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_access_student_profile(self, client, admin_token):
        """Test admin cannot access student profile endpoint."""
        response = client.get(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_student_profile_unauthorized(self, client):
        """Test getting student profile without auth fails."""
        response = client.get("/api/profile/student/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateStudentProfile:
    """Test updating student profile."""

    def test_update_student_profile(
        self, client, student_token, student_user, db_session
    ):
        """Test student can update their profile."""
        response = client.patch(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "education_level": "undergraduate",
                "institution": "Test University",
                "field_of_study": "Computer Science",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["education_level"] == "undergraduate"
        assert data["institution"] == "Test University"
        assert data["field_of_study"] == "Computer Science"

    def test_update_creates_profile_if_not_exists(
        self, client, student_token, student_user, db_session
    ):
        """Test update creates profile if it doesn't exist."""
        from models import StudentProfile

        # Ensure no profile exists
        profile = (
            db_session.query(StudentProfile)
            .filter(StudentProfile.user_id == student_user.id)
            .first()
        )
        if profile:
            db_session.delete(profile)
            db_session.commit()

        response = client.patch(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"education_level": "graduate"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["education_level"] == "graduate"

        # Verify profile was created
        profile = (
            db_session.query(StudentProfile)
            .filter(StudentProfile.user_id == student_user.id)
            .first()
        )
        assert profile is not None

    def test_update_partial_fields(
        self, client, student_token, student_user, db_session
    ):
        """Test partial update doesn't overwrite unspecified fields."""
        from models import StudentProfile

        # Create profile with multiple fields
        profile = StudentProfile(
            user_id=student_user.id,
            education_level="undergraduate",
            institution="Original University",
            field_of_study="Original Field",
            interests=["Math", "Science"],
        )
        db_session.add(profile)
        db_session.commit()

        # Update only one field
        response = client.patch(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"institution": "New University"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Updated field
        assert data["institution"] == "New University"
        # Unchanged fields
        assert data["education_level"] == "undergraduate"
        assert data["field_of_study"] == "Original Field"

    def test_update_all_fields(self, client, student_token, student_user, db_session):
        """Test updating all student profile fields."""
        full_data = {
            "education_level": "graduate",
            "institution": "Test Graduate School",
            "field_of_study": "Machine Learning",
            "year_of_study": 2,
            "interests": ["AI", "Data Science", "Python"],
            "learning_goals": "Master ML algorithms",
            "preferred_learning_style": "visual",
            "availability_notes": "Evenings and weekends",
        }

        response = client.patch(
            "/api/profile/student/me",
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
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"education_level": "graduate"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_student_profile_unauthorized(self, client):
        """Test updating student profile without auth fails."""
        response = client.patch(
            "/api/profile/student/me", json={"education_level": "graduate"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_with_empty_arrays(
        self, client, student_token, student_user, db_session
    ):
        """Test updating with empty arrays clears the field."""
        from models import StudentProfile

        # Create profile with interests
        profile = StudentProfile(user_id=student_user.id, interests=["Math", "Science"])
        db_session.add(profile)
        db_session.commit()

        # Clear interests
        response = client.patch(
            "/api/profile/student/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"interests": []},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["interests"] == []

    def test_update_year_of_study(
        self, client, student_token, student_user, db_session
    ):
        """Test updating year of study with valid values."""
        for year in [1, 2, 3, 4, 5]:
            response = client.patch(
                "/api/profile/student/me",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"year_of_study": year},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["year_of_study"] == year
