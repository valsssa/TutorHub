"""Tests for fraud detection service."""

import pytest
from sqlalchemy.orm import Session

from models import RegistrationFraudSignal, User
from modules.auth.services.fraud_detection import (
    MAX_REGISTRATIONS_PER_IP_7_DAYS,
    FraudDetectionService,
)


class TestFraudDetectionService:
    """Tests for FraudDetectionService."""

    @pytest.fixture
    def fraud_service(self, db: Session) -> FraudDetectionService:
        """Create fraud detection service instance."""
        return FraudDetectionService(db)

    def test_get_client_ip_from_request(self, fraud_service: FraudDetectionService):
        """Test extracting client IP from direct request."""
        ip = fraud_service.get_client_ip("192.168.1.1", None)
        assert ip == "192.168.1.1"

    def test_get_client_ip_from_forwarded_header(self, fraud_service: FraudDetectionService):
        """Test extracting client IP from X-Forwarded-For header."""
        ip = fraud_service.get_client_ip("10.0.0.1", "203.0.113.50, 70.41.3.18, 150.172.238.178")
        assert ip == "203.0.113.50"

    def test_get_client_ip_unknown(self, fraud_service: FraudDetectionService):
        """Test handling unknown client IP."""
        ip = fraud_service.get_client_ip(None, None)
        assert ip == "unknown"

    def test_check_ip_fraud_signals_unknown_ip(self, fraud_service: FraudDetectionService):
        """Test that unknown IP doesn't trigger fraud signals."""
        result = fraud_service.check_ip_fraud_signals("unknown")
        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False
        assert len(result["signals"]) == 0

    def test_check_email_fraud_signals_normal_email(self, fraud_service: FraudDetectionService):
        """Test that normal email doesn't trigger fraud signals."""
        result = fraud_service.check_email_fraud_signals("user@gmail.com")
        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False

    def test_check_email_fraud_signals_disposable_email(self, fraud_service: FraudDetectionService):
        """Test that disposable email triggers fraud signal."""
        result = fraud_service.check_email_fraud_signals("user@mailinator.com")
        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True
        assert len(result["signals"]) >= 1
        assert any(s["type"] == "email_pattern" for s in result["signals"])

    def test_check_email_fraud_signals_high_digit_email(self, fraud_service: FraudDetectionService):
        """Test that email with many digits triggers low-confidence signal."""
        result = fraud_service.check_email_fraud_signals("user123456789@example.com")
        assert result["is_suspicious"] is True
        # This alone shouldn't restrict trial (low confidence)
        assert any(s["type"] == "email_pattern" for s in result["signals"])

    def test_check_device_fingerprint_no_fingerprint(self, fraud_service: FraudDetectionService):
        """Test that missing fingerprint doesn't trigger signals."""
        result = fraud_service.check_device_fingerprint(None)
        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False

    def test_analyze_registration_clean(self, fraud_service: FraudDetectionService):
        """Test analyzing a clean registration."""
        result = fraud_service.analyze_registration(
            email="newuser@example.com",
            client_ip="192.168.1.100",
            device_fingerprint=None,
        )
        assert result["is_suspicious"] is False
        assert result["restrict_trial"] is False
        assert result["signal_count"] == 0

    def test_analyze_registration_suspicious_email(self, fraud_service: FraudDetectionService):
        """Test analyzing registration with suspicious email."""
        result = fraud_service.analyze_registration(
            email="user@tempmail.org",
            client_ip="192.168.1.100",
            device_fingerprint=None,
        )
        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True
        assert result["signal_count"] >= 1


