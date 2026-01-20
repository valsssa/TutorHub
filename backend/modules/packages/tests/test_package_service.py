"""
Package Service Tests

Tests for session package purchase, credit usage, and expiration management.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from backend.models.students import StudentPackage
from backend.models.tutors import TutorPricingOption


@pytest.fixture
def pricing_option_5_sessions(db: Session, test_tutor_profile):
    """Pricing option: 5 sessions for $225"""
    option = TutorPricingOption(
        tutor_profile_id=test_tutor_profile.id,
        name="5 Session Package",
        session_count=5,
        price=Decimal("225.00"),
        description="Save $25 with package deal"
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


@pytest.fixture
def pricing_option_10_sessions(db: Session, test_tutor_profile):
    """Pricing option: 10 sessions for $400"""
    option = TutorPricingOption(
        tutor_profile_id=test_tutor_profile.id,
        name="10 Session Package",
        session_count=10,
        price=Decimal("400.00"),
        description="Best value - save $100"
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


class TestPackagePurchase:
    """Test purchasing session packages"""

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_purchase_package_success(
        self,
        db: Session,
        test_student,
        test_tutor_profile,
        pricing_option_5_sessions
    ):
        """Test successful package purchase"""
        # Given
        student_id = test_student.id
        pricing_option_id = pricing_option_5_sessions.id

        # When
        # package = PackageService.purchase_package(
        #     db,
        #     student_id=student_id,
        #     pricing_option_id=pricing_option_id
        # )

        # Then
        # assert package.student_id == student_id
        # assert package.tutor_profile_id == test_tutor_profile.id
        # assert package.sessions_purchased == 5
        # assert package.sessions_remaining == 5
        # assert package.sessions_used == 0
        # assert package.purchase_price == Decimal("225.00")
        # assert package.status == "active"
        # assert package.purchased_at is not None
        pass

    def test_package_discount_calculation(self, pricing_option_5_sessions, test_tutor_profile):
        """Test that package offers discount vs individual sessions"""
        # Given
        hourly_rate = test_tutor_profile.hourly_rate  # e.g., $50
        sessions = pricing_option_5_sessions.session_count  # 5
        package_price = pricing_option_5_sessions.price  # $225

        # When
        individual_total = hourly_rate * sessions  # $250
        discount = individual_total - package_price  # $25

        # Then
        assert discount > 0
        assert package_price < individual_total
        discount_percentage = (discount / individual_total) * 100
        assert discount_percentage == 10  # 10% discount

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_purchase_multiple_packages(
        self,
        db: Session,
        test_student,
        pricing_option_5_sessions,
        pricing_option_10_sessions
    ):
        """Test student can purchase multiple packages"""
        # When - purchase both packages
        # package1 = PackageService.purchase_package(db, test_student.id, pricing_option_5_sessions.id)
        # package2 = PackageService.purchase_package(db, test_student.id, pricing_option_10_sessions.id)

        # Then
        # assert package1.id != package2.id
        # student_packages = db.query(StudentPackage).filter_by(student_id=test_student.id).all()
        # assert len(student_packages) == 2
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_purchase_package_nonexistent_pricing_option(self, db: Session, test_student):
        """Test error when pricing option doesn't exist"""
        # When/Then
        # with pytest.raises(ValueError, match="Pricing option not found"):
        #     PackageService.purchase_package(db, test_student.id, 99999)
        pass


