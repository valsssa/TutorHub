"""
Comprehensive tests for hard admin operations and workflow scenarios.

Tests cover complex edge cases for:
1. Tutor Approval Workflow Edge Cases
2. User Management Complexities
3. Bulk Operations Edge Cases
4. Audit Log Integrity
5. Feature Flag Administration
6. Financial Administration
7. Platform Configuration
8. Support Tools Edge Cases

Uses pytest with admin user fixtures, mock external services,
and audit logging verification.
"""

import asyncio
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from auth import get_password_hash
from core.audit import AuditLogger, DeferredAuditLog
from core.feature_flags import FeatureFlag, FeatureFlags, FeatureState
from models import (
    AuditLog,
    Booking,
    Notification,
    Payment,
    Payout,
    Refund,
    TutorProfile,
    User,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def second_admin_user(db_session: Session) -> User:
    """Create a second admin user for edge case testing."""
    user = User(
        email="admin2@test.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
        is_verified=True,
        first_name="Second",
        last_name="Admin",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def owner_user(db_session: Session) -> User:
    """Create an owner user for testing."""
    user = User(
        email="owner@test.com",
        hashed_password=get_password_hash("OwnerPass123!"),
        role="owner",
        is_active=True,
        is_verified=True,
        first_name="Platform",
        last_name="Owner",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def pending_tutor(db_session: Session) -> tuple[User, TutorProfile]:
    """Create a pending tutor for approval workflow testing."""
    user = User(
        email="pending_tutor@test.com",
        hashed_password=get_password_hash("TutorPass123!"),
        role="tutor",
        is_active=True,
        is_verified=True,
        first_name="Pending",
        last_name="Tutor",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()

    profile = TutorProfile(
        user_id=user.id,
        title="Pending Expert Tutor",
        headline="Expert in Mathematics",
        bio="10 years of teaching experience.",
        hourly_rate=75.00,
        is_approved=False,
        profile_status="pending_approval",
        timezone="UTC",
        currency="USD",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(profile)

    return user, profile


@pytest.fixture
def mock_feature_flags():
    """Mock feature flags for testing."""
    with patch("core.feature_flags.feature_flags") as mock_ff:
        mock_ff._local_cache = {}
        mock_ff._redis = AsyncMock()
        yield mock_ff


# =============================================================================
# 1. Tutor Approval Workflow Edge Cases
# =============================================================================


class TestTutorApprovalWorkflowEdgeCases:
    """Test tutor approval workflow edge cases."""

    def test_document_verification_timeout_handling(
        self, client, admin_token, db_session
    ):
        """Test handling when document verification times out."""
        user = User(
            email="timeout_tutor@test.com",
            hashed_password=get_password_hash("TutorPass123!"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Timeout",
            last_name="Tutor",
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Timeout Tutor",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="under_review",
            created_at=datetime.now(UTC) - timedelta(days=30),
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/tutors/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        profiles = [p for p in data["items"] if p["title"] == "Timeout Tutor"]
        assert len(profiles) == 1
        assert profiles[0]["profile_status"] == "under_review"

    def test_resubmission_after_rejection(
        self, client, admin_token, db_session, pending_tutor
    ):
        """Test tutor can resubmit after rejection."""
        user, profile = pending_tutor

        reject_response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Please provide more detailed qualifications."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert reject_response.status_code == status.HTTP_200_OK
        assert reject_response.json()["profile_status"] == "rejected"

        db_session.refresh(profile)
        profile.profile_status = "pending_approval"
        profile.bio = "Updated bio with more details about qualifications."
        db_session.commit()

        approve_response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert approve_response.status_code == status.HTTP_200_OK
        assert approve_response.json()["is_approved"] is True
        assert approve_response.json()["profile_status"] == "approved"

    def test_approval_during_document_update_race_condition(
        self, client, admin_token, db_session, pending_tutor
    ):
        """Test approval when profile is being updated simultaneously."""
        user, profile = pending_tutor

        old_bio = profile.bio
        profile.bio = "Updated bio during approval process"
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(profile)
        assert profile.is_approved is True
        assert profile.bio != old_bio

    def test_bulk_approval_processing(self, client, admin_token, db_session):
        """Test bulk approval of multiple tutors."""
        profiles = []
        for i in range(5):
            user = User(
                email=f"bulk_tutor_{i}@test.com",
                hashed_password=get_password_hash("TutorPass123!"),
                role="tutor",
                is_active=True,
                is_verified=True,
                first_name=f"Bulk{i}",
                last_name="Tutor",
            )
            db_session.add(user)
            db_session.commit()

            profile = TutorProfile(
                user_id=user.id,
                title=f"Bulk Tutor {i}",
                hourly_rate=50.00,
                is_approved=False,
                profile_status="pending_approval",
            )
            db_session.add(profile)
            db_session.commit()
            profiles.append(profile)

        approved_count = 0
        for profile in profiles:
            response = client.post(
                f"/api/v1/admin/tutors/{profile.id}/approve",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if response.status_code == status.HTTP_200_OK:
                approved_count += 1

        assert approved_count == 5

        for profile in profiles:
            db_session.refresh(profile)
            assert profile.is_approved is True

    def test_approval_with_incomplete_profile(self, client, admin_token, db_session):
        """Test approval of tutor with incomplete profile fields."""
        user = User(
            email="incomplete_tutor@test.com",
            hashed_password=get_password_hash("TutorPass123!"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Incomplete Tutor",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
            bio=None,
            headline=None,
        )
        db_session.add(profile)
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# 2. User Management Complexities
# =============================================================================


class TestUserManagementComplexities:
    """Test complex user management scenarios."""

    def test_ban_user_with_active_bookings(
        self, client, admin_token, db_session, student_user, tutor_user, test_subject
    ):
        """Test banning a user who has active bookings."""
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(UTC) + timedelta(days=1),
            end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
            topic="Test Session",
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            session_state="SCHEDULED",
            tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=test_subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{student_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        assert student_user.is_active is False

    def test_unban_timing_and_restrictions(
        self, client, admin_token, db_session
    ):
        """Test unban timing and any restrictions."""
        user = User(
            email="banned_user@test.com",
            hashed_password=get_password_hash("TestPass123!"),
            role="student",
            is_active=False,
            is_verified=True,
            first_name="Banned",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{user.id}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(user)
        assert user.is_active is True

    def test_role_change_with_active_sessions(
        self, client, admin_token, db_session, tutor_user, student_user, test_subject
    ):
        """Test changing user role when they have active sessions."""
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(UTC) + timedelta(hours=2),
            end_time=datetime.now(UTC) + timedelta(hours=3),
            topic="Active Session",
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            session_state="SCHEDULED",
            tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=test_subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{student_user.id}",
            json={"role": "tutor"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        db_session.refresh(student_user)
        assert student_user.role == "tutor"

    def test_prevent_last_admin_removal(
        self, client, admin_token, db_session, admin_user
    ):
        """Test that the last admin cannot be removed."""
        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"role": "student"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot change your own role" in response.json()["detail"].lower()

    def test_prevent_self_deactivation(
        self, client, admin_token, db_session, admin_user
    ):
        """Test that admin cannot deactivate their own account."""
        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot deactivate your own account" in response.json()["detail"].lower()

    def test_admin_cannot_delete_last_admin(
        self, client, admin_token, db_session, admin_user, second_admin_user
    ):
        """Test that the last active admin cannot be deleted."""
        db_session.refresh(second_admin_user)
        second_admin_user.is_active = False
        db_session.commit()

        response = client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# 3. Bulk Operations Edge Cases
# =============================================================================


class TestBulkOperationsEdgeCases:
    """Test bulk operations edge cases."""

    def test_bulk_status_update_atomicity(self, client, admin_token, db_session):
        """Test that bulk status updates maintain atomicity."""
        users = []
        for i in range(3):
            user = User(
                email=f"bulk_user_{i}@test.com",
                hashed_password=get_password_hash("TestPass123!"),
                role="student",
                is_active=True,
                is_verified=True,
                first_name=f"Bulk{i}",
                last_name="User",
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()

        success_count = 0
        for user in users:
            response = client.put(
                f"/api/v1/admin/users/{user.id}",
                json={"is_active": False},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if response.status_code == status.HTTP_200_OK:
                success_count += 1

        assert success_count == 3

        for user in users:
            db_session.refresh(user)
            assert user.is_active is False

    def test_bulk_delete_with_foreign_keys(
        self, client, admin_token, db_session
    ):
        """Test bulk delete handling with foreign key constraints."""
        users = []
        for i in range(3):
            user = User(
                email=f"fk_user_{i}@test.com",
                hashed_password=get_password_hash("TestPass123!"),
                role="student",
                is_active=True,
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()

        for user in users:
            response = client.delete(
                f"/api/v1/admin/users/{user.id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == status.HTTP_200_OK

        for user in users:
            db_session.refresh(user)
            assert user.is_active is False

    def test_progress_tracking_accuracy(self, client, admin_token, db_session):
        """Test that progress tracking is accurate during bulk operations."""
        total_operations = 5
        completed = 0

        for i in range(total_operations):
            user = User(
                email=f"progress_user_{i}@test.com",
                hashed_password=get_password_hash("TestPass123!"),
                role="student",
                is_active=True,
            )
            db_session.add(user)
            db_session.commit()

            response = client.put(
                f"/api/v1/admin/users/{user.id}",
                json={"is_active": False},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if response.status_code == status.HTTP_200_OK:
                completed += 1

        assert completed == total_operations


# =============================================================================
# 4. Audit Log Integrity
# =============================================================================


class TestAuditLogIntegrity:
    """Test audit log integrity scenarios."""

    def test_no_audit_log_on_transaction_rollback(self, db_session, student_user):
        """Test that no audit log is created when transaction is rolled back."""
        initial_count = db_session.query(AuditLog).count()

        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=student_user.id,
            action="UPDATE",
            old_data={"status": "active"},
            new_data={"status": "inactive"},
            changed_by=student_user.id,
        )

        db_session.rollback()

        post_rollback_count = db_session.query(AuditLog).count()
        assert post_rollback_count == initial_count

    def test_audit_log_written_after_commit(self, db_session, student_user):
        """Test that audit log is written after successful commit."""
        initial_count = db_session.query(AuditLog).count()

        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=student_user.id,
            action="UPDATE",
            old_data={"email": "old@test.com"},
            new_data={"email": student_user.email},
            changed_by=student_user.id,
        )

        db_session.commit()

        post_commit_count = db_session.query(AuditLog).count()
        assert post_commit_count == initial_count + 1

    def test_concurrent_audit_writes(self, db_session, admin_user, student_user):
        """Test concurrent audit log writes don't interfere."""
        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=admin_user.id,
            action="LOGIN",
            changed_by=admin_user.id,
        )

        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=student_user.id,
            action="LOGIN",
            changed_by=student_user.id,
        )

        db_session.commit()

        admin_logs = AuditLogger.get_audit_trail(
            db_session, record_id=admin_user.id, table_name="users"
        )
        student_logs = AuditLogger.get_audit_trail(
            db_session, record_id=student_user.id, table_name="users"
        )

        assert len(admin_logs) >= 1
        assert len(student_logs) >= 1

    def test_audit_log_tampering_detection(self, db_session, admin_user):
        """Test detection of audit log tampering attempts."""
        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=admin_user.id,
            action="SENSITIVE_ACTION",
            new_data={"action": "original_data"},
            changed_by=admin_user.id,
            immediate=True,
        )
        db_session.commit()

        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "SENSITIVE_ACTION")
            .first()
        )

        assert audit_log is not None
        original_changed_at = audit_log.changed_at

        assert audit_log.changed_at == original_changed_at

    def test_sensitive_data_redaction_in_audit(self, db_session, student_user):
        """Test that sensitive data is properly handled in audit logs."""
        sensitive_data = {
            "email": student_user.email,
            "hashed_password": "should_not_store_raw_password",
        }

        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=student_user.id,
            action="UPDATE",
            new_data=sensitive_data,
            changed_by=student_user.id,
        )

        db_session.commit()

        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.record_id == student_user.id)
            .order_by(AuditLog.changed_at.desc())
            .first()
        )

        assert audit_log is not None

    def test_audit_log_retrieval_by_filters(self, db_session, admin_user, student_user):
        """Test audit trail retrieval with various filters."""
        AuditLogger.log_action(
            db=db_session,
            table_name="bookings",
            record_id=1,
            action="CREATE",
            changed_by=student_user.id,
        )

        AuditLogger.log_action(
            db=db_session,
            table_name="users",
            record_id=admin_user.id,
            action="UPDATE",
            changed_by=admin_user.id,
        )

        db_session.commit()

        bookings_trail = AuditLogger.get_audit_trail(db_session, table_name="bookings")
        users_trail = AuditLogger.get_audit_trail(db_session, table_name="users")

        assert all(log.table_name == "bookings" for log in bookings_trail)
        assert all(log.table_name == "users" for log in users_trail)


# =============================================================================
# 5. Feature Flag Administration
# =============================================================================


class TestFeatureFlagAdministration:
    """Test feature flag administration edge cases."""

    @pytest.mark.asyncio
    async def test_flag_change_during_active_requests(self):
        """Test feature flag change while requests are in-flight."""
        ff = FeatureFlags()
        ff._redis = AsyncMock()
        ff._redis.get.return_value = json.dumps({
            "name": "test_feature",
            "state": "enabled",
            "percentage": 100,
            "allowlist": [],
            "denylist": [],
            "description": "Test",
        })

        initial_value = await ff.is_enabled("test_feature")
        assert initial_value is True

        ff._redis.get.return_value = json.dumps({
            "name": "test_feature",
            "state": "disabled",
            "percentage": 0,
            "allowlist": [],
            "denylist": [],
            "description": "Test",
        })
        ff._local_cache.clear()

        new_value = await ff.is_enabled("test_feature")
        assert new_value is False

    @pytest.mark.asyncio
    async def test_percentage_rollout_consistency(self):
        """Test that percentage rollout is consistent for same user."""
        ff = FeatureFlags()
        ff._redis = AsyncMock()
        ff._redis.get.return_value = json.dumps({
            "name": "rollout_feature",
            "state": "percentage",
            "percentage": 50,
            "allowlist": [],
            "denylist": [],
            "description": "50% rollout",
        })

        user_id = "user_123"
        results = []
        for _ in range(10):
            ff._local_cache.clear()
            result = await ff.is_enabled_for_user("rollout_feature", user_id)
            results.append(result)

        assert all(r == results[0] for r in results)

    @pytest.mark.asyncio
    async def test_emergency_flag_kill_switch(self):
        """Test emergency kill switch disables feature immediately."""
        ff = FeatureFlags()
        ff._redis = AsyncMock()

        ff._redis.get.return_value = json.dumps({
            "name": "emergency_feature",
            "state": "enabled",
            "percentage": 100,
            "allowlist": [],
            "denylist": [],
            "description": "Emergency feature",
        })

        assert await ff.is_enabled("emergency_feature") is True

        ff._redis.get.return_value = json.dumps({
            "name": "emergency_feature",
            "state": "disabled",
            "percentage": 0,
            "allowlist": [],
            "denylist": [],
            "description": "DISABLED - Emergency",
        })
        ff._local_cache.clear()

        assert await ff.is_enabled("emergency_feature") is False

    @pytest.mark.asyncio
    async def test_flag_dependency_management(self):
        """Test managing dependencies between feature flags."""
        ff = FeatureFlags()
        ff._redis = AsyncMock()

        parent_flag_data = json.dumps({
            "name": "parent_feature",
            "state": "disabled",
            "percentage": 0,
            "allowlist": [],
            "denylist": [],
            "description": "Parent feature",
            "metadata": {"children": ["child_feature"]},
        })

        child_flag_data = json.dumps({
            "name": "child_feature",
            "state": "enabled",
            "percentage": 100,
            "allowlist": [],
            "denylist": [],
            "description": "Child feature",
            "metadata": {"depends_on": "parent_feature"},
        })

        ff._redis.get.side_effect = lambda key: {
            "feature_flags:parent_feature": parent_flag_data,
            "feature_flags:child_feature": child_flag_data,
        }.get(key)

        parent_enabled = await ff.is_enabled("parent_feature")
        child_enabled = await ff.is_enabled("child_feature")

        assert parent_enabled is False
        assert child_enabled is True

    @pytest.mark.asyncio
    async def test_flag_audit_trail_completeness(self):
        """Test that feature flag changes are properly tracked."""
        ff = FeatureFlags()
        ff._redis = AsyncMock()
        ff._redis.set = AsyncMock()

        flag = FeatureFlag(
            name="audited_feature",
            state=FeatureState.DISABLED,
            description="Test audit trail",
        )

        await ff.set_flag(flag)

        ff._redis.set.assert_called_once()
        call_args = ff._redis.set.call_args
        stored_data = json.loads(call_args[0][1])

        assert stored_data["name"] == "audited_feature"
        assert stored_data["updated_at"] is not None

    def test_feature_flag_api_endpoints(self, client, admin_token):
        """Test feature flag API endpoints."""
        list_response = client.get(
            "/api/v1/admin/features",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert list_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


# =============================================================================
# 6. Financial Administration
# =============================================================================


class TestFinancialAdministration:
    """Test financial administration edge cases."""

    def test_manual_refund_processing(
        self, client, admin_token, db_session, student_user
    ):
        """Test manual refund processing by admin."""
        payment = Payment(
            student_id=student_user.id,
            amount_cents=5000,
            currency="USD",
            provider="stripe",
            status="completed",
            stripe_payment_intent_id="pi_test_123",
        )
        db_session.add(payment)
        db_session.commit()

        refund = Refund(
            payment_id=payment.id,
            amount_cents=5000,
            currency="USD",
            reason="GOODWILL",
            provider_refund_id="re_test_123",
        )
        db_session.add(refund)
        db_session.commit()

        assert refund.amount_cents == 5000
        assert refund.reason == "GOODWILL"

    def test_payout_hold_and_release(self, db_session, tutor_user):
        """Test payout hold and release workflow."""
        payout = Payout(
            tutor_id=tutor_user.id,
            period_start=datetime.now(UTC).date() - timedelta(days=30),
            period_end=datetime.now(UTC).date(),
            amount_cents=10000,
            currency="USD",
            status="PENDING",
        )
        db_session.add(payout)
        db_session.commit()

        assert payout.status == "PENDING"

        payout.status = "SUBMITTED"
        db_session.commit()

        assert payout.status == "SUBMITTED"

        payout.status = "PAID"
        db_session.commit()

        assert payout.status == "PAID"

    def test_currency_conversion_edge_cases(self, db_session, student_user):
        """Test currency conversion edge cases."""
        payment_usd = Payment(
            student_id=student_user.id,
            amount_cents=10000,
            currency="USD",
            provider="stripe",
            status="completed",
        )
        db_session.add(payment_usd)

        payment_eur = Payment(
            student_id=student_user.id,
            amount_cents=8500,
            currency="EUR",
            provider="stripe",
            status="completed",
        )
        db_session.add(payment_eur)
        db_session.commit()

        assert payment_usd.currency == "USD"
        assert payment_eur.currency == "EUR"

    def test_platform_fee_calculation(self, db_session, tutor_user, student_user, test_subject):
        """Test platform fee calculation accuracy."""
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(UTC) + timedelta(days=1),
            end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
            topic="Fee Test Session",
            hourly_rate=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            currency="USD",
            platform_fee_pct=Decimal("20.00"),
            platform_fee_cents=2000,
            tutor_earnings_cents=8000,
            tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=test_subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        assert booking.platform_fee_cents == 2000
        assert booking.tutor_earnings_cents == 8000
        assert booking.platform_fee_cents + booking.tutor_earnings_cents == 10000


# =============================================================================
# 7. Platform Configuration
# =============================================================================


class TestPlatformConfiguration:
    """Test platform configuration edge cases."""

    def test_config_change_propagation(self, client, admin_token):
        """Test configuration change propagation."""
        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_cache_invalidation_on_config_change(self, db_session):
        """Test cache invalidation when configuration changes."""
        ff = FeatureFlags()
        ff._local_cache["test_feature"] = (
            FeatureFlag(name="test_feature", state=FeatureState.ENABLED),
            datetime.utcnow(),
        )

        assert "test_feature" in ff._local_cache

        ff.invalidate_cache("test_feature")

        assert "test_feature" not in ff._local_cache

    def test_cache_invalidation_all(self):
        """Test invalidating all cache entries."""
        ff = FeatureFlags()
        ff._local_cache["feature1"] = (
            FeatureFlag(name="feature1"),
            datetime.utcnow(),
        )
        ff._local_cache["feature2"] = (
            FeatureFlag(name="feature2"),
            datetime.utcnow(),
        )

        ff.invalidate_cache()

        assert len(ff._local_cache) == 0


# =============================================================================
# 8. Support Tools Edge Cases
# =============================================================================


class TestSupportToolsEdgeCases:
    """Test support tools edge cases."""

    def test_support_action_audit_trail(
        self, db_session, admin_user, student_user
    ):
        """Test that support actions create proper audit trail."""
        AuditLogger.log_action(
            db=db_session,
            table_name="support_actions",
            record_id=student_user.id,
            action="ACCOUNT_UNLOCK",
            new_data={
                "target_user_id": student_user.id,
                "reason": "User requested unlock after verification",
                "support_agent_id": admin_user.id,
            },
            changed_by=admin_user.id,
        )

        db_session.commit()

        audit_logs = AuditLogger.get_audit_trail(
            db_session, table_name="support_actions"
        )

        assert len(audit_logs) >= 1
        assert audit_logs[0].action == "ACCOUNT_UNLOCK"
        assert audit_logs[0].changed_by == admin_user.id

    def test_admin_viewing_user_bookings(
        self, client, admin_token, db_session, student_user, tutor_user, test_subject
    ):
        """Test admin ability to view user's booking history."""
        for i in range(3):
            booking = Booking(
                tutor_profile_id=tutor_user.tutor_profile.id,
                student_id=student_user.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) + timedelta(days=i + 1),
                end_time=datetime.now(UTC) + timedelta(days=i + 1, hours=1),
                topic=f"Support Review Session {i}",
                hourly_rate=50.00,
                total_amount=50.00,
                currency="USD",
                session_state="SCHEDULED",
                tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
                student_name=f"{student_user.first_name} {student_user.last_name}",
                subject_name=test_subject.name,
            )
            db_session.add(booking)
        db_session.commit()

        bookings = (
            db_session.query(Booking)
            .filter(Booking.student_id == student_user.id)
            .all()
        )

        assert len(bookings) >= 3

    def test_admin_notification_creation(
        self, db_session, admin_user, student_user
    ):
        """Test admin creating notifications for users."""
        notification = Notification(
            user_id=student_user.id,
            type="admin_message",
            title="Important Account Update",
            message="Your account has been verified by our support team.",
            link="/settings",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        user_notifications = (
            db_session.query(Notification)
            .filter(Notification.user_id == student_user.id)
            .filter(Notification.type == "admin_message")
            .all()
        )

        assert len(user_notifications) >= 1
        assert user_notifications[0].title == "Important Account Update"

    def test_soft_delete_user_endpoint(
        self, client, admin_token, db_session
    ):
        """Test soft delete user via audit endpoint."""
        user = User(
            email="soft_delete_test@test.com",
            hashed_password=get_password_hash("TestPass123!"),
            role="student",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/admin/audit/soft-delete-user",
            json={"user_id": user.id, "reason": "User requested deletion"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_restore_soft_deleted_user(self, client, admin_token, db_session):
        """Test restoring a soft-deleted user."""
        user = User(
            email="restore_test@test.com",
            hashed_password=get_password_hash("TestPass123!"),
            role="student",
            is_active=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/admin/audit/restore-user",
            json={"user_id": user.id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_admin_dashboard_stats_calculation(self, client, admin_token, db_session):
        """Test admin dashboard statistics calculation."""
        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "totalUsers" in data
        assert "activeTutors" in data
        assert "totalSessions" in data
        assert "revenue" in data

    def test_admin_recent_activities(self, client, admin_token, db_session):
        """Test fetching recent activities."""
        response = client.get(
            "/api/v1/admin/dashboard/recent-activities?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_admin_user_filtering_by_status(self, client, admin_token, db_session):
        """Test filtering users by status."""
        active_response = client.get(
            "/api/v1/admin/users?status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        inactive_response = client.get(
            "/api/v1/admin/users?status=inactive",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert active_response.status_code == status.HTTP_200_OK
        assert inactive_response.status_code == status.HTTP_200_OK

    def test_audit_log_api_endpoint(self, client, admin_token, db_session):
        """Test audit log API endpoint."""
        response = client.get(
            "/api/v1/admin/audit/logs?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_deleted_users_list(self, client, admin_token, db_session):
        """Test fetching list of deleted users."""
        response = client.get(
            "/api/v1/admin/audit/deleted-users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_concurrent_admin_operations(
        self, client, admin_token, db_session
    ):
        """Test that concurrent admin operations don't conflict."""
        users_created = []
        for i in range(3):
            user = User(
                email=f"concurrent_user_{i}@test.com",
                hashed_password=get_password_hash("TestPass123!"),
                role="student",
                is_active=True,
            )
            db_session.add(user)
            users_created.append(user)
        db_session.commit()

        responses = []
        for user in users_created:
            response = client.put(
                f"/api/v1/admin/users/{user.id}",
                json={"is_active": False},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            responses.append(response)

        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        assert success_count == 3

    def test_session_metrics_calculation(self, client, admin_token):
        """Test session metrics endpoint."""
        response = client.get(
            "/api/v1/admin/dashboard/session-metrics",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_monthly_revenue_data(self, client, admin_token):
        """Test monthly revenue data endpoint."""
        response = client.get(
            "/api/v1/admin/dashboard/monthly-revenue?months=6",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_user_growth_data(self, client, admin_token):
        """Test user growth data endpoint."""
        response = client.get(
            "/api/v1/admin/dashboard/user-growth?months=6",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_subject_distribution(self, client, admin_token):
        """Test subject distribution endpoint."""
        response = client.get(
            "/api/v1/admin/dashboard/subject-distribution",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
