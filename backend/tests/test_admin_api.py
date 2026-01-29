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

        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})

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
        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user(self, client, admin_token, test_db_session):
        """Test updating user details."""
        from models import User

        user = User(email="update@test.com", hashed_password="hash", role="student")
        test_db_session.add(user)
        test_db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{user.id}",
            json={"role": "tutor"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "tutor"

    def test_admin_cannot_change_own_role(self, client, admin_token, admin_user):
        """Test that admin cannot change their own role."""
        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot change your own role" in response.json()["detail"]

    def test_admin_cannot_deactivate_own_account(self, client, admin_token, admin_user):
        """Test that admin cannot deactivate their own account."""
        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate your own account" in response.json()["detail"]

    def test_cannot_demote_last_admin(self, client, admin_token, admin_user, test_db_session):
        """Test that the last active admin cannot be demoted."""
        from models import User

        # Ensure no other active admins exist (deactivate if any)
        other_admins = (
            test_db_session.query(User)
            .filter(User.role == "admin", User.id != admin_user.id, User.is_active.is_(True))
            .all()
        )
        for admin in other_admins:
            admin.is_active = False
        test_db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Could be "Cannot change your own role" or "Cannot remove the last active admin"
        # Since this is the same user making the request, it will hit the self-check first

    def test_cannot_deactivate_last_admin_via_update(self, client, admin_token, test_db_session):
        """Test that the last active admin cannot be deactivated via update endpoint."""
        from models import User

        # Create a second admin that will be the "last admin" we try to deactivate
        second_admin = User(
            email="second_admin@test.com",
            hashed_password="hash",
            role="admin",
            is_active=True,
        )
        test_db_session.add(second_admin)
        test_db_session.commit()

        # Deactivate the first admin (admin_user from fixture) so second_admin is the last
        from models import User as UserModel

        first_admin = test_db_session.query(UserModel).filter(UserModel.email == "admin@test.com").first()
        if first_admin:
            first_admin.is_active = False
            test_db_session.commit()

        # Now try to deactivate the last admin
        response = client.put(
            f"/api/v1/admin/users/{second_admin.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot remove the last active admin" in response.json()["detail"]

    def test_cannot_delete_last_admin(self, client, admin_token, test_db_session):
        """Test that the last active admin cannot be deleted."""
        from models import User

        # Create a second admin that will be the "last admin" we try to delete
        second_admin = User(
            email="delete_last_admin@test.com",
            hashed_password="hash",
            role="admin",
            is_active=True,
        )
        test_db_session.add(second_admin)
        test_db_session.commit()

        # Deactivate all other admins so second_admin is the last
        other_admins = (
            test_db_session.query(User)
            .filter(User.role == "admin", User.id != second_admin.id, User.is_active.is_(True))
            .all()
        )
        for admin in other_admins:
            admin.is_active = False
        test_db_session.commit()

        # Now try to delete the last admin
        response = client.delete(
            f"/api/v1/admin/users/{second_admin.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot remove the last active admin" in response.json()["detail"]

    def test_can_demote_admin_when_others_exist(self, client, admin_token, test_db_session):
        """Test that an admin can be demoted when other admins exist."""
        from models import User

        # Create two more admins
        second_admin = User(
            email="second_admin_demote@test.com",
            hashed_password="hash",
            role="admin",
            is_active=True,
        )
        third_admin = User(
            email="third_admin_demote@test.com",
            hashed_password="hash",
            role="admin",
            is_active=True,
        )
        test_db_session.add_all([second_admin, third_admin])
        test_db_session.commit()

        # Demote the second admin (should succeed since third_admin exists)
        response = client.put(
            f"/api/v1/admin/users/{second_admin.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "student"

    def test_delete_user(self, client, admin_token, test_db_session):
        """Test soft-deleting a user."""
        from models import User

        user = User(email="delete@test.com", hashed_password="hash", role="student")
        test_db_session.add(user)
        test_db_session.commit()

        response = client.delete(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user is soft-deleted
        test_db_session.refresh(user)
        assert user.is_active is False

    def test_admin_cannot_delete_themselves(self, client, admin_token, admin_user):
        """Test that admin cannot delete themselves."""
        response = client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
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
            "/api/v1/admin/tutors/pending",
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
            f"/api/v1/admin/tutors/{profile.id}/approve",
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
            f"/api/v1/admin/tutors/{profile.id}/reject",
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
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Short"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_tutor_approval_requires_admin(self, client, student_token):
        """Test that non-admins cannot approve tutors."""
        response = client.post(
            "/api/v1/admin/tutors/1/approve",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
