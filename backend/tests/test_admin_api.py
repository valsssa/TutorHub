"""Tests for admin API endpoints."""

from fastapi import status


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    def test_list_users_excludes_unapproved_tutors(self, client, admin_token, test_db_session):
        """Test that non-approved tutors don't appear in user management."""
        from models import TutorProfile, User

        # Create users
        student = User(email="student@test.com", hashed_password="hash", role="student")
        tutor_approved = User(email="tutor_approved@test.com", hashed_password="hash", role="tutor")
        tutor_pending = User(email="tutor_pending@test.com", hashed_password="hash", role="tutor")
        test_db_session.add_all([student, tutor_approved, tutor_pending])
        test_db_session.commit()

        # Create tutor profiles
        profile_approved = TutorProfile(
            user_id=tutor_approved.id,
            title="Approved Tutor",
            hourly_rate=50,
            is_approved=True,
            profile_status="approved",
        )
        profile_pending = TutorProfile(
            user_id=tutor_pending.id,
            title="Pending Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add_all([profile_approved, profile_pending])
        test_db_session.commit()

        response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        emails = [user["email"] for user in data["items"]]

        # Student and approved tutor should be visible
        assert "student@test.com" in emails
        assert "tutor_approved@test.com" in emails

        # Pending tutor should NOT be visible
        assert "tutor_pending@test.com" not in emails

    def test_list_users_requires_admin(self, client, student_token):
        """Test that non-admins cannot list users."""
        response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user(self, client, admin_token, test_db_session):
        """Test updating user details."""
        from models import User

        user = User(email="update@test.com", hashed_password="hash", role="student")
        test_db_session.add(user)
        test_db_session.commit()

        response = client.put(
            f"/api/admin/users/{user.id}",
            json={"role": "tutor"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "tutor"

    def test_admin_cannot_change_own_role(self, client, admin_token, admin_user):
        """Test that admin cannot change their own role."""
        response = client.put(
            f"/api/admin/users/{admin_user.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_user(self, client, admin_token, test_db_session):
        """Test soft-deleting a user."""
        from models import User

        user = User(email="delete@test.com", hashed_password="hash", role="student")
        test_db_session.add(user)
        test_db_session.commit()

        response = client.delete(
            f"/api/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user is soft-deleted
        test_db_session.refresh(user)
        assert user.is_active is False

    def test_admin_cannot_delete_themselves(self, client, admin_token, admin_user):
        """Test that admin cannot delete themselves."""
        response = client.delete(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAdminTutorApprovals:
    """Test admin tutor approval workflows."""

    def test_list_pending_tutors(self, client, admin_token, test_db_session):
        """Test listing pending tutor profiles."""
        from models import TutorProfile, User

        user = User(email="pending@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(user)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.get(
            "/api/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == "Test Tutor"

    def test_approve_tutor(self, client, admin_token, test_db_session):
        """Test approving a tutor profile."""
        from models import TutorProfile, User

        user = User(email="approve@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(user)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.post(
            f"/api/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_approved"] is True
        assert data["profile_status"] == "approved"
        assert data["approved_at"] is not None

        # Verify notification created
        from models import Notification

        notification = test_db_session.query(Notification).filter(Notification.user_id == user.id).first()
        assert notification is not None
        assert notification.type == "profile_approved"

    def test_reject_tutor(self, client, admin_token, test_db_session):
        """Test rejecting a tutor profile."""
        from models import TutorProfile, User

        user = User(email="reject@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(user)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.post(
            f"/api/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Insufficient qualifications provided"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_approved"] is False
        assert data["profile_status"] == "rejected"
        assert "Insufficient qualifications" in data["rejection_reason"]

        # Verify notification created
        from models import Notification

        notification = test_db_session.query(Notification).filter(Notification.user_id == user.id).first()
        assert notification is not None
        assert notification.type == "profile_rejected"

    def test_reject_tutor_requires_reason(self, client, admin_token, test_db_session):
        """Test that rejection requires a reason."""
        from models import TutorProfile, User

        user = User(email="reject2@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(user)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.post(
            f"/api/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Short"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_tutor_approval_requires_admin(self, client, student_token):
        """Test that non-admins cannot approve tutors."""
        response = client.post(
            "/api/admin/tutors/1/approve",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
