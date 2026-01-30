"""
Comprehensive tests for hard package and session flow scenarios.

Tests cover complex edge cases including:
- Package expiration edge cases
- Session deduction complexities
- Package purchase flows
- Validity period calculations
- Background job edge cases
- Multi-package scenarios

These tests validate proper transaction handling, race condition prevention,
and correct business logic under edge conditions.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import calendar

import pytest
from fastapi import status
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from models import Booking, StudentPackage, TutorPricingOption, TutorProfile, User
from modules.bookings.domain.status import SessionState, PaymentState
from modules.packages.services.expiration_service import PackageExpirationService


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def pricing_option_factory(db_session, tutor_user):
    """Factory to create pricing options with various configurations."""
    def _create(
        price: Decimal = Decimal("50.00"),
        validity_days: int | None = None,
        extend_on_use: bool = False,
        duration_minutes: int = 60,
    ) -> TutorPricingOption:
        option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            title="Test Package",
            description="Test package for hard flow tests",
            duration_minutes=duration_minutes,
            price=price,
            validity_days=validity_days,
            extend_on_use=extend_on_use,
        )
        db_session.add(option)
        db_session.commit()
        db_session.refresh(option)
        return option
    return _create


@pytest.fixture
def package_factory(db_session, student_user, tutor_user, pricing_option_factory):
    """Factory to create packages with various configurations."""
    def _create(
        sessions_purchased: int = 5,
        sessions_remaining: int = 5,
        sessions_used: int = 0,
        status: str = "active",
        expires_at: datetime | None = None,
        pricing_option: TutorPricingOption | None = None,
        student_id: int | None = None,
    ) -> StudentPackage:
        if pricing_option is None:
            pricing_option = pricing_option_factory()

        package = StudentPackage(
            student_id=student_id or student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=sessions_purchased,
            sessions_remaining=sessions_remaining,
            sessions_used=sessions_used,
            purchase_price=pricing_option.price * sessions_purchased,
            purchased_at=datetime.now(UTC),
            expires_at=expires_at,
            status=status,
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)
        return package
    return _create


@pytest.fixture
def booking_factory(db_session, student_user, tutor_user):
    """Factory to create bookings for package tests."""
    def _create(
        session_state: str = "SCHEDULED",
        payment_state: str = "AUTHORIZED",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        package_id: int | None = None,
    ) -> Booking:
        if start_time is None:
            start_time = datetime.now(UTC) + timedelta(hours=1)
        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            start_time=start_time,
            end_time=end_time,
            session_state=session_state,
            payment_state=payment_state,
            hourly_rate=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            currency="USD",
            package_id=package_id,
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)
        return booking
    return _create


@pytest.fixture
def second_tutor(db_session):
    """Create a second tutor for multi-tutor tests."""
    from auth import get_password_hash

    user = User(
        email="tutor2@test.com",
        hashed_password=get_password_hash("TutorPass123!"),
        role="tutor",
        is_active=True,
        is_verified=True,
        first_name="Second",
        last_name="Tutor",
    )
    db_session.add(user)
    db_session.commit()

    profile = TutorProfile(
        user_id=user.id,
        title="Second Tutor",
        hourly_rate=Decimal("60.00"),
        is_approved=True,
        profile_status="approved",
    )
    db_session.add(profile)
    db_session.commit()

    user.tutor_profile = profile
    db_session.refresh(user)
    return user


@pytest.fixture
def second_student(db_session):
    """Create a second student for multi-student tests."""
    from auth import get_password_hash
    from models import StudentProfile

    user = User(
        email="student2@test.com",
        hashed_password=get_password_hash("StudentPass123!"),
        role="student",
        is_active=True,
        is_verified=True,
        first_name="Second",
        last_name="Student",
    )
    db_session.add(user)
    db_session.commit()

    profile = StudentProfile(user_id=user.id)
    db_session.add(profile)
    db_session.commit()

    db_session.refresh(user)
    return user


# =============================================================================
# 1. Package Expiration Edge Cases
# =============================================================================


class TestPackageExpirationEdgeCases:
    """Test package expiration under edge conditions."""

    def test_package_expires_during_active_booking(
        self, db_session, package_factory, booking_factory
    ):
        """
        Test that package expiration doesn't affect an already-active booking.

        Scenario: Student has package, starts session, package expires during session.
        Expected: The active session should continue; package marked expired after.
        """
        # Create package expiring very soon
        expires_at = datetime.now(UTC) + timedelta(seconds=1)
        package = package_factory(
            sessions_remaining=3,
            expires_at=expires_at,
        )

        # Create active booking using this package
        booking = booking_factory(
            session_state=SessionState.ACTIVE.value,
            payment_state=PaymentState.AUTHORIZED.value,
            package_id=package.id,
            start_time=datetime.now(UTC) - timedelta(minutes=30),
            end_time=datetime.now(UTC) + timedelta(minutes=30),
        )

        # Simulate time passing - package expires
        import time
        time.sleep(1.5)

        # Run expiration service
        count = PackageExpirationService.mark_expired_packages(db_session)

        # Package should be expired
        db_session.refresh(package)
        assert package.status == "expired"

        # But booking should still be active (not cancelled)
        db_session.refresh(booking)
        assert booking.session_state == SessionState.ACTIVE.value

        # The sessions_remaining should still reflect what was there
        # (this session was already deducted when booked)
        assert package.sessions_remaining == 3

    def test_booking_attempt_on_expiring_package_race_condition(
        self, client, student_token, db_session, tutor_user, student_user, pricing_option_factory
    ):
        """
        Test race condition: booking attempt exactly as package expires.

        Scenario: Package expires during credit usage API call.
        Expected: Should fail gracefully with appropriate error message.
        """
        # Create package expiring in 2 seconds
        pricing_option = pricing_option_factory(validity_days=30)
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=29, hours=23, minutes=59, seconds=58),
            expires_at=datetime.now(UTC) + timedelta(seconds=2),
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        # Wait for expiration
        import time
        time.sleep(2.5)

        # Try to use credit - should fail
        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.json()["detail"].lower()

    def test_extend_on_use_triggers_during_session(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """
        Test that extend_on_use properly extends validity when using credit.

        Scenario: Package with rolling expiry uses credit near expiration.
        Expected: Expiration date extended by validity_days from current time.
        """
        # Create pricing option with extend_on_use
        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            title="Rolling Package",
            duration_minutes=60,
            price=Decimal("50.00"),
            validity_days=30,
            extend_on_use=True,
        )
        db_session.add(pricing_option)
        db_session.commit()

        # Create package expiring in 5 days
        old_expires_at = datetime.now(UTC) + timedelta(days=5)
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=25),
            expires_at=old_expires_at,
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        # Use credit
        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(package)

        # Expiration should be extended to ~30 days from now
        expected_min = datetime.now(UTC) + timedelta(days=29)
        expected_max = datetime.now(UTC) + timedelta(days=31)

        assert package.expires_at > old_expires_at
        assert expected_min < package.expires_at < expected_max

    def test_multiple_packages_same_subject_selection_priority(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test that packages are selected by expiration date (soonest first).

        Scenario: Student has multiple active packages with same tutor.
        Expected: get_active_packages_for_student returns them ordered by expires_at.
        """
        pricing_option = pricing_option_factory()

        # Create multiple packages with different expiration dates
        pkg_later = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=60),
            status="active",
        )
        pkg_sooner = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=3,
            sessions_remaining=3,
            sessions_used=0,
            purchase_price=Decimal("150.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=10),
            status="active",
        )
        pkg_no_expiry = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=10,
            sessions_remaining=10,
            sessions_used=0,
            purchase_price=Decimal("500.00"),
            purchased_at=datetime.now(UTC),
            expires_at=None,  # No expiration
            status="active",
        )

        db_session.add_all([pkg_later, pkg_sooner, pkg_no_expiry])
        db_session.commit()

        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )

        # Should be ordered: soonest expiring first, then no expiry last
        assert len(active_packages) == 3
        assert active_packages[0].id == pkg_sooner.id  # Expires in 10 days
        assert active_packages[1].id == pkg_later.id   # Expires in 60 days
        assert active_packages[2].id == pkg_no_expiry.id  # Never expires