class TestPackageCreditUsage:
    """Test consuming session credits from packages"""

    @pytest.fixture
    def student_package_with_credits(self, db: Session, test_student, pricing_option_5_sessions):
        """Active package with 5 remaining credits"""
        package = StudentPackage(
            student_id=test_student.id,
            tutor_profile_id=pricing_option_5_sessions.tutor_profile_id,
            pricing_option_id=pricing_option_5_sessions.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=pricing_option_5_sessions.price,
            purchased_at=datetime.now(timezone.utc),
            status="active"
        )
        db.add(package)
        db.commit()
        db.refresh(package)
        return package

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_use_package_credit(
        self,
        db: Session,
        student_package_with_credits,
        test_booking
    ):
        """Test consuming one session credit"""
        # Given
        initial_remaining = student_package_with_credits.sessions_remaining
        package_id = student_package_with_credits.id
        booking_id = test_booking.id

        # When
        # updated = PackageService.use_credit(db, package_id, booking_id)

        # Then
        # assert updated.sessions_remaining == initial_remaining - 1
        # assert updated.sessions_used == 1
        # Booking should be linked to package
        # db.refresh(test_booking)
        # assert test_booking.package_id == package_id
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_use_multiple_credits(self, db: Session, student_package_with_credits):
        """Test consuming multiple credits over time"""
        # Given
        package_id = student_package_with_credits.id

        # When - use 3 credits
        # for i in range(3):
        #     booking = create_test_booking(db, i)
        #     PackageService.use_credit(db, package_id, booking.id)

        # Then
        # db.refresh(student_package_with_credits)
        # assert student_package_with_credits.sessions_remaining == 2
        # assert student_package_with_credits.sessions_used == 3
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_use_credit_insufficient_sessions(self, db: Session, student_package_with_credits):
        """Test error when package has no remaining sessions"""
        # Given - deplete all credits
        student_package_with_credits.sessions_remaining = 0
        student_package_with_credits.sessions_used = 5
        db.commit()

        # When/Then
        # with pytest.raises(ValueError, match="No sessions remaining"):
        #     PackageService.use_credit(db, student_package_with_credits.id, 999)
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_use_credit_expired_package(self, db: Session, student_package_with_credits):
        """Test error when trying to use credit from expired package"""
        # Given - package expired
        student_package_with_credits.status = "expired"
        student_package_with_credits.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

        # When/Then
        # with pytest.raises(ValueError, match="Package expired"):
        #     PackageService.use_credit(db, student_package_with_credits.id, 999)
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_package_completed_when_all_credits_used(
        self,
        db: Session,
        student_package_with_credits
    ):
        """Test package marked as completed when all sessions used"""
        # Given
        package_id = student_package_with_credits.id

        # When - use all 5 credits
        # for i in range(5):
        #     booking = create_test_booking(db, i)
        #     PackageService.use_credit(db, package_id, booking.id)

        # Then
        # db.refresh(student_package_with_credits)
        # assert student_package_with_credits.sessions_remaining == 0
        # assert student_package_with_credits.status == "completed"
        pass


class TestPackageExpiration:
    """Test package expiration logic"""

    @pytest.fixture
    def expired_package(self, db: Session, test_student, pricing_option_5_sessions):
        """Package purchased 13 months ago (expired)"""
        package = StudentPackage(
            student_id=test_student.id,
            tutor_profile_id=pricing_option_5_sessions.tutor_profile_id,
            pricing_option_id=pricing_option_5_sessions.id,
            sessions_purchased=5,
            sessions_remaining=3,  # Still has unused credits
            sessions_used=2,
            purchase_price=pricing_option_5_sessions.price,
            purchased_at=datetime.now(timezone.utc) - timedelta(days=400),
            expires_at=datetime.now(timezone.utc) - timedelta(days=35),  # Expired 35 days ago
            status="active"  # Should be expired
        )
        db.add(package)
        db.commit()
        db.refresh(package)
        return package

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_package_expiration_12_months(self, db: Session, student_package_with_credits):
        """Test package expires after 12 months"""
        # Given - package purchased 13 months ago
        student_package_with_credits.purchased_at = datetime.now(timezone.utc) - timedelta(days=395)
        student_package_with_credits.expires_at = datetime.now(timezone.utc) - timedelta(days=5)
        db.commit()

        # When - run expiration check job
        # PackageService.check_expirations(db)

        # Then
        # db.refresh(student_package_with_credits)
        # assert student_package_with_credits.status == "expired"
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_expiration_notification_sent(self, db: Session, expired_package):
        """Test that notification is sent when package expires"""
        # When - run expiration check
        # PackageService.check_expirations(db)

        # Then - notification should be created
        # notification = db.query(Notification).filter(
        #     Notification.user_id == expired_package.student_id,
        #     Notification.type == "package_expired"
        # ).first()
        # assert notification is not None
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_list_active_packages_excludes_expired(self, db: Session, test_student, expired_package):
        """Test that listing active packages excludes expired ones"""
        # When
        # active_packages = PackageService.list_student_packages(
        #     db,
        #     test_student.id,
        #     status="active"
        # )

        # Then
        # assert len(active_packages) == 0  # Expired package not included
        pass


