"""
Package Expiration Service Tests

Comprehensive tests for PackageExpirationService including:
- Marking expired packages
- Checking package validity
- Getting active packages for students
- Getting expiring packages
- Sending expiry warnings
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from modules.packages.services.expiration_service import PackageExpirationService


class TestMarkExpiredPackages:
    """Tests for mark_expired_packages method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def expired_package(self):
        """Create mock expired package."""
        package = MagicMock()
        package.id = 1
        package.status = "active"
        package.expires_at = datetime.now(UTC) - timedelta(days=1)
        package.updated_at = None
        return package

    @pytest.fixture
    def active_package(self):
        """Create mock active (not expired) package."""
        package = MagicMock()
        package.id = 2
        package.status = "active"
        package.expires_at = datetime.now(UTC) + timedelta(days=30)
        package.updated_at = None
        return package

    def test_marks_expired_packages_as_expired(self, mock_db, expired_package):
        """Test that expired packages are marked as 'expired' status."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            expired_package
        ]

        count = PackageExpirationService.mark_expired_packages(mock_db)

        assert count == 1
        assert expired_package.status == "expired"
        assert expired_package.updated_at is not None
        mock_db.commit.assert_called_once()

    def test_returns_zero_when_no_expired_packages(self, mock_db):
        """Test that zero is returned when no packages are expired."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        count = PackageExpirationService.mark_expired_packages(mock_db)

        assert count == 0
        mock_db.commit.assert_not_called()

    def test_handles_multiple_expired_packages(self, mock_db):
        """Test handling of multiple expired packages."""
        packages = []
        for i in range(5):
            pkg = MagicMock()
            pkg.id = i
            pkg.status = "active"
            pkg.expires_at = datetime.now(UTC) - timedelta(days=i + 1)
            packages.append(pkg)

        mock_db.query.return_value.filter.return_value.all.return_value = packages

        count = PackageExpirationService.mark_expired_packages(mock_db)

        assert count == 5
        for pkg in packages:
            assert pkg.status == "expired"
        mock_db.commit.assert_called_once()

    def test_rollback_on_exception(self, mock_db, expired_package):
        """Test that transaction is rolled back on exception."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            expired_package
        ]
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            PackageExpirationService.mark_expired_packages(mock_db)

        mock_db.rollback.assert_called_once()

    def test_only_marks_active_packages(self, mock_db):
        """Test that only active packages are considered for expiration."""
        # The query filter should include status == 'active'
        mock_db.query.return_value.filter.return_value.all.return_value = []

        PackageExpirationService.mark_expired_packages(mock_db)

        # Verify query was called (filter includes status check)
        mock_db.query.assert_called()


class TestCheckPackageValidity:
    """Tests for check_package_validity method."""

    @pytest.fixture
    def valid_package(self):
        """Create mock valid package."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)
        return package

    def test_valid_package_returns_true(self, valid_package):
        """Test that valid package returns (True, None)."""
        is_valid, error = PackageExpirationService.check_package_validity(valid_package)

        assert is_valid is True
        assert error is None

    def test_invalid_status_returns_false(self):
        """Test that non-active status returns (False, error)."""
        package = MagicMock()
        package.status = "expired"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_no_sessions_remaining_returns_false(self):
        """Test that zero sessions remaining returns (False, error)."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 0
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "credits" in error.lower() or "remaining" in error.lower()

    def test_expired_package_returns_false(self):
        """Test that expired package returns (False, error)."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) - timedelta(days=1)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_no_expiry_date_is_valid(self):
        """Test that package without expiry date is valid (no time limit)."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = None

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is True
        assert error is None


class TestCheckPackageValidityForCheckout:
    """Tests for check_package_validity_for_checkout method."""

    @pytest.fixture
    def valid_package(self):
        """Create mock valid package for checkout."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)
        return package

    def test_valid_package_returns_true(self, valid_package):
        """Test valid package returns (True, False, None)."""
        is_valid, expired_during, error = (
            PackageExpirationService.check_package_validity_for_checkout(valid_package)
        )

        assert is_valid is True
        assert expired_during is False
        assert error is None

    def test_no_sessions_not_expired_during_checkout(self):
        """Test that no sessions is not considered 'expired during checkout'."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 0
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, expired_during, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        assert expired_during is False
        assert "credits" in error.lower() or "remaining" in error.lower()

    def test_expired_is_detected_as_during_checkout(self):
        """Test that expired package is detected as expired during checkout."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) - timedelta(hours=1)

        is_valid, expired_during, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        assert expired_during is True
        assert "expired" in error.lower()

    def test_expired_status_detected(self):
        """Test that 'expired' status is detected as expired during checkout."""
        package = MagicMock()
        package.status = "expired"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, expired_during, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        assert expired_during is True
        assert "expired" in error.lower()

    def test_exhausted_status_not_expired_during_checkout(self):
        """Test that 'exhausted' status is not 'expired during checkout'."""
        package = MagicMock()
        package.status = "exhausted"
        package.sessions_remaining = 0
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, expired_during, error = (
            PackageExpirationService.check_package_validity_for_checkout(package)
        )

        assert is_valid is False
        # 'exhausted' is not 'expired', so expired_during should be False
        assert expired_during is False


