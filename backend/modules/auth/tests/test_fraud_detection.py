"""Tests for the fraud detection service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from modules.auth.services.fraud_detection import (
    MAX_REGISTRATIONS_PER_IP_24_HOURS,
    MAX_REGISTRATIONS_PER_IP_7_DAYS,
    SUSPICIOUS_EMAIL_PATTERNS,
    FraudDetectionService,
)


class TestFraudDetectionService:
    """Tests for FraudDetectionService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create fraud detection service instance."""
        return FraudDetectionService(mock_db)


class TestGetClientIP:
    """Tests for client IP extraction."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return FraudDetectionService(MagicMock())

    def test_direct_ip(self, service):
        """Test extraction of direct client IP."""
        result = service.get_client_ip("192.168.1.1", None)
        assert result == "192.168.1.1"

    def test_forwarded_for_single_ip(self, service):
        """Test extraction from X-Forwarded-For with single IP."""
        result = service.get_client_ip("10.0.0.1", "203.0.113.1")
        assert result == "203.0.113.1"

    def test_forwarded_for_multiple_ips(self, service):
        """Test extraction from X-Forwarded-For with multiple IPs."""
        result = service.get_client_ip(
            "10.0.0.1", "203.0.113.1, 10.0.0.2, 10.0.0.3"
        )
        assert result == "203.0.113.1"

    def test_forwarded_for_strips_whitespace(self, service):
        """Test whitespace is stripped from IPs."""
        result = service.get_client_ip("10.0.0.1", "  203.0.113.1  ,  10.0.0.2  ")
        assert result == "203.0.113.1"

    def test_no_ip_returns_unknown(self, service):
        """Test returns 'unknown' when no IP available."""
        result = service.get_client_ip(None, None)
        assert result == "unknown"


class TestCheckIPFraudSignals:
    """Tests for IP-based fraud detection."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_unknown_ip_returns_no_signals(self, service, mock_db):
        """Test unknown IP returns no fraud signals."""
        result = service.check_ip_fraud_signals("unknown")

        assert result["is_suspicious"] is False
        assert result["signals"] == []
        assert result["restrict_trial"] is False

    def test_clean_ip(self, service, mock_db):
        """Test clean IP with no previous registrations."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_ip_fraud_signals("192.168.1.1")

        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False

    def test_exceeds_7_day_limit(self, service, mock_db):
        """Test IP exceeding 7-day registration limit."""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            MAX_REGISTRATIONS_PER_IP_7_DAYS,
            0,
        ]

        result = service.check_ip_fraud_signals("192.168.1.1")

        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True
        assert len(result["signals"]) >= 1
        assert result["registrations_7d"] == MAX_REGISTRATIONS_PER_IP_7_DAYS

    def test_exceeds_24_hour_limit(self, service, mock_db):
        """Test IP exceeding 24-hour registration limit."""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            0,
            MAX_REGISTRATIONS_PER_IP_24_HOURS,
        ]

        result = service.check_ip_fraud_signals("192.168.1.1")

        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True
        assert result["registrations_24h"] == MAX_REGISTRATIONS_PER_IP_24_HOURS

    def test_signal_includes_confidence(self, service, mock_db):
        """Test fraud signals include confidence scores."""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            MAX_REGISTRATIONS_PER_IP_7_DAYS,
            0,
        ]

        result = service.check_ip_fraud_signals("192.168.1.1")

        for signal in result["signals"]:
            assert "confidence" in signal
            assert 0 <= signal["confidence"] <= 1


class TestCheckEmailFraudSignals:
    """Tests for email-based fraud detection."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_legitimate_email(self, service, mock_db):
        """Test legitimate email returns no signals."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_email_fraud_signals("user@gmail.com")

        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False

    def test_disposable_email_patterns(self, service, mock_db):
        """Test disposable email domains are flagged."""
        for pattern in SUSPICIOUS_EMAIL_PATTERNS[:2]:
            result = service.check_email_fraud_signals(f"user@{pattern}.com")

            assert result["is_suspicious"] is True
            assert result["restrict_trial"] is True
            signal_types = [s["type"] for s in result["signals"]]
            assert "email_pattern" in signal_types

    def test_high_number_ratio_email(self, service, mock_db):
        """Test email with high proportion of numbers is flagged."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_email_fraud_signals("12345678@example.com")

        assert result["is_suspicious"] is True

    def test_similar_email_pattern(self, service, mock_db):
        """Test similar email patterns are detected."""
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        result = service.check_email_fraud_signals("user1@example.com")

        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True


class TestCheckDeviceFingerprint:
    """Tests for device fingerprint fraud detection."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_no_fingerprint(self, service):
        """Test no fingerprint returns no signals."""
        result = service.check_device_fingerprint(None)

        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False

    def test_new_fingerprint(self, service, mock_db):
        """Test new device fingerprint returns no signals."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_device_fingerprint("fingerprint_abc123")

        assert result["is_suspicious"] is False

    def test_repeated_fingerprint(self, service, mock_db):
        """Test repeated device fingerprint is flagged."""
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        result = service.check_device_fingerprint("fingerprint_abc123")

        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True


class TestAnalyzeRegistration:
    """Tests for comprehensive registration analysis."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_clean_registration(self, service, mock_db):
        """Test clean registration returns no signals."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.analyze_registration(
            email="user@gmail.com",
            client_ip="192.168.1.1",
        )

        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False
        assert result["signal_count"] == 0

    def test_combines_all_signals(self, service, mock_db):
        """Test analysis combines signals from all checks."""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            MAX_REGISTRATIONS_PER_IP_7_DAYS,
            0,
            0,
            3,
        ]

        result = service.analyze_registration(
            email="user1@example.com",
            client_ip="192.168.1.1",
            device_fingerprint="fingerprint_123",
        )

        assert result["is_suspicious"] is True
        assert result["signal_count"] > 0

    def test_calculates_risk_score(self, service, mock_db):
        """Test risk score is calculated correctly."""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            MAX_REGISTRATIONS_PER_IP_7_DAYS,
            MAX_REGISTRATIONS_PER_IP_24_HOURS,
            0,
        ]

        result = service.analyze_registration(
            email="user@gmail.com",
            client_ip="192.168.1.1",
        )

        assert "risk_score" in result
        if result["signal_count"] > 0:
            assert 0 < result["risk_score"] <= 1

    def test_includes_client_ip_in_result(self, service, mock_db):
        """Test client IP is included in result."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.analyze_registration(
            email="user@gmail.com",
            client_ip="192.168.1.1",
        )

        assert result["client_ip"] == "192.168.1.1"