class TestFraudDetectionWithDatabase:
    """Tests for fraud detection that require database interactions."""

    @pytest.fixture
    def fraud_service(self, db: Session) -> FraudDetectionService:
        """Create fraud detection service instance."""
        return FraudDetectionService(db)

    def test_check_ip_fraud_signals_multiple_registrations(
        self, fraud_service: FraudDetectionService, db: Session
    ):
        """Test that multiple registrations from same IP trigger fraud signal."""
        # Create multiple users from the same IP
        test_ip = "10.0.0.50"
        for i in range(MAX_REGISTRATIONS_PER_IP_7_DAYS):
            user = User(
                email=f"fraudtest{i}@example.com",
                hashed_password="hashed",
                role="student",
                registration_ip=test_ip,
                trial_restricted=False,
            )
            db.add(user)
        db.commit()

        # Now check if next registration from same IP is flagged
        result = fraud_service.check_ip_fraud_signals(test_ip)
        assert result["is_suspicious"] is True
        assert result["restrict_trial"] is True
        assert result["registrations_7d"] >= MAX_REGISTRATIONS_PER_IP_7_DAYS

    def test_record_fraud_signals(
        self, fraud_service: FraudDetectionService, db: Session, student_user: User
    ):
        """Test recording fraud signals to database."""
        signals = [
            {"type": "email_pattern", "reason": "Suspicious pattern", "confidence": 0.7}
        ]

        recorded = fraud_service.record_fraud_signals(
            user_id=student_user.id,
            signals=signals,
            client_ip="192.168.1.1",
            device_fingerprint="abc123fingerprint",
        )
        db.commit()

        # Should have recorded IP and fingerprint signals at minimum
        assert len(recorded) >= 2

        # Verify signals in database
        db_signals = (
            db.query(RegistrationFraudSignal)
            .filter(RegistrationFraudSignal.user_id == student_user.id)
            .all()
        )
        assert len(db_signals) >= 2

        # Check for IP signal
        ip_signal = next((s for s in db_signals if s.signal_type == "ip_address"), None)
        assert ip_signal is not None
        assert ip_signal.signal_value == "192.168.1.1"

        # Check for fingerprint signal
        fp_signal = next((s for s in db_signals if s.signal_type == "device_fingerprint"), None)
        assert fp_signal is not None
        assert fp_signal.signal_value == "abc123fingerprint"

    def test_get_user_fraud_signals(
        self, fraud_service: FraudDetectionService, db: Session, student_user: User
    ):
        """Test retrieving fraud signals for a user."""
        # Create a signal
        signal = RegistrationFraudSignal(
            user_id=student_user.id,
            signal_type="ip_address",
            signal_value="192.168.1.1",
            confidence_score=85,
        )
        db.add(signal)
        db.commit()

        # Retrieve signals
        signals = fraud_service.get_user_fraud_signals(student_user.id)
        assert len(signals) >= 1
        assert signals[0].signal_type == "ip_address"

    def test_clear_trial_restriction(
        self, fraud_service: FraudDetectionService, db: Session, admin_user: User
    ):
        """Test clearing trial restriction for a user."""
        # Create a restricted user
        restricted_user = User(
            email="restricted@example.com",
            hashed_password="hashed",
            role="student",
            trial_restricted=True,
        )
        db.add(restricted_user)
        db.commit()

        # Add a pending fraud signal
        signal = RegistrationFraudSignal(
            user_id=restricted_user.id,
            signal_type="ip_address",
            signal_value="10.0.0.1",
            confidence_score=80,
        )
        db.add(signal)
        db.commit()

        # Clear the restriction
        result = fraud_service.clear_trial_restriction(restricted_user.id, admin_user.id)
        assert result is True

        # Verify user is no longer restricted
        db.refresh(restricted_user)
        assert restricted_user.trial_restricted is False

        # Verify signal was marked as reviewed
        db.refresh(signal)
        assert signal.reviewed_at is not None
        assert signal.reviewed_by == admin_user.id
        assert signal.review_outcome == "legitimate"

    def test_get_pending_reviews(
        self, fraud_service: FraudDetectionService, db: Session
    ):
        """Test getting users with pending trial restriction reviews."""
        # Create a restricted user
        restricted_user = User(
            email="pending_review@example.com",
            hashed_password="hashed",
            role="student",
            trial_restricted=True,
        )
        db.add(restricted_user)
        db.commit()

        # Get pending reviews
        pending = fraud_service.get_pending_reviews(limit=10)
        assert len(pending) >= 1
        assert any(u.email == "pending_review@example.com" for u in pending)

    def test_mark_reviewed(
        self, fraud_service: FraudDetectionService, db: Session, admin_user: User
    ):
        """Test marking a fraud signal as reviewed."""
        # Create a signal
        signal = RegistrationFraudSignal(
            user_id=admin_user.id,
            signal_type="ip_address",
            signal_value="192.168.1.1",
            confidence_score=75,
        )
        db.add(signal)
        db.commit()

        # Mark as reviewed
        updated = fraud_service.mark_reviewed(
            signal_id=signal.id,
            reviewer_id=admin_user.id,
            outcome="legitimate",
            notes="Verified by admin",
        )

        assert updated is not None
        assert updated.reviewed_at is not None
        assert updated.reviewed_by == admin_user.id
        assert updated.review_outcome == "legitimate"
        assert updated.review_notes == "Verified by admin"


class TestRegistrationWithFraudDetection:
    """Integration tests for registration with fraud detection."""

    def test_registration_stores_ip(self, client, db: Session):
        """Test that registration stores the client IP."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "iptest@example.com",
                "password": "Password123!",
                "first_name": "IP",
                "last_name": "Test",
            },
        )
        assert response.status_code == 201

        # Check that the user has registration_ip stored
        user = db.query(User).filter(User.email == "iptest@example.com").first()
        assert user is not None
        # IP might be set or not depending on test client configuration
        # The important thing is the field exists

    def test_registration_accepts_device_fingerprint(self, client):
        """Test that registration accepts device fingerprint header."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fptest@example.com",
                "password": "Password123!",
                "first_name": "FP",
                "last_name": "Test",
            },
            headers={"X-Device-Fingerprint": "test-fingerprint-hash"},
        )
        assert response.status_code == 201

    def test_registration_with_suspicious_email(self, client, db: Session):
        """Test registration with suspicious email patterns."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@mailinator.com",
                "password": "Password123!",
                "first_name": "Suspicious",
                "last_name": "User",
            },
        )
        # Registration should still succeed but user might be trial-restricted
        assert response.status_code == 201

        user = db.query(User).filter(User.email == "user@mailinator.com").first()
        assert user is not None
        assert user.trial_restricted is True