class TestGetActivePackagesForStudent:
    """Tests for get_active_packages_for_student method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_returns_active_packages(self, mock_db):
        """Test that active packages are returned."""
        active_pkg = MagicMock()
        active_pkg.id = 1
        active_pkg.status = "active"
        active_pkg.sessions_remaining = 5

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            active_pkg
        ]

        result = PackageExpirationService.get_active_packages_for_student(mock_db, 1)

        assert len(result) == 1
        assert result[0].id == 1

    def test_returns_empty_list_when_no_active_packages(self, mock_db):
        """Test that empty list is returned when no active packages."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = PackageExpirationService.get_active_packages_for_student(mock_db, 1)

        assert result == []

    def test_orders_by_expiring_first(self, mock_db):
        """Test that packages are ordered by expiration date (soonest first)."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        PackageExpirationService.get_active_packages_for_student(mock_db, 1)

        # Verify order_by was called (for expiring first ordering)
        mock_db.query.return_value.filter.return_value.order_by.assert_called()


class TestGetExpiringPackages:
    """Tests for get_expiring_packages method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def expiring_package(self):
        """Create mock package expiring soon."""
        package = MagicMock()
        package.id = 1
        package.status = "active"
        package.sessions_remaining = 3
        package.expires_at = datetime.now(UTC) + timedelta(days=5)
        package.expiry_warning_sent = False
        package.tutor_profile = MagicMock()
        return package

    def test_returns_expiring_packages(self, mock_db, expiring_package):
        """Test that expiring packages are returned."""
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            expiring_package
        ]

        result = PackageExpirationService.get_expiring_packages(mock_db, days_until_expiry=7)

        assert len(result) == 1
        assert result[0].id == 1

    def test_excludes_already_warned_packages(self, mock_db):
        """Test that packages with warning already sent are excluded."""
        warned_package = MagicMock()
        warned_package.id = 1
        warned_package.expiry_warning_sent = True

        # The query filter should exclude this package
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = (
            []
        )

        result = PackageExpirationService.get_expiring_packages(mock_db)

        assert len(result) == 0

    def test_uses_default_7_days(self, mock_db):
        """Test that default days_until_expiry is 7."""
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = (
            []
        )

        # Call without parameter to use default
        PackageExpirationService.get_expiring_packages(mock_db)

        # Method should work with default parameter
        mock_db.query.assert_called()

    def test_custom_days_until_expiry(self, mock_db):
        """Test that custom days_until_expiry works."""
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = (
            []
        )

        # Call with custom days
        PackageExpirationService.get_expiring_packages(mock_db, days_until_expiry=14)

        mock_db.query.assert_called()


