"""
Comprehensive tests for package purchase and usage functionality.

Tests cover:
- Package purchase
- Credit usage
- Package expiration
- Session counting
- Package listing
- Edge cases and error handling
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import status


class TestPackagePurchase:
    """Test package purchase functionality."""

    def _create_pricing_option(self, db_session, tutor_profile, price=50.00, validity_days=None):
        """Helper to create a pricing option."""
        from models import TutorPricingOption

        option = TutorPricingOption(
            tutor_profile_id=tutor_profile.id,
            name="Test Package",
            session_count=1,
            price=Decimal(str(price)),
            description="Test package description",
            validity_days=validity_days,
        )
        db_session.add(option)
        db_session.commit()
        db_session.refresh(option)
        return option

    def test_purchase_package_success(
        self, client, student_token, db_session, tutor_user, student_user
    ):
        """Test successful package purchase."""
        pricing_option = self._create_pricing_option(
            db_session, tutor_user.tutor_profile
        )

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
        # Response wraps package in a 'package' field with optional warning
        package = data["package"]
        assert package["student_id"] == student_user.id
        assert package["tutor_profile_id"] == tutor_user.tutor_profile.id
        assert package["sessions_purchased"] == 1
        assert package["sessions_remaining"] == 1
        assert package["sessions_used"] == 0
        assert package["status"] == "active"
        # No active session, so no warning expected
        assert data["warning"] is None
        assert data["active_booking_id"] is None

    def test_purchase_package_with_validity(
        self, client, student_token, db_session, tutor_user
    ):
        """Test package purchase with validity period sets expiration."""
        pricing_option = self._create_pricing_option(
            db_session, tutor_user.tutor_profile, validity_days=30
        )

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
        assert data["package"]["expires_at"] is not None

    def test_purchase_package_tutor_not_found(self, client, student_token, db_session):
        """Test purchase fails when tutor doesn't exist."""
        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": 99999,
                "pricing_option_id": 1,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "tutor not found" in response.json()["detail"].lower()

    def test_purchase_package_tutor_not_approved(
        self, client, student_token, db_session
    ):
        """Test purchase fails when tutor is not approved."""
        from auth import get_password_hash
        from models import TutorPricingOption, TutorProfile, User

        user = User(
            email="unapproved_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Unapproved Tutor",
            hourly_rate=50.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        pricing_option = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="Test Package",
            session_count=1,
            price=Decimal("50.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not approved" in response.json()["detail"].lower()

    def test_purchase_package_pricing_option_not_found(
        self, client, student_token, db_session, tutor_user
    ):
        """Test purchase fails when pricing option doesn't exist."""
        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": 99999,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "pricing option" in response.json()["detail"].lower()

    def test_purchase_package_pricing_option_wrong_tutor(
        self, client, student_token, db_session, tutor_user
    ):
        """Test purchase fails when pricing option belongs to different tutor."""
        from auth import get_password_hash
        from models import TutorPricingOption, TutorProfile, User

        other_user = User(
            email="other_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        other_profile = TutorProfile(
            user_id=other_user.id,
            title="Other Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(other_profile)
        db_session.commit()

        other_pricing = TutorPricingOption(
            tutor_profile_id=other_profile.id,
            name="Other Package",
            session_count=1,
            price=Decimal("50.00"),
        )
        db_session.add(other_pricing)
        db_session.commit()

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": other_pricing.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "does not belong" in response.json()["detail"].lower()

    def test_purchase_requires_student_role(
        self, client, tutor_token, db_session, tutor_user
    ):
        """Test that only students can purchase packages."""
        pricing_option = self._create_pricing_option(
            db_session, tutor_user.tutor_profile
        )

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_purchase_during_active_session_shows_warning(
        self, client, student_token, db_session, tutor_user, student_user
    ):
        """Test that purchasing during an active session returns a warning."""
        from models import Booking

        pricing_option = self._create_pricing_option(
            db_session, tutor_user.tutor_profile
        )

        # Create an active session for the student
        active_booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            start_time=datetime.now(UTC) - timedelta(minutes=30),
            end_time=datetime.now(UTC) + timedelta(minutes=30),
            session_state="ACTIVE",
            payment_state="AUTHORIZED",
            hourly_rate=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            currency="USD",
        )
        db_session.add(active_booking)
        db_session.commit()
        db_session.refresh(active_booking)

        response = client.post(
            "/api/v1/packages",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "pricing_option_id": pricing_option.id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Purchase should still succeed
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # But should include a warning about active session
        assert data["warning"] is not None
        assert "active session" in data["warning"].lower()
        assert "future bookings" in data["warning"].lower()
        assert data["active_booking_id"] == active_booking.id

        # Package should still be created successfully
        assert data["package"]["status"] == "active"


class TestPackageCreditUsage:
    """Test package credit usage functionality."""

    def _create_active_package(
        self, db_session, student_id, tutor_profile_id, sessions_remaining=5
    ):
        """Helper to create an active package with credits."""
        from models import StudentPackage, TutorPricingOption

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_profile_id,
            name="Test Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_id,
            tutor_profile_id=tutor_profile_id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=sessions_remaining,
            sessions_used=5 - sessions_remaining,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)
        return package

    def test_use_credit_success(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test successfully using a package credit."""
        package = self._create_active_package(
            db_session, student_user.id, tutor_user.tutor_profile.id
        )

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sessions_remaining"] == 4
        assert data["sessions_used"] == 1

    def test_use_credit_updates_count(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test that using credits properly updates counts."""
        package = self._create_active_package(
            db_session, student_user.id, tutor_user.tutor_profile.id
        )

        for _i in range(3):
            response = client.patch(
                f"/api/v1/packages/{package.id}/use-credit",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["sessions_remaining"] == 2
        assert data["sessions_used"] == 3

    def test_use_credit_exhausts_package(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test that using last credit marks package as exhausted."""
        package = self._create_active_package(
            db_session, student_user.id, tutor_user.tutor_profile.id, sessions_remaining=1
        )

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sessions_remaining"] == 0
        assert data["status"] == "exhausted"

    def test_use_credit_no_remaining(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test error when no credits remaining."""
        package = self._create_active_package(
            db_session, student_user.id, tutor_user.tutor_profile.id, sessions_remaining=0
        )
        package.status = "exhausted"
        db_session.commit()

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_use_credit_package_not_found(self, client, student_token):
        """Test error when package doesn't exist."""
        response = client.patch(
            "/api/v1/packages/99999/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_use_credit_wrong_owner(
        self, client, db_session, tutor_user
    ):
        """Test error when user doesn't own the package."""
        from auth import get_password_hash
        from core.security import TokenManager
        from models import StudentPackage, TutorPricingOption, User

        other_student = User(
            email="other_student@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(other_student)
        db_session.commit()

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Test Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=other_student.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        yet_another = User(
            email="yet_another@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(yet_another)
        db_session.commit()

        token = TokenManager.create_access_token({"sub": yet_another.email})

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPackageExpiration:
    """Test package expiration functionality."""

    def _create_package_with_expiration(
        self, db_session, student_id, tutor_profile_id, expires_at
    ):
        """Helper to create a package with specific expiration."""
        from models import StudentPackage, TutorPricingOption

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_profile_id,
            name="Expiring Package",
            session_count=5,
            price=Decimal("225.00"),
            validity_days=30,
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_id,
            tutor_profile_id=tutor_profile_id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=60),
            expires_at=expires_at,
            status="active",
        )
        db_session.add(package)
        db_session.commit()
        db_session.refresh(package)
        return package

    def test_use_credit_expired_package(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test error when trying to use credit from expired package."""
        package = self._create_package_with_expiration(
            db_session,
            student_user.id,
            tutor_user.tutor_profile.id,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        response = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.json()["detail"].lower()

    def test_expiration_service_marks_expired(self, db_session, student_user, tutor_user):
        """Test expiration service marks expired packages."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Expired Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=60),
            expires_at=datetime.now(UTC) - timedelta(days=5),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        count = PackageExpirationService.mark_expired_packages(db_session)

        assert count >= 1
        db_session.refresh(package)
        assert package.status == "expired"

    def test_expiration_service_ignores_non_expired(
        self, db_session, student_user, tutor_user
    ):
        """Test expiration service ignores non-expired packages."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Valid Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        PackageExpirationService.mark_expired_packages(db_session)

        db_session.refresh(package)
        assert package.status == "active"

    def test_check_package_validity_active(self, db_session, student_user, tutor_user):
        """Test validity check for active package."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Valid Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is True
        assert error is None

    def test_check_package_validity_expired(self, db_session, student_user, tutor_user):
        """Test validity check for expired package."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Expired Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=60),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_check_package_validity_no_sessions(self, db_session, student_user, tutor_user):
        """Test validity check for package with no sessions."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Empty Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=0,
            sessions_used=5,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "no credits" in error.lower()


class TestPackageListing:
    """Test package listing functionality."""

    def _create_packages(self, db_session, student_id, tutor_profile_id):
        """Helper to create multiple packages with different statuses."""
        from models import StudentPackage, TutorPricingOption

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_profile_id,
            name="List Test Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        packages = []
        statuses = ["active", "active", "exhausted", "expired"]
        for i, pkg_status in enumerate(statuses):
            package = StudentPackage(
                student_id=student_id,
                tutor_profile_id=tutor_profile_id,
                pricing_option_id=pricing_option.id,
                sessions_purchased=5,
                sessions_remaining=3 if pkg_status == "active" else 0,
                sessions_used=2 if pkg_status == "active" else 5,
                purchase_price=Decimal("225.00"),
                purchased_at=datetime.now(UTC) - timedelta(days=i * 10),
                status=pkg_status,
            )
            db_session.add(package)
            packages.append(package)

        db_session.commit()
        return packages

    def test_list_all_packages(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test listing all packages for a student."""
        self._create_packages(db_session, student_user.id, tutor_user.tutor_profile.id)

        response = client.get(
            "/api/v1/packages",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 4

    def test_list_packages_filter_active(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test listing only active packages."""
        self._create_packages(db_session, student_user.id, tutor_user.tutor_profile.id)

        response = client.get(
            "/api/v1/packages?status_filter=active",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(p["status"] == "active" for p in data)

    def test_list_packages_filter_exhausted(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test listing only exhausted packages."""
        self._create_packages(db_session, student_user.id, tutor_user.tutor_profile.id)

        response = client.get(
            "/api/v1/packages?status_filter=exhausted",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(p["status"] == "exhausted" for p in data)

    def test_list_packages_only_own(
        self, client, db_session, tutor_user
    ):
        """Test that students only see their own packages."""
        from auth import get_password_hash
        from core.security import TokenManager
        from models import StudentPackage, TutorPricingOption, User

        student1 = User(
            email="student1@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        student2 = User(
            email="student2@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add_all([student1, student2])
        db_session.commit()

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Isolation Test",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package1 = StudentPackage(
            student_id=student1.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        package2 = StudentPackage(
            student_id=student2.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add_all([package1, package2])
        db_session.commit()

        token1 = TokenManager.create_access_token({"sub": student1.email})
        response = client.get(
            "/api/v1/packages",
            headers={"Authorization": f"Bearer {token1}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(p["student_id"] == student1.id for p in data)


class TestGetActivePackages:
    """Test getting active packages for booking."""

    def test_get_active_packages_for_student(self, db_session, student_user, tutor_user):
        """Test getting active non-expired packages."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Active Package Test",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        active_pkg = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active",
        )
        expired_pkg = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=60),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            status="active",
        )
        db_session.add_all([active_pkg, expired_pkg])
        db_session.commit()

        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )

        assert len(active_packages) == 1
        assert active_packages[0].id == active_pkg.id

    def test_get_active_packages_ordered_by_expiration(
        self, db_session, student_user, tutor_user
    ):
        """Test active packages are ordered by expiration date."""
        from models import StudentPackage, TutorPricingOption
        from modules.packages.services.expiration_service import PackageExpirationService

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Order Test Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        pkg_later = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=60),
            status="active",
        )
        pkg_sooner = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("225.00"),
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=10),
            status="active",
        )
        db_session.add_all([pkg_later, pkg_sooner])
        db_session.commit()

        active_packages = PackageExpirationService.get_active_packages_for_student(
            db_session, student_user.id
        )

        assert len(active_packages) == 2
        assert active_packages[0].id == pkg_sooner.id


class TestConcurrentCreditUsage:
    """Test handling of concurrent credit usage requests."""

    def test_atomic_credit_deduction(
        self, client, student_token, db_session, student_user, tutor_user
    ):
        """Test that credit deduction is atomic."""
        from models import StudentPackage, TutorPricingOption

        pricing_option = TutorPricingOption(
            tutor_profile_id=tutor_user.tutor_profile.id,
            name="Atomic Test",
            session_count=1,
            price=Decimal("50.00"),
        )
        db_session.add(pricing_option)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            pricing_option_id=pricing_option.id,
            sessions_purchased=1,
            sessions_remaining=1,
            sessions_used=0,
            purchase_price=Decimal("50.00"),
            purchased_at=datetime.now(UTC),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        response1 = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response1.status_code == status.HTTP_200_OK

        response2 = client.patch(
            f"/api/v1/packages/{package.id}/use-credit",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
