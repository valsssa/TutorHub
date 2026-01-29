"""
Comprehensive tests for tutor approval workflow.

Tests cover:
- Listing pending tutors
- Approving tutors
- Rejecting tutors with reasons
- Notification creation
- State transitions
- Edge cases and error handling
"""

from datetime import UTC, datetime

import pytest
from fastapi import status


class TestListPendingTutors:
    """Test listing tutors pending approval."""

    def test_list_pending_tutors_empty(self, client, admin_token):
        """Test listing when no pending tutors exist."""
        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_pending_tutors_with_results(self, client, admin_token, db_session):
        """Test listing pending tutors returns correct results."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="pending_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Pending Tutor",
            headline="Test headline",
            bio="Test bio for pending tutor",
            hourly_rate=50.00,
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
        assert any(t["title"] == "Pending Tutor" for t in data["items"])

    def test_list_pending_excludes_approved(self, client, admin_token, db_session):
        """Test that approved tutors are not in pending list."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="approved_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Approved Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["title"] != "Approved Tutor" for t in data["items"])

    def test_list_pending_includes_under_review(self, client, admin_token, db_session):
        """Test that under_review status tutors are included."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="under_review@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Under Review Tutor",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="under_review",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(t["title"] == "Under Review Tutor" for t in data["items"])

    def test_list_pending_requires_admin(self, client, student_token):
        """Test that only admins can list pending tutors."""
        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_pending_pagination(self, client, admin_token, db_session):
        """Test pagination of pending tutors list."""
        from models import TutorProfile, User
        from auth import get_password_hash

        for i in range(5):
            user = User(
                email=f"paginate_tutor_{i}@test.com",
                hashed_password=get_password_hash("password123"),
                role="tutor",
                is_active=True,
            )
            db_session.add(user)
            db_session.commit()

            profile = TutorProfile(
                user_id=user.id,
                title=f"Paginate Tutor {i}",
                hourly_rate=50.00,
                is_approved=False,
                profile_status="pending_approval",
            )
            db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/pending?page=1&page_size=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestApproveTutor:
    """Test tutor approval functionality."""

    def _create_pending_tutor(self, db_session, email="approve_test@test.com"):
        """Helper to create a pending tutor."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor for Approval",
            headline="Test headline",
            bio="Test bio content",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        return user, profile

    def test_approve_tutor_success(self, client, admin_token, db_session):
        """Test successful tutor approval."""
        user, profile = self._create_pending_tutor(db_session)

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_approved"] is True
        assert data["profile_status"] == "approved"
        assert data["approved_at"] is not None
        assert data["rejection_reason"] is None

    def test_approve_tutor_creates_notification(self, client, admin_token, db_session):
        """Test that approval creates a notification for the tutor."""
        from models import Notification

        user, profile = self._create_pending_tutor(
            db_session, email="notify_approve@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        notification = (
            db_session.query(Notification)
            .filter(Notification.user_id == user.id)
            .first()
        )
        assert notification is not None
        assert notification.type == "profile_approved"
        assert "approved" in notification.title.lower() or "live" in notification.title.lower()
        assert notification.is_read is False

    def test_approve_tutor_sets_approved_by(self, client, admin_token, db_session, admin_user):
        """Test that approval records the admin who approved."""
        user, profile = self._create_pending_tutor(
            db_session, email="approved_by@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(profile)
        assert profile.approved_by == admin_user.id

    def test_approve_already_approved(self, client, admin_token, db_session):
        """Test approving an already approved tutor fails."""
        user, profile = self._create_pending_tutor(
            db_session, email="already_approved@test.com"
        )
        profile.is_approved = True
        profile.profile_status = "approved"
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already approved" in response.json()["detail"].lower()

    def test_approve_nonexistent_tutor(self, client, admin_token):
        """Test approving a non-existent tutor fails."""
        response = client.post(
            "/api/v1/admin/tutors/99999/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_approve_requires_admin(self, client, student_token, db_session):
        """Test that only admins can approve tutors."""
        user, profile = self._create_pending_tutor(
            db_session, email="student_approve@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_approve_clears_rejection_reason(self, client, admin_token, db_session):
        """Test that approval clears any previous rejection reason."""
        user, profile = self._create_pending_tutor(
            db_session, email="clear_rejection@test.com"
        )
        profile.rejection_reason = "Previous rejection reason"
        profile.profile_status = "pending_approval"
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rejection_reason"] is None


class TestRejectTutor:
    """Test tutor rejection functionality."""

    def _create_pending_tutor(self, db_session, email="reject_test@test.com"):
        """Helper to create a pending tutor."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Test Tutor for Rejection",
            headline="Test headline",
            bio="Test bio content",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        return user, profile

    def test_reject_tutor_success(self, client, admin_token, db_session):
        """Test successful tutor rejection."""
        user, profile = self._create_pending_tutor(db_session)

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Please provide more details about your qualifications and experience."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_approved"] is False
        assert data["profile_status"] == "rejected"
        assert "qualifications" in data["rejection_reason"].lower()

    def test_reject_tutor_creates_notification(self, client, admin_token, db_session):
        """Test that rejection creates a notification for the tutor."""
        from models import Notification

        user, profile = self._create_pending_tutor(
            db_session, email="notify_reject@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Please provide more documentation about your teaching credentials."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        notification = (
            db_session.query(Notification)
            .filter(Notification.user_id == user.id)
            .first()
        )
        assert notification is not None
        assert notification.type == "profile_rejected"
        assert notification.is_read is False

    def test_reject_requires_reason(self, client, admin_token, db_session):
        """Test that rejection requires a reason."""
        user, profile = self._create_pending_tutor(
            db_session, email="no_reason@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": ""},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reject_reason_minimum_length(self, client, admin_token, db_session):
        """Test that rejection reason has minimum length."""
        user, profile = self._create_pending_tutor(
            db_session, email="short_reason@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Short"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "10 characters" in response.json()["detail"].lower()

    def test_reject_already_rejected(self, client, admin_token, db_session):
        """Test rejecting an already rejected tutor fails."""
        user, profile = self._create_pending_tutor(
            db_session, email="already_rejected@test.com"
        )
        profile.is_approved = False
        profile.profile_status = "rejected"
        profile.rejection_reason = "Previous rejection"
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "New rejection reason that is long enough"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already rejected" in response.json()["detail"].lower()

    def test_reject_nonexistent_tutor(self, client, admin_token):
        """Test rejecting a non-existent tutor fails."""
        response = client.post(
            "/api/v1/admin/tutors/99999/reject",
            json={"rejection_reason": "This tutor does not exist but reason is valid"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reject_requires_admin(self, client, student_token, db_session):
        """Test that only admins can reject tutors."""
        user, profile = self._create_pending_tutor(
            db_session, email="student_reject@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "This should fail because student cannot reject"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_reject_clears_approval_fields(self, client, admin_token, db_session):
        """Test that rejection clears approval-related fields."""
        user, profile = self._create_pending_tutor(
            db_session, email="clear_approval@test.com"
        )
        profile.approved_at = datetime.now(UTC)
        profile.approved_by = 1
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Profile needs significant improvements before approval."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["approved_at"] is None

    def test_reject_reason_sanitized(self, client, admin_token, db_session):
        """Test that rejection reason is sanitized for XSS."""
        user, profile = self._create_pending_tutor(
            db_session, email="xss_reject@test.com"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "<script>alert('xss')</script>Please improve your profile."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "<script>" not in data["rejection_reason"]


class TestListApprovedTutors:
    """Test listing approved tutors."""

    def test_list_approved_tutors(self, client, admin_token, db_session):
        """Test listing approved tutors."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="list_approved@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Listed Approved Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
            approved_at=datetime.now(UTC),
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/approved",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(t["title"] == "Listed Approved Tutor" for t in data["items"])

    def test_list_approved_excludes_pending(self, client, admin_token, db_session):
        """Test that pending tutors are not in approved list."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="pending_not_approved@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Pending Not Approved",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/approved",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["title"] != "Pending Not Approved" for t in data["items"])


class TestTutorApprovalStateTransitions:
    """Test state transitions in tutor approval workflow."""

    def _create_tutor_with_status(self, db_session, email, profile_status):
        """Helper to create tutor with specific status."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title=f"Tutor {profile_status}",
            hourly_rate=50.00,
            is_approved=profile_status == "approved",
            profile_status=profile_status,
        )
        db_session.add(profile)
        db_session.commit()

        return user, profile

    def test_pending_to_approved(self, client, admin_token, db_session):
        """Test transition from pending to approved."""
        user, profile = self._create_tutor_with_status(
            db_session, "pending_to_approved@test.com", "pending_approval"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["profile_status"] == "approved"

    def test_pending_to_rejected(self, client, admin_token, db_session):
        """Test transition from pending to rejected."""
        user, profile = self._create_tutor_with_status(
            db_session, "pending_to_rejected@test.com", "pending_approval"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Please provide verification documents for your credentials."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["profile_status"] == "rejected"

    def test_under_review_to_approved(self, client, admin_token, db_session):
        """Test transition from under_review to approved."""
        user, profile = self._create_tutor_with_status(
            db_session, "review_to_approved@test.com", "under_review"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["profile_status"] == "approved"

    def test_under_review_to_rejected(self, client, admin_token, db_session):
        """Test transition from under_review to rejected."""
        user, profile = self._create_tutor_with_status(
            db_session, "review_to_rejected@test.com", "under_review"
        )

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Background check did not pass our verification process."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["profile_status"] == "rejected"


class TestTutorVisibilityAfterApproval:
    """Test tutor visibility in user listings after approval status changes."""

    def test_approved_tutor_visible_in_user_list(self, client, admin_token, db_session):
        """Test approved tutors appear in admin user list."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="visible_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Visible Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        emails = [u["email"] for u in data["items"]]
        assert "visible_tutor@test.com" in emails

    def test_pending_tutor_hidden_in_user_list(self, client, admin_token, db_session):
        """Test pending tutors do not appear in admin user list."""
        from models import TutorProfile, User
        from auth import get_password_hash

        user = User(
            email="hidden_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Hidden Tutor",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        emails = [u["email"] for u in data["items"]]
        assert "hidden_tutor@test.com" not in emails
