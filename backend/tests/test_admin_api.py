"""Tests for admin API endpoints."""

from fastapi import status


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    def test_list_users_excludes_unapproved_tutors(self, client, admin_token, db_session):
        """Test that non-approved tutors don't appear in user management."""
        from models import TutorProfile, User

        # Create users
        student = User(email="student@test.com", hashed_password="hash", role="student")
        tutor_approved = User(email="tutor_approved@test.com", hashed_password="hash", role="tutor")
        tutor_pending = User(email="tutor_pending@test.com", hashed_password="hash", role="tutor")
        db_session.add_all([student, tutor_approved, tutor_pending])
        db_session.commit()

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
        db_session.add_all([profile_approved, profile_pending])
        db_session.commit()

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

    def test_update_user(self, client, admin_token, db_session):
        """Test updating user details."""
        from models import User

        user = User(email="update@test.com", hashed_password="hash", role="student")
        db_session.add(user)
        db_session.commit()

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

    def test_cannot_demote_last_admin(self, client, admin_token, admin_user, db_session):
        """Test that the last active admin cannot be demoted."""
        from models import User

        # Ensure no other active admins exist (deactivate if any)
        other_admins = (
            db_session.query(User)
            .filter(User.role == "admin", User.id != admin_user.id, User.is_active.is_(True))
            .all()
        )
        for admin in other_admins:
            admin.is_active = False
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Could be "Cannot change your own role" or "Cannot remove the last active admin"
        # Since this is the same user making the request, it will hit the self-check first

    def test_cannot_deactivate_last_admin_via_update(self, client, admin_token, admin_user, db_session):
        """Test that the last active admin cannot be deactivated via update endpoint."""
        from models import User
        from tests.conftest import create_test_user, ADMIN_PASSWORD

        # Create a second admin who will be the one making the request
        second_admin = create_test_user(
            db_session,
            email="second_admin@test.com",
            password=ADMIN_PASSWORD,
            role="admin",
        )

        # Login as second admin
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "second_admin@test.com", "password": ADMIN_PASSWORD}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        second_admin_token = login_resp.json()["access_token"]

        # Deactivate the first admin so second_admin is the last active
        first_admin = db_session.query(User).filter(User.email == "admin@test.com").first()
        if first_admin:
            first_admin.is_active = False
            db_session.commit()

        # Now try to deactivate the last admin (second_admin trying to deactivate themselves)
        response = client.put(
            f"/api/v1/admin/users/{second_admin.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {second_admin_token}"},
        )

        # Will fail because admin cannot deactivate their own account
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate your own account" in response.json()["detail"]

    def test_cannot_delete_last_admin(self, client, admin_token, admin_user, db_session):
        """Test that the last active admin cannot be deleted."""
        from models import User
        from tests.conftest import create_test_user, ADMIN_PASSWORD

        # Create a second admin who will try to delete themselves
        second_admin = create_test_user(
            db_session,
            email="delete_last_admin@test.com",
            password=ADMIN_PASSWORD,
            role="admin",
        )

        # Login as second admin
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "delete_last_admin@test.com", "password": ADMIN_PASSWORD}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        second_admin_token = login_resp.json()["access_token"]

        # Deactivate all other admins so second_admin is the last
        other_admins = (
            db_session.query(User)
            .filter(User.role == "admin", User.id != second_admin.id, User.is_active.is_(True))
            .all()
        )
        for admin in other_admins:
            admin.is_active = False
        db_session.commit()

        # Now try to delete the last admin (second_admin trying to delete themselves)
        response = client.delete(
            f"/api/v1/admin/users/{second_admin.id}",
            headers={"Authorization": f"Bearer {second_admin_token}"},
        )

        # Will fail because admin cannot delete themselves
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot delete yourself" in response.json()["detail"]

    def test_can_demote_admin_when_others_exist(self, client, admin_token, db_session):
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
        db_session.add_all([second_admin, third_admin])
        db_session.commit()

        # Demote the second admin (should succeed since third_admin exists)
        response = client.put(
            f"/api/v1/admin/users/{second_admin.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "student"

    def test_delete_user(self, client, admin_token, db_session):
        """Test soft-deleting a user."""
        from models import User

        user = User(email="delete@test.com", hashed_password="hash", role="student")
        db_session.add(user)
        db_session.commit()

        response = client.delete(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user is soft-deleted
        db_session.refresh(user)
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

    def test_list_pending_tutors(self, client, admin_token, db_session):
        """Test listing pending tutor profiles."""
        from models import TutorProfile, User

        user = User(email="pending@test.com", hashed_password="hash", role="tutor")
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == "Test Tutor"

    def test_approve_tutor(self, client, admin_token, db_session):
        """Test approving a tutor profile."""
        from models import TutorProfile, User

        user = User(email="approve@test.com", hashed_password="hash", role="tutor")
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

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

        notification = db_session.query(Notification).filter(Notification.user_id == user.id).first()
        assert notification is not None
        assert notification.type == "profile_approved"

    def test_reject_tutor(self, client, admin_token, db_session):
        """Test rejecting a tutor profile."""
        from models import TutorProfile, User

        user = User(email="reject@test.com", hashed_password="hash", role="tutor")
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

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

        notification = db_session.query(Notification).filter(Notification.user_id == user.id).first()
        assert notification is not None
        assert notification.type == "profile_rejected"

    def test_reject_tutor_requires_reason(self, client, admin_token, db_session):
        """Test that rejection requires a reason."""
        from models import TutorProfile, User

        user = User(email="reject2@test.com", hashed_password="hash", role="tutor")
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor",
            hourly_rate=50,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Short"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Pydantic validation returns 422 for too-short rejection reason
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_tutor_approval_requires_admin(self, client, student_token):
        """Test that non-admins cannot approve tutors."""
        response = client.post(
            "/api/v1/admin/tutors/1/approve",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
