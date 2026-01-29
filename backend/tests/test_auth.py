"""Tests for authentication endpoints."""

from fastapi import status

from tests.conftest import STUDENT_PASSWORD, TEST_PASSWORD


class TestRegistration:
    """Test user registration."""

    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@test.com", "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "student"  # Default role
        assert "hashed_password" not in data
        assert data["avatar_url"] == "https://placehold.co/300x300?text=Avatar"

    def test_register_duplicate_email(self, client, student_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": student_user.email, "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_case_insensitive_email(self, client, student_user):
        """Test that email is case-insensitive."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": student_user.email.upper(), "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "notanemail", "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_too_short(self, client):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Ab1!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_too_long(self, client):
        """Test registration with password longer than 128 characters."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Aa1!" + "a" * 125},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_missing_uppercase(self, client):
        """Test registration with password missing uppercase."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "testpass123!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_missing_lowercase(self, client):
        """Test registration with password missing lowercase."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "TESTPASS123!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_missing_digit(self, client):
        """Test registration with password missing digit."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "TestPass!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_missing_special(self, client):
        """Test registration with password missing special character."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_email_normalization(self, client):
        """Test that email is normalized to lowercase."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "Test.User@EXAMPLE.COM", "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test.user@example.com"
        assert data["avatar_url"] == "https://placehold.co/300x300?text=Avatar"

    def test_register_missing_email(self, client):
        """Test registration without email."""
        response = client.post("/api/v1/auth/register", json={"password": TEST_PASSWORD})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_password(self, client):
        """Test registration without password."""
        response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test user login."""

    def test_login_success(self, client, student_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, student_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": "WrongPass123!"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@test.com", "password": TEST_PASSWORD},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client, student_user, db_session):
        """Test login with inactive user."""
        student_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_login_case_insensitive_email(self, client, student_user):
        """Test login is case-insensitive for email."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email.upper(), "password": STUDENT_PASSWORD},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_login_with_whitespace_email(self, client, student_user):
        """Test login trims whitespace from email."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": f"  {student_user.email}  ", "password": STUDENT_PASSWORD},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_login_missing_username(self, client):
        """Test login without username."""
        response = client.post("/api/v1/auth/login", data={"password": TEST_PASSWORD})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_password(self, client):
        """Test login without password."""
        response = client.post("/api/v1/auth/login", data={"username": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_password(self, client, student_user):
        """Test login with empty password."""
        response = client.post("/api/v1/auth/login", data={"username": student_user.email, "password": ""})
        # Empty password is a validation error (422) or auth failure (401)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_me_success(self, client, student_token, student_user):
        """Test successful get current user."""
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == student_user.email
        assert data["role"] == "student"
        assert data["avatar_url"] == "https://placehold.co/300x300?text=Avatar"

    def test_get_me_no_token(self, client):
        """Test get current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_invalid_token(self, client):
        """Test get current user with invalid token."""
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_student_cannot_access_admin_endpoint(self, client, student_token):
        """Test student cannot access admin endpoints."""
        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tutor_cannot_access_admin_endpoint(self, client, tutor_token):
        """Test tutor cannot access admin endpoints."""
        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_admin_endpoint(self, client, admin_token):
        """Test admin can access admin endpoints."""
        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_200_OK

    def test_student_cannot_create_tutor_profile(self, client, student_token):
        """Test student cannot create tutor profile."""
        response = client.post(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "title": "Test Tutor",
                "headline": "Test",
                "bio": "Test bio",
                "hourly_rate": 50,
                "subjects": [],
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