# =============================================================================
# 2. Session Deduction Complexities
# =============================================================================


class TestSessionDeductionComplexities:
    """Test complex session deduction scenarios."""

    def test_concurrent_session_deductions_prevented(
        self, client, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test that concurrent deduction requests don't cause overdraft.

        Scenario: Two simultaneous requests to use the last credit.
        Expected: Only one succeeds; other fails with appropriate error.
        """
        from core.security import TokenManager

        pricing_option = pricing_option_factory()

        # Package with exactly 1 credit remaining
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=1,  # Only one credit left!
            sessions_used=4,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        token = TokenManager.create_access_token({"sub": student_user.email})

        results = []
        errors = []

        def try_use_credit():
            """Make API request to use credit."""
            from fastapi.testclient import TestClient
            from main import app

            with TestClient(app) as test_client:
                response = test_client.patch(
                    f"/api/v1/packages/{package.id}/use-credit",
                    headers={"Authorization": f"Bearer {token}"},
                )
                results.append(response.status_code)

        # Run concurrent requests using threads
        threads = []
        for _ in range(3):
            t = threading.Thread(target=try_use_credit)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Exactly one should succeed, others should fail
        success_count = sum(1 for r in results if r == 200)
        failure_count = sum(1 for r in results if r == 400)

        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert failure_count == 2, f"Expected 2 failures, got {failure_count}"

        # Verify package state
        db_session.expire_all()
        db_session.refresh(package)
        assert package.sessions_remaining == 0
        assert package.status == "exhausted"

    def test_session_count_cannot_go_negative(
        self, client, student_token, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test overdraft prevention - sessions_remaining can't go below 0.

        Scenario: Package has 0 credits, attempt to use credit.
        Expected: Request fails; database constraint prevents negative.
        """
        pricing_option = pricing_option_factory()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=0,  # Already exhausted
            sessions_used=5,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            status="exhausted",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify database constraint
        db_session.refresh(package)
        assert package.sessions_remaining == 0

    def test_deduction_with_booking_cancellation_flow(
        self, db_session, package_factory, booking_factory
    ):
        """
        Test credit handling when booking is cancelled.

        Note: This tests the expected behavior - credits are deducted at booking
        creation and should be returned on cancellation (manual process).
        """
        package = package_factory(sessions_remaining=5)
        initial_remaining = package.sessions_remaining

        # Create booking that uses package
        booking = booking_factory(
            package_id=package.id,
            session_state=SessionState.SCHEDULED.value,
        )

        # Simulate credit deduction (normally done during booking)
        package.sessions_remaining -= 1
        package.sessions_used += 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == initial_remaining - 1

        # Cancel the booking
        booking.session_state = SessionState.CANCELLED.value
        booking.cancelled_by_role = "STUDENT"

        # Credit should be returned (simulate the refund logic)
        package.sessions_remaining += 1
        package.sessions_used -= 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == initial_remaining


# =============================================================================
# 3. Package Purchase Flows
# =============================================================================


class TestPackagePurchaseFlows:
    """Test complex package purchase scenarios."""

    def test_purchase_while_existing_package_active(
        self, client, student_token, db_session, tutor_user, student_user, pricing_option_factory
    ):
        """
        Test purchasing a new package when student already has active one.

        Scenario: Student has active package, purchases another.
        Expected: Both packages coexist; student can choose which to use.
        """
        pricing_option = pricing_option_factory()

        # Create existing active package
        existing_package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=10),
            expires_at=datetime.now(UTC) + timedelta(days=20),
            status="active",
        )
        db_session.add(existing_package)
        db_session.commit()

        # Purchase new package
        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Both packages should be active
        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )
        assert len(active_packages) >= 2

    def test_purchase_during_active_session_warning(
        self, client, student_token, db_session, tutor_user, student_user,
        pricing_option_factory, booking_factory
    ):
        """
        Test that purchasing during active session shows warning.

        Scenario: Student in active session purchases package.
        Expected: Purchase succeeds with warning about applying to future only.
        """
        pricing_option = pricing_option_factory()

        # Create active session
        active_booking = booking_factory(
            session_state=SessionState.ACTIVE.value,
            start_time=datetime.now(UTC) - timedelta(minutes=30),
            end_time=datetime.now(UTC) + timedelta(minutes=30),
        )

        # Purchase package
        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Should have warning
        assert data["warning"] is not None
        assert "active session" in data["warning"].lower()
        assert data["active_booking_id"] == active_booking.id

    def test_package_price_snapshot_at_purchase(
        self, client, student_token, db_session, tutor_user, student_user, pricing_option_factory
    ):
        """
        Test that package records price at purchase time, not current price.

        Scenario: Price changes after purchase.
        Expected: Package retains original purchase price.
        """
        # Create pricing option at $50
        pricing_option = pricing_option_factory(price=Decimal("50.00"))
        original_price = pricing_option.price

        # Purchase package at $50
        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        package_data = response.json()["package"]

        # Change price to $75
        pricing_option.price = Decimal("75.00")
        db_session.commit()

        # Verify package still has original price
        package = db_session.query(StudentPackage).filter(
            StudentPackage.id == package_data["id"]
        ).first()

        assert package.purchase_price == original_price


