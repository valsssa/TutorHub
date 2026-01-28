"""Tests for admin endpoints."""

from fastapi import status


class TestListUsers:
    """Test listing all users."""

    def test_admin_list_users(self, client, admin_token, student_user, tutor_user):
        """Test admin can list all users."""
        response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert "items" in payload
        assert payload["total"] >= 3  # admin, tutor, student

        emails = {item["email"] for item in payload["items"]}
        assert student_user.email in emails
        assert tutor_user.email in emails

    def test_admin_list_users_includes_inactive(self, client, admin_token, student_user):
        """Deactivated users remain visible in admin dashboard."""
        deactivate_response = client.put(
            f"/api/admin/users/{student_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )
        assert deactivate_response.status_code == status.HTTP_200_OK

        default_response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert default_response.status_code == status.HTTP_200_OK
        default_payload = default_response.json()
        inactive_user = next(
            (item for item in default_payload["items"] if item["email"] == student_user.email),
            None,
        )
        assert inactive_user is not None
        assert inactive_user["is_active"] is False

        inactive_response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"status": "inactive"},
        )
        assert inactive_response.status_code == status.HTTP_200_OK
        inactive_payload = inactive_response.json()
        assert all(item["is_active"] is False for item in inactive_payload["items"])
        emails = {item["email"] for item in inactive_payload["items"]}
        assert student_user.email in emails

    def test_student_cannot_list_users(self, client, student_token):
        """Test student cannot access admin endpoint."""
        response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tutor_cannot_list_users(self, client, tutor_token):
        """Test tutor cannot access admin endpoint."""
        response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {tutor_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUser:
    """Test updating users."""

    def test_admin_update_user_role(self, client, admin_token, student_user):
        """Test admin can update user role."""
        response = client.put(
            f"/api/admin/users/{student_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "tutor"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "tutor"

    def test_admin_deactivate_user(self, client, admin_token, student_user):
        """Test admin can deactivate user."""
        response = client.put(
            f"/api/admin/users/{student_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    def test_admin_cannot_change_own_role(self, client, admin_token, admin_user):
        """Test admin cannot demote themselves."""
        response = client.put(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "student"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own role" in response.json()["detail"].lower()

    def test_admin_update_nonexistent_user(self, client, admin_token):
        """Test updating nonexistent user."""
        response = client.put(
            "/api/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "tutor"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_update_user(self, client, student_token, tutor_user):
        """Test student cannot update users."""
        response = client.put(
            f"/api/admin/users/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"role": "admin"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteUser:
    """Test deleting users."""

    def test_admin_delete_user(self, client, admin_token, db_session):
        """Test admin can delete user."""
        from auth import get_password_hash
        from models import User

        # Create user to delete
        user_to_delete = User(
            email="delete_me@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
        )
        db_session.add(user_to_delete)
        db_session.commit()
        user_id = user_to_delete.id

        response = client.delete(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_admin_cannot_delete_self(self, client, admin_token, admin_user):
        """Test admin cannot delete themselves."""
        response = client.delete(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "yourself" in response.json()["detail"].lower()

    def test_admin_delete_nonexistent_user(self, client, admin_token):
        """Test deleting nonexistent user."""
        response = client.delete("/api/admin/users/99999", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_delete_user(self, client, student_token, tutor_user):
        """Test student cannot delete users."""
        response = client.delete(
            f"/api/admin/users/{tutor_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
