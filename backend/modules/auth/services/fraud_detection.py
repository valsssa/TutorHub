"""Fraud detection service for trial abuse prevention."""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import RegistrationFraudSignal, User

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Configuration constants
MAX_REGISTRATIONS_PER_IP_7_DAYS = 3
MAX_REGISTRATIONS_PER_IP_24_HOURS = 2
SUSPICIOUS_EMAIL_PATTERNS = [
    # Common disposable email domains (sample list)
    "tempmail",
    "throwaway",
    "mailinator",
    "guerrillamail",
    "10minutemail",
]


class FraudDetectionService:
    """Service for detecting potential trial abuse during registration."""

    def __init__(self, db: Session):
        """Initialize fraud detection service."""
        self.db = db

    def get_client_ip(self, request_client_host: str | None, forwarded_for: str | None) -> str:
        """
        Extract real client IP, handling proxies.

        Args:
            request_client_host: Direct client host from request
            forwarded_for: X-Forwarded-For header value

        Returns:
            Best estimate of real client IP
        """
        if forwarded_for:
            # X-Forwarded-For contains comma-separated list: client, proxy1, proxy2
            # First IP is the original client
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            if ips:
                return ips[0]

        return request_client_host or "unknown"

    def check_ip_fraud_signals(self, client_ip: str) -> dict[str, Any]:
        """
        Check for fraud signals based on IP address.

        Args:
            client_ip: Client IP address

        Returns:
            Dict with fraud check results
        """
        if client_ip == "unknown":
            return {
                "is_suspicious": False,
                "signals": [],
                "restrict_trial": False,
            }

        signals: list[dict[str, Any]] = []
        restrict_trial = False

        # Check registrations in last 7 days from this IP
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_registrations_7d = (
            self.db.query(User)
            .filter(
                func.host(User.registration_ip) == client_ip,
                User.created_at > seven_days_ago,
                User.deleted_at.is_(None),
            )
            .count()
        )

        if recent_registrations_7d >= MAX_REGISTRATIONS_PER_IP_7_DAYS:
            signals.append({
                "type": "ip_address",
                "reason": f"Multiple registrations from same IP ({recent_registrations_7d} in 7 days)",
                "confidence": 0.85,
            })
            restrict_trial = True
            logger.warning(
                f"Fraud signal: {recent_registrations_7d} registrations from IP {client_ip} in 7 days"
            )

        # Check registrations in last 24 hours from this IP
        one_day_ago = datetime.now(UTC) - timedelta(hours=24)
        recent_registrations_24h = (
            self.db.query(User)
            .filter(
                func.host(User.registration_ip) == client_ip,
                User.created_at > one_day_ago,
                User.deleted_at.is_(None),
            )
            .count()
        )

        if recent_registrations_24h >= MAX_REGISTRATIONS_PER_IP_24_HOURS:
            signals.append({
                "type": "ip_address",
                "reason": f"Rapid registrations from same IP ({recent_registrations_24h} in 24 hours)",
                "confidence": 0.90,
            })
            restrict_trial = True
            logger.warning(
                f"Fraud signal: {recent_registrations_24h} registrations from IP {client_ip} in 24 hours"
            )

        return {
            "is_suspicious": len(signals) > 0,
            "signals": signals,
            "restrict_trial": restrict_trial,
            "registrations_7d": recent_registrations_7d,
            "registrations_24h": recent_registrations_24h,
        }

    def check_email_fraud_signals(self, email: str) -> dict[str, Any]:
        """
        Check for fraud signals based on email patterns.

        Args:
            email: User email address

        Returns:
            Dict with fraud check results
        """
        signals: list[dict[str, Any]] = []
        restrict_trial = False

        email_lower = email.lower()
        email_domain = email_lower.split("@")[-1] if "@" in email_lower else ""

        # Check for disposable email patterns
        for pattern in SUSPICIOUS_EMAIL_PATTERNS:
            if pattern in email_domain:
                signals.append({
                    "type": "email_pattern",
                    "reason": f"Potentially disposable email domain: {email_domain}",
                    "confidence": 0.70,
                })
                restrict_trial = True
                logger.warning(f"Fraud signal: Disposable email pattern detected in {email_domain}")
                break

        # Check for email with many numbers (common pattern for fake accounts)
        local_part = email_lower.split("@")[0] if "@" in email_lower else email_lower
        digit_count = sum(c.isdigit() for c in local_part)
        if len(local_part) > 0 and digit_count / len(local_part) > 0.5:
            signals.append({
                "type": "email_pattern",
                "reason": "Email has high proportion of numbers",
                "confidence": 0.40,
            })
            # Don't restrict trial for this alone, just flag it
            logger.info(f"Fraud signal (low confidence): Email has many numbers: {email}")

        # Check for similar emails registered recently (e.g., user1@, user2@, user3@)
        if email_domain and local_part:
            # Remove trailing numbers to find base pattern
            base_pattern = local_part.rstrip("0123456789")
            if base_pattern and len(base_pattern) < len(local_part):
                seven_days_ago = datetime.now(UTC) - timedelta(days=7)
                similar_emails = (
                    self.db.query(User)
                    .filter(
                        User.email.ilike(f"{base_pattern}%@{email_domain}"),
                        User.created_at > seven_days_ago,
                        User.deleted_at.is_(None),
                    )
                    .count()
                )
                if similar_emails >= 2:
                    signals.append({
                        "type": "email_pattern",
                        "reason": f"Similar email pattern detected ({similar_emails} similar addresses)",
                        "confidence": 0.75,
                    })
                    restrict_trial = True
                    logger.warning(
                        f"Fraud signal: {similar_emails} similar emails to {email} registered recently"
                    )

        return {
            "is_suspicious": len(signals) > 0,
            "signals": signals,
            "restrict_trial": restrict_trial,
        }

    def check_device_fingerprint(self, device_fingerprint: str | None) -> dict[str, Any]:
        """
        Check for fraud signals based on device fingerprint.

        Args:
            device_fingerprint: Device fingerprint hash (from browser/client)

        Returns:
            Dict with fraud check results
        """
        if not device_fingerprint:
            return {
                "is_suspicious": False,
                "signals": [],
                "restrict_trial": False,
            }

        signals: list[dict[str, Any]] = []
        restrict_trial = False

        # Check for same device fingerprint registering multiple accounts
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        same_fingerprint_count = (
            self.db.query(RegistrationFraudSignal)
            .filter(
                RegistrationFraudSignal.signal_type == "device_fingerprint",
                RegistrationFraudSignal.signal_value == device_fingerprint,
                RegistrationFraudSignal.detected_at > seven_days_ago,
            )
            .count()
        )

        if same_fingerprint_count >= 2:
            signals.append({
                "type": "device_fingerprint",
                "reason": f"Same device registered {same_fingerprint_count} accounts in 7 days",
                "confidence": 0.90,
            })
            restrict_trial = True
            logger.warning(
                f"Fraud signal: Device fingerprint {device_fingerprint[:20]}... "
                f"has {same_fingerprint_count} registrations"
            )

        return {
            "is_suspicious": len(signals) > 0,
            "signals": signals,
            "restrict_trial": restrict_trial,
        }

    def analyze_registration(
        self,
        email: str,
        client_ip: str,
        device_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform comprehensive fraud analysis for a registration.

        Args:
            email: User email
            client_ip: Client IP address
            device_fingerprint: Optional device fingerprint

        Returns:
            Comprehensive fraud analysis results
        """
        all_signals: list[dict[str, Any]] = []
        should_restrict_trial = False

        # Check IP-based signals
        ip_check = self.check_ip_fraud_signals(client_ip)
        all_signals.extend(ip_check["signals"])
        if ip_check["restrict_trial"]:
            should_restrict_trial = True

        # Check email-based signals
        email_check = self.check_email_fraud_signals(email)
        all_signals.extend(email_check["signals"])
        if email_check["restrict_trial"]:
            should_restrict_trial = True

        # Check device fingerprint signals
        if device_fingerprint:
            device_check = self.check_device_fingerprint(device_fingerprint)
            all_signals.extend(device_check["signals"])
            if device_check["restrict_trial"]:
                should_restrict_trial = True

        # Calculate overall risk score (average of signal confidences)
        risk_score = 0.0
        if all_signals:
            risk_score = sum(s["confidence"] for s in all_signals) / len(all_signals)

        return {
            "is_suspicious": len(all_signals) > 0,
            "restrict_trial": should_restrict_trial,
            "signals": all_signals,
            "signal_count": len(all_signals),
            "risk_score": risk_score,
            "client_ip": client_ip,
        }

    def record_fraud_signals(
        self,
        user_id: int,
        signals: list[dict[str, Any]],
        client_ip: str,
        device_fingerprint: str | None = None,
    ) -> list[RegistrationFraudSignal]:
        """
        Record detected fraud signals in the database.

        Args:
            user_id: The registered user's ID
            signals: List of detected fraud signals
            client_ip: Client IP address
            device_fingerprint: Optional device fingerprint

        Returns:
            List of created RegistrationFraudSignal records
        """
        created_signals: list[RegistrationFraudSignal] = []

        # Always record the IP address if known
        if client_ip and client_ip != "unknown":
            ip_signal = RegistrationFraudSignal(
                user_id=user_id,
                signal_type="ip_address",
                signal_value=client_ip,
                confidence_score=50,  # Neutral confidence for just recording
            )
            self.db.add(ip_signal)
            created_signals.append(ip_signal)

        # Record device fingerprint if provided
        if device_fingerprint:
            fp_signal = RegistrationFraudSignal(
                user_id=user_id,
                signal_type="device_fingerprint",
                signal_value=device_fingerprint,
                confidence_score=50,
            )
            self.db.add(fp_signal)
            created_signals.append(fp_signal)

        # Record any additional suspicious signals
        for signal in signals:
            if signal["type"] not in ["ip_address", "device_fingerprint"]:
                fraud_signal = RegistrationFraudSignal(
                    user_id=user_id,
                    signal_type=signal["type"],
                    signal_value=signal.get("reason", "Unknown"),
                    confidence_score=int(signal.get("confidence", 0.5) * 100),
                )
                self.db.add(fraud_signal)
                created_signals.append(fraud_signal)

        return created_signals

    def get_user_fraud_signals(self, user_id: int) -> list[RegistrationFraudSignal]:
        """
        Get all fraud signals for a specific user.

        Args:
            user_id: User ID

        Returns:
            List of fraud signals
        """
        return (
            self.db.query(RegistrationFraudSignal)
            .filter(RegistrationFraudSignal.user_id == user_id)
            .order_by(RegistrationFraudSignal.detected_at.desc())
            .all()
        )

    def get_pending_reviews(self, limit: int = 50) -> list[User]:
        """
        Get users with trial restrictions pending review.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of users pending fraud review
        """
        return (
            self.db.query(User)
            .filter(
                User.trial_restricted.is_(True),
                User.deleted_at.is_(None),
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_reviewed(
        self,
        signal_id: int,
        reviewer_id: int,
        outcome: str,
        notes: str | None = None,
    ) -> RegistrationFraudSignal | None:
        """
        Mark a fraud signal as reviewed.

        Args:
            signal_id: Fraud signal ID
            reviewer_id: Admin user ID performing review
            outcome: Review outcome (legitimate, fraudulent, suspicious)
            notes: Optional review notes

        Returns:
            Updated fraud signal or None if not found
        """
        signal = (
            self.db.query(RegistrationFraudSignal)
            .filter(RegistrationFraudSignal.id == signal_id)
            .first()
        )

        if not signal:
            return None

        signal.reviewed_at = datetime.now(UTC)
        signal.reviewed_by = reviewer_id
        signal.review_outcome = outcome
        signal.review_notes = notes

        self.db.commit()
        self.db.refresh(signal)

        logger.info(
            f"Fraud signal {signal_id} reviewed by user {reviewer_id}: {outcome}"
        )

        return signal

    def clear_trial_restriction(self, user_id: int, admin_id: int) -> bool:
        """
        Clear trial restriction for a user after manual review.

        Args:
            user_id: User ID to clear restriction
            admin_id: Admin user performing the action

        Returns:
            True if successful, False if user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        user.trial_restricted = False
        user.updated_at = datetime.now(UTC)

        # Mark all pending signals as reviewed
        pending_signals = (
            self.db.query(RegistrationFraudSignal)
            .filter(
                RegistrationFraudSignal.user_id == user_id,
                RegistrationFraudSignal.reviewed_at.is_(None),
            )
            .all()
        )

        for signal in pending_signals:
            signal.reviewed_at = datetime.now(UTC)
            signal.reviewed_by = admin_id
            signal.review_outcome = "legitimate"
            signal.review_notes = "Trial restriction cleared by admin"

        self.db.commit()

        logger.info(
            f"Trial restriction cleared for user {user_id} by admin {admin_id}"
        )

        return True