class TestRecordFraudSignals:
    """Tests for recording fraud signals."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_records_ip_address(self, service, mock_db):
        """Test IP address is always recorded."""
        signals = service.record_fraud_signals(
            user_id=1,
            signals=[],
            client_ip="192.168.1.1",
        )

        assert len(signals) >= 1
        mock_db.add.assert_called()

    def test_records_device_fingerprint(self, service, mock_db):
        """Test device fingerprint is recorded when provided."""
        signals = service.record_fraud_signals(
            user_id=1,
            signals=[],
            client_ip="192.168.1.1",
            device_fingerprint="fingerprint_123",
        )

        assert len(signals) >= 2
        call_count = mock_db.add.call_count
        assert call_count >= 2

    def test_records_additional_signals(self, service, mock_db):
        """Test additional fraud signals are recorded."""
        additional_signals = [
            {
                "type": "email_pattern",
                "reason": "Disposable email",
                "confidence": 0.8,
            }
        ]

        signals = service.record_fraud_signals(
            user_id=1,
            signals=additional_signals,
            client_ip="192.168.1.1",
        )

        assert len(signals) >= 2

    def test_unknown_ip_not_recorded(self, service, mock_db):
        """Test unknown IP is not recorded."""
        signals = service.record_fraud_signals(
            user_id=1,
            signals=[],
            client_ip="unknown",
        )

        assert len(signals) == 0


class TestGetUserFraudSignals:
    """Tests for retrieving user fraud signals."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_returns_signals(self, service, mock_db):
        """Test returns fraud signals for user."""
        mock_signals = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_signals
        )

        result = service.get_user_fraud_signals(user_id=1)

        assert result == mock_signals


class TestGetPendingReviews:
    """Tests for retrieving pending reviews."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_returns_pending_users(self, service, mock_db):
        """Test returns users with trial restrictions."""
        mock_users = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_users
        )

        result = service.get_pending_reviews()

        assert result == mock_users

    def test_respects_limit(self, service, mock_db):
        """Test limit parameter is respected."""
        service.get_pending_reviews(limit=10)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(
            10
        )


class TestMarkReviewed:
    """Tests for marking signals as reviewed."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_marks_signal_reviewed(self, service, mock_db):
        """Test marking a signal as reviewed."""
        mock_signal = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_signal

        result = service.mark_reviewed(
            signal_id=1,
            reviewer_id=100,
            outcome="legitimate",
            notes="Verified user",
        )

        assert result == mock_signal
        assert mock_signal.reviewed_by == 100
        assert mock_signal.review_outcome == "legitimate"
        assert mock_signal.review_notes == "Verified user"
        mock_db.commit.assert_called_once()

    def test_returns_none_if_not_found(self, service, mock_db):
        """Test returns None if signal not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.mark_reviewed(
            signal_id=999,
            reviewer_id=100,
            outcome="legitimate",
        )

        assert result is None


class TestClearTrialRestriction:
    """Tests for clearing trial restrictions."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return FraudDetectionService(mock_db)

    def test_clears_restriction(self, service, mock_db):
        """Test clearing trial restriction."""
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.clear_trial_restriction(user_id=1, admin_id=100)

        assert result is True
        assert mock_user.trial_restricted is False
        mock_db.commit.assert_called_once()

    def test_returns_false_if_user_not_found(self, service, mock_db):
        """Test returns False if user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.clear_trial_restriction(user_id=999, admin_id=100)

        assert result is False

    def test_marks_pending_signals_reviewed(self, service, mock_db):
        """Test pending signals are marked as reviewed."""
        mock_user = MagicMock()
        mock_signals = [MagicMock(), MagicMock()]

        def query_side_effect(*args, **kwargs):
            mock = MagicMock()
            mock.filter.return_value.first.return_value = mock_user
            mock.filter.return_value.all.return_value = mock_signals
            return mock

        mock_db.query.side_effect = query_side_effect

        service.clear_trial_restriction(user_id=1, admin_id=100)

        for signal in mock_signals:
            assert signal.reviewed_by == 100
            assert signal.review_outcome == "legitimate"


class TestConstants:
    """Tests for module constants."""

    def test_ip_limits(self):
        """Test IP limit constants."""
        assert MAX_REGISTRATIONS_PER_IP_7_DAYS == 3
        assert MAX_REGISTRATIONS_PER_IP_24_HOURS == 2

    def test_suspicious_email_patterns(self):
        """Test suspicious email patterns."""
        assert len(SUSPICIOUS_EMAIL_PATTERNS) > 0
        assert "tempmail" in SUSPICIOUS_EMAIL_PATTERNS
        assert "mailinator" in SUSPICIOUS_EMAIL_PATTERNS
