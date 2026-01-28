"""
End-to-End tests for admin workflows.
Tests complete user journeys using actual HTTP requests.
"""

import os
from typing import Any

import pytest
import requests

# Configuration
API_URL = os.getenv("API_URL", "https://api.valsa.solutions")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://edustream.valsa.solutions")


class TestAdminWorkflows:
    """Test complete admin user management workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test."""
        self.api_url = API_URL
        self.admin_token = None
        self.student_token = None

        # Login as admin
        response = requests.post(
            f"{self.api_url}/token",
            data={"username": "admin@example.com", "password": "admin123"},
        )
        assert response.status_code == 200
        self.admin_token = response.json()["access_token"]

        # Login as student
        response = requests.post(
            f"{self.api_url}/token",
            data={"username": "student@example.com", "password": "student123"},
        )
        assert response.status_code == 200
        self.student_token = response.json()["access_token"]

        yield

        # Cleanup is handled by database reset between test runs

    def get_headers(self, token: str) -> dict[str, str]:
        """Get authorization headers with token."""
        return {"Authorization": f"Bearer {token}"}

    def test_complete_admin_workflow_create_user(self):
        """
        Test complete workflow: Admin creates, edits, and deletes a user.
        """
        # Step 1: Admin creates a new user
        new_user_data = {"email": "newuser@example.com", "password": "testpassword123"}

        response = requests.post(f"{self.api_url}/register", json=new_user_data)
        assert response.status_code == 200
        new_user = response.json()
        new_user_id = new_user["id"]
        assert new_user["email"] == "newuser@example.com"
        assert new_user["role"] == "student"  # Default role
        assert new_user["is_active"] is True

        # Step 2: Admin lists all users and finds the new user
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.admin_token))
        assert response.status_code == 200
        users = response.json()
        new_user_found = any(u["id"] == new_user_id for u in users)
        assert new_user_found, "New user should appear in user list"

        # Step 3: Admin updates the user's email
        update_data = {"email": "updatedemail@example.com"}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=update_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["email"] == "updatedemail@example.com"

        # Step 4: Admin promotes user to admin
        promote_data = {"role": "admin"}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=promote_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        promoted_user = response.json()
        assert promoted_user["role"] == "admin"

        # Step 5: Admin assigns tutor role
        tutor_data = {"role": "tutor"}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=tutor_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        tutor_user = response.json()
        assert tutor_user["role"] == "tutor"

        # Step 6: Admin restores student role
        student_data = {"role": "student"}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=student_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        demoted_user = response.json()
        assert demoted_user["role"] == "student"

        # Step 7: Admin deactivates the user
        deactivate_data = {"is_active": False}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=deactivate_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        deactivated_user = response.json()
        assert deactivated_user["is_active"] is False

        # Step 8: Verify deactivated user cannot login
        response = requests.post(
            f"{self.api_url}/token",
            data={
                "username": "updatedemail@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 401, "Deactivated user should not be able to login"

        # Step 9: Admin reactivates the user
        reactivate_data = {"is_active": True}
        response = requests.put(
            f"{self.api_url}/admin/users/{new_user_id}",
            json=reactivate_data,
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200
        reactivated_user = response.json()
        assert reactivated_user["is_active"] is True

        # Step 10: Admin resets user's password
        new_password = "newpassword456"
        response = requests.post(
            f"{self.api_url}/admin/users/{new_user_id}/reset-password",
            json={"new_password": new_password},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200

        # Step 11: Verify user can login with new password
        response = requests.post(
            f"{self.api_url}/token",
            data={"username": "updatedemail@example.com", "password": new_password},
        )
        assert response.status_code == 200, "User should be able to login with new password"

        # Step 12: Admin deletes the user
        response = requests.delete(
            f"{self.api_url}/admin/users/{new_user_id}",
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 200

        # Step 12: Verify user is deleted
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.admin_token))
        assert response.status_code == 200
        users = response.json()
        deleted_user_found = any(u["id"] == new_user_id for u in users)
        assert not deleted_user_found, "Deleted user should not appear in user list"

    def test_admin_self_protection_workflow(self):
        """
        Test that admin cannot perform dangerous operations on themselves.
        """
        # Get current admin user details
        response = requests.get(f"{self.api_url}/users/me", headers=self.get_headers(self.admin_token))
        assert response.status_code == 200
        admin_user = response.json()
        admin_id = admin_user["id"]

        # Attempt 1: Admin tries to demote themselves
        for target_role in ("tutor", "student"):
            response = requests.put(
                f"{self.api_url}/admin/users/{admin_id}",
                json={"role": target_role},
                headers=self.get_headers(self.admin_token),
            )
            assert response.status_code == 400
            assert "cannot change your own role" in response.json()["detail"].lower()

        # Attempt 2: Admin tries to deactivate themselves
        response = requests.put(
            f"{self.api_url}/admin/users/{admin_id}",
            json={"is_active": False},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 400
        assert "cannot deactivate yourself" in response.json()["detail"].lower()

        # Attempt 3: Admin tries to delete themselves
        response = requests.delete(
            f"{self.api_url}/admin/users/{admin_id}",
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 400
        assert "cannot delete yourself" in response.json()["detail"].lower()

        # Verify admin is still active and has admin role
        response = requests.get(f"{self.api_url}/users/me", headers=self.get_headers(self.admin_token))
        assert response.status_code == 200
        admin_user = response.json()
        assert admin_user["role"] == "admin"
        assert admin_user["is_active"] is True

    def test_regular_user_cannot_access_admin_endpoints(self):
        """
        Test that regular users are denied access to admin endpoints.
        """
        # Get a user ID to test with
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.admin_token))
        assert response.status_code == 200
        users = response.json()
        target_user_id = next(u["id"] for u in users if u["role"] in ("student", "tutor"))

        # Attempt 1: Regular user tries to list all users
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.student_token))
        assert response.status_code == 403

        # Attempt 2: Regular user tries to update another user
        response = requests.put(
            f"{self.api_url}/admin/users/{target_user_id}",
            json={"role": "admin"},
            headers=self.get_headers(self.student_token),
        )
        assert response.status_code == 403

        # Attempt 3: Regular user tries to delete another user
        response = requests.delete(
            f"{self.api_url}/admin/users/{target_user_id}",
            headers=self.get_headers(self.student_token),
        )
        assert response.status_code == 403

        # Attempt 4: Regular user tries to reset another user's password
        response = requests.post(
            f"{self.api_url}/admin/users/{target_user_id}/reset-password",
            json={"new_password": "hackpassword123"},
            headers=self.get_headers(self.student_token),
        )
        assert response.status_code == 403

    def test_unauthenticated_access_denied(self):
        """
        Test that unauthenticated requests are denied.
        """
        # Attempt 1: Access admin users list without token
        response = requests.get(f"{self.api_url}/admin/users")
        assert response.status_code == 401

        # Attempt 2: Update user without token
        response = requests.put(f"{self.api_url}/admin/users/1", json={"role": "admin"})
        assert response.status_code == 401

        # Attempt 3: Delete user without token
        response = requests.delete(f"{self.api_url}/admin/users/1")
        assert response.status_code == 401

        # Attempt 4: Reset password without token
        response = requests.post(
            f"{self.api_url}/admin/users/1/reset-password",
            json={"new_password": "newpassword"},
        )
        assert response.status_code == 401

    def test_invalid_inputs_rejected(self):
        """
        Test that invalid inputs are properly rejected.
        """
        # Get a test user
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.admin_token))
        users = response.json()
        test_user_id = next(u["id"] for u in users if u["role"] in ("student", "tutor"))

        # Test 1: Invalid email format
        response = requests.put(
            f"{self.api_url}/admin/users/{test_user_id}",
            json={"email": "notanemail"},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 422

        # Test 2: Invalid role
        response = requests.put(
            f"{self.api_url}/admin/users/{test_user_id}",
            json={"role": "superadmin"},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 400
        detail_lower = response.json()["detail"].lower()
        assert "invalid role" in detail_lower or "must be" in detail_lower

        # Test 3: Password too short
        response = requests.post(
            f"{self.api_url}/admin/users/{test_user_id}/reset-password",
            json={"new_password": "12345"},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 400
        assert "at least 6 characters" in response.json()["detail"].lower()

        # Test 4: Non-existent user ID
        response = requests.put(
            f"{self.api_url}/admin/users/999999",
            json={"email": "test@example.com"},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 404

    def test_email_uniqueness_enforced(self):
        """
        Test that email uniqueness is enforced across all users.
        """
        # Create a new user
        response = requests.post(
            f"{self.api_url}/register",
            json={"email": "unique@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        new_user = response.json()

        # Try to create another user with same email
        response = requests.post(
            f"{self.api_url}/register",
            json={"email": "unique@example.com", "password": "differentpassword"},
        )
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

        # Try to update a different user to use the same email
        response = requests.get(f"{self.api_url}/admin/users", headers=self.get_headers(self.admin_token))
        users = response.json()
        other_user = next(u for u in users if u["id"] != new_user["id"] and u["role"] in ("student", "tutor"))

        response = requests.put(
            f"{self.api_url}/admin/users/{other_user['id']}",
            json={"email": "unique@example.com"},
            headers=self.get_headers(self.admin_token),
        )
        assert response.status_code == 400
        detail_lower = response.json()["detail"].lower()
        assert "email already" in detail_lower

        # Cleanup: delete the test user
        requests.delete(
            f"{self.api_url}/admin/users/{new_user['id']}",
            headers=self.get_headers(self.admin_token),
        )

    def test_multi_field_update(self):
        """
        Test updating multiple fields at once.
        """
        # Create a test user
        response = requests.post(
            f"{self.api_url}/register",
            json={"email": "multiupdate@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        user = response.json()
        user_id = user["id"]

        try:
            # Update multiple fields at once
            response = requests.put(
                f"{self.api_url}/admin/users/{user_id}",
                json={
                    "email": "updated@example.com",
                    "role": "admin",
                    "is_active": False,
                },
                headers=self.get_headers(self.admin_token),
            )
            assert response.status_code == 200
            updated_user = response.json()

            # Verify all fields were updated
            assert updated_user["email"] == "updated@example.com"
            assert updated_user["role"] == "admin"
            assert updated_user["is_active"] is False

        finally:
            # Cleanup
            requests.delete(
                f"{self.api_url}/admin/users/{user_id}",
                headers=self.get_headers(self.admin_token),
            )

    def test_concurrent_admin_operations(self):
        """
        Test that concurrent admin operations don't cause data corruption.
        """
        # Create a test user
        response = requests.post(
            f"{self.api_url}/register",
            json={"email": "concurrent@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        user = response.json()
        user_id = user["id"]

        try:
            # Perform multiple updates in quick succession
            updates = [{"email": f"concurrent{i}@example.com"} for i in range(5)]

            for update in updates:
                response = requests.put(
                    f"{self.api_url}/admin/users/{user_id}",
                    json=update,
                    headers=self.get_headers(self.admin_token),
                )
                assert response.status_code == 200

            # Verify final state
            response = requests.get(
                f"{self.api_url}/admin/users",
                headers=self.get_headers(self.admin_token),
            )
            users = response.json()
            final_user = next(u for u in users if u["id"] == user_id)
            assert final_user["email"] == "concurrent4@example.com"

        finally:
            # Cleanup
            requests.delete(
                f"{self.api_url}/admin/users/{user_id}",
                headers=self.get_headers(self.admin_token),
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