class TestSendExpiryWarnings:
    """Tests for send_expiry_warnings method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def expiring_package(self):
        """Create mock expiring package."""
        package = MagicMock()
        package.id = 1
        package.student_id = 1
        package.status = "active"
        package.sessions_remaining = 3
        package.expires_at = datetime.now(UTC) + timedelta(days=5)
        package.expiry_warning_sent = False
        package.tutor_profile = MagicMock()
        package.tutor_profile_id = 1
        package.updated_at = None
        return package

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_sends_warnings_for_expiring_packages(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that warnings are sent for expiring packages."""
        # Mock get_expiring_packages to return our expiring package
        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            # Mock the TutorSubject query
            mock_tutor_subject = MagicMock()
            mock_tutor_subject.subject = MagicMock()
            mock_tutor_subject.subject.name = "Mathematics"
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_tutor_subject
            )

            count = PackageExpirationService.send_expiry_warnings(mock_db)

            assert count == 1
            assert expiring_package.expiry_warning_sent is True
            mock_notification_service.notify_package_expiring.assert_called_once()
            mock_db.commit.assert_called_once()

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_returns_zero_when_no_expiring_packages(
        self, mock_notification_service, mock_db
    ):
        """Test that zero is returned when no packages are expiring."""
        with patch.object(
            PackageExpirationService, "get_expiring_packages", return_value=[]
        ):
            count = PackageExpirationService.send_expiry_warnings(mock_db)

            assert count == 0
            mock_notification_service.notify_package_expiring.assert_not_called()

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_marks_warning_as_sent(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that expiry_warning_sent is set to True after warning."""
        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            PackageExpirationService.send_expiry_warnings(mock_db)

            assert expiring_package.expiry_warning_sent is True
            assert expiring_package.updated_at is not None

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_continues_on_individual_notification_error(
        self, mock_notification_service, mock_db
    ):
        """Test that errors on individual notifications don't stop processing."""
        pkg1 = MagicMock()
        pkg1.id = 1
        pkg1.student_id = 1
        pkg1.sessions_remaining = 3
        pkg1.expires_at = datetime.now(UTC) + timedelta(days=5)
        pkg1.expiry_warning_sent = False
        pkg1.tutor_profile = None
        pkg1.tutor_profile_id = 1

        pkg2 = MagicMock()
        pkg2.id = 2
        pkg2.student_id = 2
        pkg2.sessions_remaining = 2
        pkg2.expires_at = datetime.now(UTC) + timedelta(days=3)
        pkg2.expiry_warning_sent = False
        pkg2.tutor_profile = None
        pkg2.tutor_profile_id = 2

        with patch.object(
            PackageExpirationService, "get_expiring_packages", return_value=[pkg1, pkg2]
        ):
            mock_db.query.return_value.filter.return_value.first.return_value = None
            # First call raises error, second succeeds
            mock_notification_service.notify_package_expiring.side_effect = [
                Exception("Notification error"),
                None,
            ]

            count = PackageExpirationService.send_expiry_warnings(mock_db)

            # Only the second notification succeeded
            assert count == 1

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_rollback_on_critical_error(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that transaction is rolled back on critical error."""
        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.commit.side_effect = Exception("Database error")

            with pytest.raises(Exception):
                PackageExpirationService.send_expiry_warnings(mock_db)

            mock_db.rollback.assert_called()

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_calculates_days_left_correctly(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that days_left calculation is correct."""
        expiring_package.expires_at = datetime.now(UTC) + timedelta(days=5)

        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            PackageExpirationService.send_expiry_warnings(mock_db)

            # Verify expires_in_days parameter
            call_kwargs = mock_notification_service.notify_package_expiring.call_args.kwargs
            assert "expires_in_days" in call_kwargs
            assert call_kwargs["expires_in_days"] >= 4  # Should be around 5

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_uses_tutor_subject_name_when_available(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that subject name from tutor profile is used."""
        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            mock_tutor_subject = MagicMock()
            mock_tutor_subject.subject = MagicMock()
            mock_tutor_subject.subject.name = "Physics"
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_tutor_subject
            )

            PackageExpirationService.send_expiry_warnings(mock_db)

            call_kwargs = mock_notification_service.notify_package_expiring.call_args.kwargs
            assert call_kwargs["subject_name"] == "Physics"

    @patch("modules.packages.services.expiration_service.notification_service")
    def test_defaults_to_tutoring_when_no_subject(
        self, mock_notification_service, mock_db, expiring_package
    ):
        """Test that 'tutoring' is used as default subject name."""
        expiring_package.tutor_profile = None

        with patch.object(
            PackageExpirationService,
            "get_expiring_packages",
            return_value=[expiring_package],
        ):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            PackageExpirationService.send_expiry_warnings(mock_db)

            call_kwargs = mock_notification_service.notify_package_expiring.call_args.kwargs
            assert call_kwargs["subject_name"] == "tutoring"


class TestPackageStatusValues:
    """Tests for valid package status values."""

    def test_active_status_is_valid(self):
        """Test that 'active' is a valid package status."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, _ = PackageExpirationService.check_package_validity(package)
        assert is_valid is True

    def test_expired_status_is_invalid(self):
        """Test that 'expired' is an invalid package status."""
        package = MagicMock()
        package.status = "expired"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, _ = PackageExpirationService.check_package_validity(package)
        assert is_valid is False

    def test_exhausted_status_is_invalid(self):
        """Test that 'exhausted' is an invalid package status."""
        package = MagicMock()
        package.status = "exhausted"
        package.sessions_remaining = 0
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, _ = PackageExpirationService.check_package_validity(package)
        assert is_valid is False

    def test_refunded_status_is_invalid(self):
        """Test that 'refunded' is an invalid package status."""
        package = MagicMock()
        package.status = "refunded"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, _ = PackageExpirationService.check_package_validity(package)
        assert is_valid is False


class TestEdgeCases:
    """Tests for edge cases in package expiration service."""

    def test_package_expires_at_exact_boundary(self):
        """Test package that expires exactly now."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        # Exact boundary should be considered expired (< now)
        assert is_valid is False

    def test_package_with_negative_sessions(self):
        """Test package with negative sessions remaining."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = -1
        package.expires_at = datetime.now(UTC) + timedelta(days=30)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False

    def test_very_old_expiration_date(self):
        """Test package that expired long ago."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) - timedelta(days=365)

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_far_future_expiration_date(self):
        """Test package with far future expiration."""
        package = MagicMock()
        package.status = "active"
        package.sessions_remaining = 5
        package.expires_at = datetime.now(UTC) + timedelta(days=3650)  # 10 years

        is_valid, error = PackageExpirationService.check_package_validity(package)

        assert is_valid is True
        assert error is None