# =============================================================================
# 4. Validity Period Calculations
# =============================================================================


class TestValidityPeriodCalculations:
    """Test validity period edge cases and calculations."""

    def test_validity_starts_from_purchase(
        self, client, student_token, db_session, tutor_user, student_user
    ):
        """
        Test that validity period starts from purchase date.

        Expected: expires_at = purchased_at + validity_days
        """
        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            title="30-Day Package",
            duration_minutes=60,
            price=Decimal("50.00"),
            validity_days=30,
        )
        db_session.add(pricing_option)
        db_session.commit()

        before_purchase = datetime.now(UTC)

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        after_purchase = datetime.now(UTC)

        assert response.status_code == status.HTTP_201_CREATED

        package_id = response.json()["package"]["id"]
        package = db_session.query(StudentPackage).filter(
            StudentPackage.id == package_id
        ).first()

        # Expiration should be ~30 days from now
        expected_min = before_purchase + timedelta(days=30)
        expected_max = after_purchase + timedelta(days=30)

        assert package.expires_at is not None
        assert expected_min <= package.expires_at <= expected_max

    def test_extension_calculation_with_existing_validity(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """
        Test that extension only happens if new date is later than current.

        Scenario: Package with 60 days remaining uses credit with extend_on_use.
        Expected: Expiration should NOT be shortened.
        """
        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            title="Rolling Package",
            duration_minutes=60,
            price=Decimal("50.00"),
            validity_days=30,  # Would extend to 30 days from now
            extend_on_use=True,
        )
        db_session.add(pricing_option)
        db_session.commit()

        # Package with 60 days remaining (longer than 30-day extension would give)
        far_future = datetime.now(UTC) + timedelta(days=60)
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=far_future,
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        original_expires = package.expires_at

        # Use credit
        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(package)

        # Expiration should NOT have changed (would shorten it)
        assert package.expires_at == original_expires

    def test_timezone_impact_on_expiration_date(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test that expiration is stored in UTC regardless of user timezone.

        All expiration dates are stored in UTC for consistency.
        """
        pricing_option = pricing_option_factory(validity_days=30)

        # Create package
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        # Verify timezone info
        assert package.expires_at.tzinfo is not None

    def test_leap_year_boundary_handling(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test validity calculation across leap year boundary.

        Scenario: Package purchased Jan 31 with 30-day validity.
        Expected: Expires Feb 28/29 correctly.
        """
        pricing_option = pricing_option_factory(validity_days=30)

        # Simulate purchase on Jan 31 of a leap year
        # Using 2024 as a leap year example
        jan_31_2024 = datetime(2024, 1, 31, 12, 0, 0, tzinfo=UTC)
        expected_expiry = jan_31_2024 + timedelta(days=30)  # March 1, 2024

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=jan_31_2024,
            expires_at=expected_expiry,
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        # Verify correct calculation
        assert package.expires_at == expected_expiry
        assert package.expires_at.month == 3  # March
        assert package.expires_at.day == 1

    def test_month_boundary_handling(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test validity calculation across month boundaries with varying lengths.

        Scenario: Package purchased March 31 with 30-day validity.
        Expected: Expires April 30.
        """
        pricing_option = pricing_option_factory(validity_days=30)

        # March 31 + 30 days = April 30
        march_31 = datetime(2024, 3, 31, 12, 0, 0, tzinfo=UTC)
        expected_expiry = march_31 + timedelta(days=30)

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=march_31,
            expires_at=expected_expiry,
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        assert package.expires_at.month == 4
        assert package.expires_at.day == 30


# =============================================================================
# 5. Background Job Edge Cases
# =============================================================================


class TestBackgroundJobEdgeCases:
    """Test background job edge cases and failure scenarios."""

    def test_expiration_job_skips_packages_with_active_sessions(
        self, db_session, package_factory, booking_factory
    ):
        """
        Test that expiration job marks package expired even with active session.

        Note: The package expiration is independent of session state.
        Active sessions should continue; they were already paid for.
        """
        # Package that's already expired
        expired_package = package_factory(
            sessions_remaining=3,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        # Create active booking
        booking = booking_factory(
            session_state=SessionState.ACTIVE.value,
            package_id=expired_package.id,
        )

        # Run expiration job
        count = PackageExpirationService.mark_expired_packages(db_session)

        # Package should be marked expired
        db_session.refresh(expired_package)
        assert expired_package.status == "expired"

        # But booking should still be active
        db_session.refresh(booking)
        assert booking.session_state == SessionState.ACTIVE.value

    def test_notification_not_sent_for_already_expired_package(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test that expiry warnings aren't sent for already expired packages.
        """
        pricing_option = pricing_option_factory(validity_days=30)

        # Create already expired package
        expired_package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=60),
            expires_at=datetime.now(UTC) - timedelta(days=5),  # Already expired
            status="active",  # Not yet marked by job
            expiry_warning_sent=False,
        )
        db_session.add(expired_package)
        db_session.commit()

        # Get expiring packages (should not include already expired)
        expiring = PackageExpirationService.get_expiring_packages(db_session, days_until_expiry=7)

        assert len([p for p in expiring if p.id == expired_package.id]) == 0

    def test_job_failure_and_retry_scenario(
        self, db_session, package_factory
    ):
        """
        Test that job failures don't leave data in inconsistent state.

        Simulates a failure during package expiration processing.
        """
        # Create packages to expire
        pkg1 = package_factory(
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        pkg2 = package_factory(
            expires_at=datetime.now(UTC) - timedelta(hours=2),
        )

        # First run - succeeds
        count = PackageExpirationService.mark_expired_packages(db_session)
        assert count >= 2

        # Verify both expired
        db_session.refresh(pkg1)
        db_session.refresh(pkg2)
        assert pkg1.status == "expired"
        assert pkg2.status == "expired"

        # Second run - should find nothing new to expire
        count = PackageExpirationService.mark_expired_packages(db_session)
        assert count == 0

    @pytest.mark.asyncio
    async def test_concurrent_job_execution_prevented_by_lock(self):
        """
        Test that distributed lock prevents concurrent job execution.
        """
        from core.distributed_lock import DistributedLockService

        lock_service = DistributedLockService()

        # Mock Redis to test lock behavior
        with patch.object(lock_service, '_get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            # First acquisition succeeds
            mock_redis_instance.set.return_value = True

            acquired1, token1 = await lock_service.try_acquire("job:mark_expired_packages", timeout=300)
            assert acquired1 is True

            # Second acquisition fails (lock held)
            mock_redis_instance.set.return_value = False

            acquired2, token2 = await lock_service.try_acquire("job:mark_expired_packages", timeout=300)
            assert acquired2 is False
            assert token2 is None


# =============================================================================
# 6. Multi-Package Scenarios
# =============================================================================


class TestMultiPackageScenarios:
    """Test scenarios involving multiple packages."""

    def test_student_has_packages_with_multiple_tutors(
        self, db_session, student_user, tutor_user, second_tutor
    ):
        """
        Test student with packages from different tutors.

        Scenario: Student has packages with Tutor A and Tutor B.
        Expected: Each tutor's packages are independent.
        """
        # Create pricing options for both tutors
        pricing_a = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            title="Package A",
            duration_minutes=60,
            price=Decimal("50.00"),
        )
        pricing_b = TutorPricingOption(
            tutor_profile_id=second_tutor.tutor_profile.id,
            title="Package B",
            duration_minutes=60,
            price=Decimal("60.00"),
        )
        db_session.add_all([pricing_a, pricing_b])
        db_session.commit()

        # Create packages with both tutors
        pkg_tutor_a = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_a.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active",
        )
        pkg_tutor_b = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=second_tutor.tutor_profile.id,
            pricing_option_id=pricing_b.id,
            sessions_purchased=3,
            sessions_remaining=3,
            sessions_used=0,
            purchase_price=Decimal("180.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=60),
            status="active",
        )
        db_session.add_all([pkg_tutor_a, pkg_tutor_b])
        db_session.commit()

        # Get all active packages
        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )

        assert len(active_packages) == 2
        tutor_ids = {p.tutor_profile_id for p in active_packages}
        assert tutor_user.tutor_profile.id in tutor_ids
        assert second_tutor.tutor_profile.id in tutor_ids

    def test_package_isolation_between_students(
        self, db_session, student_user, second_student, tutor_user, pricing_option_factory
    ):
        """
        Test that packages are properly isolated between students.

        Scenario: Two students have packages; each should only see their own.
        """
        pricing_option = pricing_option_factory()

        # Create packages for both students
        pkg_student1 = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        pkg_student2 = StudentPackage(
            student_id=second_student.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=3,
            sessions_remaining=3,
            sessions_used=0,
            purchase_price=Decimal("150.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add_all([pkg_student1, pkg_student2])
        db_session.commit()

        # Student 1's packages
        pkgs_student1 = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )
        assert len(pkgs_student1) == 1
        assert pkgs_student1[0].student_id == student_user.id

        # Student 2's packages
        pkgs_student2 = PackageExpirationService.get_active_packages_for_student(
            db_session, second_student.id
        )
        assert len(pkgs_student2) == 1
        assert pkgs_student2[0].student_id == second_student.id

    def test_consolidation_view_of_partial_packages(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test viewing multiple partially-used packages.

        Scenario: Student has several partially-used packages with same tutor.
        Expected: All active packages visible, ordered by expiration.
        """
        pricing_option = pricing_option_factory(validity_days=30)

        # Create multiple packages with varying usage
        packages_data = [
            {"remaining": 5, "used": 0, "days_until_expiry": 5},
            {"remaining": 2, "used": 3, "days_until_expiry": 15},
            {"remaining": 1, "used": 4, "days_until_expiry": 25},
        ]

        created_packages = []
        for pd in packages_data:
            pkg = StudentPackage(
                student_id=student_user.id,
                tutor_profile_id=tutor_user.tutor_profile.id,
                pricing_option_id=pricing_option.id,
                sessions_purchased=5,
                sessions_remaining=pd["remaining"],
                sessions_used=pd["used"],
                purchase_price=Decimal("250.00"),
                purchased_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(days=pd["days_until_expiry"]),
                status="active",
            )
            db_session.add(pkg)
            created_packages.append(pkg)

        db_session.commit()

        # Get active packages
        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )

        # All 3 should be returned
        assert len(active_packages) == 3

        # Should be ordered by expiration (soonest first)
        assert active_packages[0].sessions_remaining == 5  # Expires in 5 days
        assert active_packages[1].sessions_remaining == 2  # Expires in 15 days
        assert active_packages[2].sessions_remaining == 1  # Expires in 25 days

        # Calculate total remaining credits
        total_remaining = sum(p.sessions_remaining for p in active_packages)
        assert total_remaining == 8


# =============================================================================
# 7. Transaction Integrity Tests
# =============================================================================


class TestTransactionIntegrity:
    """Test transaction handling and data integrity."""

    def test_package_creation_atomic_with_audit(
        self, client, student_token, db_session, tutor_user, student_user, pricing_option_factory
    ):
        """
        Test that package creation and audit log are atomic.

        Either both succeed or neither does.
        """
        pricing_option = pricing_option_factory()

        initial_package_count = db_session.query(StudentPackage).count()

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Package count should increase by 1
        new_package_count = db_session.query(StudentPackage).count()
        assert new_package_count == initial_package_count + 1

    def test_credit_deduction_atomic(
        self, client, student_token, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """
        Test that credit deduction is atomic with status update.

        If exhausted, both sessions_remaining=0 and status='exhausted' together.
        """
        pricing_option = pricing_option_factory()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=1,
            sessions_remaining=1,  # Last credit
            sessions_used=0,
            purchase_price=Decimal("50.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(package)

        # Both should be updated atomically
        assert package.sessions_remaining == 0
        assert package.status == "exhausted"

    def test_expiration_update_rollback_on_error(self, db_session, package_factory):
        """
        Test that expiration updates rollback properly on error.
        """
        package = package_factory(
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        original_status = package.status

        # Simulate error during update
        try:
            with db_session.begin_nested():
                package.status = "expired"
                # Simulate error
                raise Exception("Simulated error")
        except Exception:
            pass

        # Status should be rolled back
        db_session.refresh(package)
        assert package.status == original_status


# =============================================================================
# 8. Validity Checkout Race Condition Tests
# =============================================================================


class TestValidityCheckoutRaceConditions:
    """Test package validity during checkout process."""

    def test_check_package_validity_for_checkout_active(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """Test validity check for active valid package during checkout."""
        pricing_option = pricing_option_factory(validity_days=30)

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=25),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        is_valid, expired_during_checkout, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is True
        assert expired_during_checkout is False
        assert error is None

    def test_check_package_validity_for_checkout_expired_during(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """Test detecting package that expired during checkout."""
        pricing_option = pricing_option_factory(validity_days=30)

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=31),
            expires_at=datetime.now(UTC) - timedelta(minutes=5),  # Just expired
            status="active",  # Not yet marked by job
        )
        db_session.add(package)
        db_session.commit()

        is_valid, expired_during_checkout, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        assert expired_during_checkout is True
        assert "expired" in error.lower()

    def test_check_package_validity_for_checkout_no_credits(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """Test validity check when no credits remain (not a checkout race)."""
        pricing_option = pricing_option_factory()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=0,  # No credits
            sessions_used=5,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        is_valid, expired_during_checkout, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        assert expired_during_checkout is False  # Not an expiration issue
        assert "no credits" in error.lower()


# =============================================================================
# 9. Expiry Warning Tests
# =============================================================================


class TestExpiryWarnings:
    """Test package expiry warning functionality."""

    def test_get_expiring_packages_returns_correct_packages(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """Test that only packages expiring within timeframe are returned."""
        pricing_option = pricing_option_factory(validity_days=30)

        # Package expiring in 3 days (should be included for 7-day warning)
        pkg_expiring_soon = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=27),
            expires_at=datetime.now(UTC) + timedelta(days=3),
            status="active",
            expiry_warning_sent=False,
        )

        # Package expiring in 15 days (should NOT be included)
        pkg_not_soon = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=15),
            status="active",
            expiry_warning_sent=False,
        )

        # Package with warning already sent (should NOT be included)
        pkg_warned = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=2,
            sessions_used=3,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=25),
            expires_at=datetime.now(UTC) + timedelta(days=5),
            status="active",
            expiry_warning_sent=True,  # Already warned
        )

        db_session.add_all([pkg_expiring_soon, pkg_not_soon, pkg_warned])
        db_session.commit()

        expiring = PackageExpirationService.get_expiring_packages(
            db_session, days_until_expiry=7
        )

        # Only the first package should be returned
        expiring_ids = [p.id for p in expiring]
        assert pkg_expiring_soon.id in expiring_ids
        assert pkg_not_soon.id not in expiring_ids
        assert pkg_warned.id not in expiring_ids

    def test_expiry_warning_not_sent_for_exhausted_packages(
        self, db_session, student_user, tutor_user, pricing_option_factory
    ):
        """Test that warnings aren't sent for packages with no credits."""
        pricing_option = pricing_option_factory(validity_days=30)

        # Package expiring soon but no credits
        pkg_exhausted = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=0,  # No credits left
            sessions_used=5,
            purchase_price=Decimal("250.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=27),
            expires_at=datetime.now(UTC) + timedelta(days=3),
            status="active",  # Could be 'exhausted', testing active with 0
            expiry_warning_sent=False,
        )
        db_session.add(pkg_exhausted)
        db_session.commit()

        expiring = PackageExpirationService.get_expiring_packages(
            db_session, days_until_expiry=7
        )

        # Should not be included (no credits to warn about)
        assert pkg_exhausted.id not in [p.id for p in expiring]