class TestPackageListing:
    """Test retrieving student packages"""

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_list_student_packages(
        self,
        db: Session,
        test_student,
        student_package_with_credits
    ):
        """Test retrieving all packages for a student"""
        # When
        # packages = PackageService.list_student_packages(db, test_student.id)

        # Then
        # assert len(packages) >= 1
        # assert any(p.id == student_package_with_credits.id for p in packages)
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_list_packages_by_status(
        self,
        db: Session,
        test_student,
        student_package_with_credits
    ):
        """Test filtering packages by status"""
        # When
        # active_packages = PackageService.list_student_packages(
        #     db,
        #     test_student.id,
        #     status="active"
        # )

        # Then
        # assert all(p.status == "active" for p in active_packages)
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_list_packages_by_tutor(
        self,
        db: Session,
        test_student,
        test_tutor_profile,
        student_package_with_credits
    ):
        """Test filtering packages by tutor"""
        # When
        # tutor_packages = PackageService.list_student_packages(
        #     db,
        #     test_student.id,
        #     tutor_profile_id=test_tutor_profile.id
        # )

        # Then
        # assert all(p.tutor_profile_id == test_tutor_profile.id for p in tutor_packages)
        pass


class TestPackagePricing:
    """Test pricing option management"""

    def test_create_pricing_option(self, db: Session, test_tutor_profile):
        """Test tutor creating pricing option"""
        # Given
        option_data = {
            "name": "3 Session Starter",
            "session_count": 3,
            "price": Decimal("135.00"),
            "description": "Try 3 sessions"
        }

        # When
        option = TutorPricingOption(
            tutor_profile_id=test_tutor_profile.id,
            **option_data
        )
        db.add(option)
        db.commit()
        db.refresh(option)

        # Then
        assert option.name == "3 Session Starter"
        assert option.session_count == 3
        assert option.price == Decimal("135.00")

    def test_tutor_multiple_pricing_options(
        self,
        db: Session,
        test_tutor_profile,
        pricing_option_5_sessions,
        pricing_option_10_sessions
    ):
        """Test tutor can offer multiple packages"""
        # Then
        assert len(test_tutor_profile.pricing_options) >= 2

    def test_pricing_option_validation_min_sessions(self, db: Session, test_tutor_profile):
        """Test minimum session count validation"""
        # When/Then - try to create package with 0 sessions
        with pytest.raises(ValueError):
            option = TutorPricingOption(
                tutor_profile_id=test_tutor_profile.id,
                name="Invalid",
                session_count=0,
                price=Decimal("100.00")
            )
            db.add(option)
            db.commit()

    def test_pricing_option_validation_price(self, db: Session, test_tutor_profile):
        """Test price must be positive"""
        # When/Then - try negative price
        with pytest.raises(ValueError):
            option = TutorPricingOption(
                tutor_profile_id=test_tutor_profile.id,
                name="Invalid",
                session_count=5,
                price=Decimal("-50.00")
            )
            db.add(option)
            db.commit()


class TestPackageRefund:
    """Test package refund scenarios"""

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_refund_unused_package(self, db: Session, student_package_with_credits):
        """Test refunding package with unused credits"""
        # Given - package with 5 unused sessions
        package_id = student_package_with_credits.id

        # When
        # refund = PackageService.refund_package(db, package_id, reason="Student request")

        # Then
        # assert refund.amount == student_package_with_credits.purchase_price
        # db.refresh(student_package_with_credits)
        # assert student_package_with_credits.status == "refunded"
        pass

    @pytest.mark.skip(reason="Requires PackageService implementation")
    def test_partial_refund_partially_used_package(
        self,
        db: Session,
        student_package_with_credits
    ):
        """Test partial refund for partially used package"""
        # Given - use 2 out of 5 sessions
        student_package_with_credits.sessions_used = 2
        student_package_with_credits.sessions_remaining = 3
        db.commit()

        # When
        # refund = PackageService.refund_package(db, student_package_with_credits.id)

        # Then - refund 3/5 of purchase price
        # expected_refund = (Decimal("3") / Decimal("5")) * student_package_with_credits.purchase_price
        # assert refund.amount == expected_refund
        pass


# Additional test scenarios to implement:
# - Package transfer between tutors (if tutor leaves)
# - Package upgrade (5→10 sessions, pay difference)
# - Auto-renewal of packages
# - Gift packages (one student buys for another)
# - Promotional packages with time-limited discounts
# - Package analytics (most popular packages, conversion rate)
# - Package recommendations based on past bookings
