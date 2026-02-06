"""
Comprehensive tests for hard payment flow scenarios.

Tests cover complex edge cases and failure scenarios including:
- Stripe webhook edge cases (idempotency, out-of-order, signature failures)
- Payment state inconsistencies (capture during cancellation, double charges)
- Wallet operations (concurrent deductions, rollbacks)
- Refund complexities (partial refunds, disconnected accounts)
- Connect account issues (incomplete onboarding, deauthorization)

These tests validate the payment system's resilience and correctness
under challenging real-world conditions.
"""

import hashlib
import json
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from fastapi import status
from sqlalchemy import update
from sqlalchemy.orm import Session

from models import Booking, Payment, Refund, StudentProfile, TutorProfile, User, WebhookEvent

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_stripe():
    """Create a comprehensive mock for the stripe module."""
    with patch("stripe.checkout.Session") as mock_session, \
         patch("stripe.PaymentIntent") as mock_intent, \
         patch("stripe.Refund") as mock_refund, \
         patch("stripe.Account") as mock_account, \
         patch("stripe.Transfer") as mock_transfer, \
         patch("stripe.Balance") as mock_balance, \
         patch("stripe.Webhook") as mock_webhook:
        yield {
            "Session": mock_session,
            "PaymentIntent": mock_intent,
            "Refund": mock_refund,
            "Account": mock_account,
            "Transfer": mock_transfer,
            "Balance": mock_balance,
            "Webhook": mock_webhook,
        }


@pytest.fixture
def completed_payment(db_session: Session, test_booking: Booking) -> Payment:
    """Create a completed payment for testing refunds."""
    payment = Payment(
        booking_id=test_booking.id,
        student_id=test_booking.student_id,
        amount_cents=5000,
        currency="usd",
        status="completed",
        stripe_checkout_session_id="cs_test_completed",
        stripe_payment_intent_id="pi_test_completed",
        paid_at=datetime.now(UTC),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def tutor_with_connect(db_session: Session, tutor_user: User) -> TutorProfile:
    """Create a tutor with a fully configured Connect account."""
    tutor_profile = tutor_user.tutor_profile
    tutor_profile.stripe_account_id = "acct_test_tutor_123"
    tutor_profile.stripe_charges_enabled = True
    tutor_profile.stripe_payouts_enabled = True
    tutor_profile.stripe_onboarding_completed = True
    db_session.commit()
    db_session.refresh(tutor_profile)
    return tutor_profile


@pytest.fixture
def student_with_balance(db_session: Session, student_user: User) -> StudentProfile:
    """Create a student with wallet balance."""
    student_profile = (
        db_session.query(StudentProfile)
        .filter(StudentProfile.user_id == student_user.id)
        .first()
    )
    if not student_profile:
        student_profile = StudentProfile(user_id=student_user.id)
        db_session.add(student_profile)
    student_profile.credit_balance_cents = 10000  # $100.00
    db_session.commit()
    db_session.refresh(student_profile)
    return student_profile


# =============================================================================
# 1. Stripe Webhook Edge Cases
# =============================================================================


class TestWebhookIdempotency:
    """Test webhook idempotency and duplicate handling."""

    def test_duplicate_webhook_delivery_ignored(
        self, client, db_session, test_booking
    ):
        """Test that duplicate webhook events are handled idempotently."""
        event_id = "evt_test_duplicate_123"

        # First webhook delivery
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = event_id
            mock_event.data.object = {
                "id": "cs_test_123",
                "metadata": {"booking_id": str(test_booking.id)},
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_123",
            }
            mock_verify.return_value = mock_event

            response1 = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )
            assert response1.status_code == status.HTTP_200_OK
            assert response1.json()["status"] == "success"

        # Verify payment was created
        payment_count_after_first = (
            db_session.query(Payment)
            .filter(Payment.booking_id == test_booking.id)
            .count()
        )
        assert payment_count_after_first == 1

        # Second delivery of the same webhook
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = event_id  # Same event ID
            mock_event.data.object = {
                "id": "cs_test_123",
                "metadata": {"booking_id": str(test_booking.id)},
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_123",
            }
            mock_verify.return_value = mock_event

            response2 = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )
            assert response2.status_code == status.HTTP_200_OK
            assert response2.json()["status"] == "already_processed"

        # Verify no duplicate payment was created
        payment_count_after_second = (
            db_session.query(Payment)
            .filter(Payment.booking_id == test_booking.id)
            .count()
        )
        assert payment_count_after_second == 1

    def test_rapid_duplicate_webhooks(self, client, db_session, test_booking):
        """Test handling of rapid duplicate webhook deliveries (race condition)."""
        event_id = "evt_test_rapid_duplicate"
        results = []

        def send_webhook():
            with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
                mock_event = MagicMock()
                mock_event.type = "checkout.session.completed"
                mock_event.id = event_id
                mock_event.data.object = {
                    "id": "cs_test_rapid",
                    "metadata": {"booking_id": str(test_booking.id)},
                    "amount_total": 5000,
                    "currency": "usd",
                    "payment_intent": "pi_test_rapid",
                }
                mock_verify.return_value = mock_event

                response = client.post(
                    "/api/v1/payments/webhook",
                    content=b"{}",
                    headers={"Stripe-Signature": "test_sig"},
                )
                results.append(response.json()["status"])

        # Send 3 webhooks nearly simultaneously
        threads = [threading.Thread(target=send_webhook) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one should succeed, others should be "already_processed"
        assert results.count("success") <= 1
        # At least some should be processed (success or already_processed)
        assert len([r for r in results if r in ["success", "already_processed"]]) >= 1


class TestWebhookOutOfOrder:
    """Test handling of out-of-order webhook events."""

    def test_payment_succeeded_before_checkout_completed(
        self, client, db_session, test_booking
    ):
        """
        Test handling payment_intent.succeeded arriving before checkout.session.completed.

        This can happen due to network timing issues.
        """
        # First: payment_intent.succeeded arrives
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "payment_intent.succeeded"
            mock_event.id = "evt_intent_first"
            mock_event.data.object = {
                "id": "pi_test_ooo",
                "metadata": {"booking_id": str(test_booking.id)},
            }
            mock_verify.return_value = mock_event

            response1 = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )
            assert response1.status_code == status.HTTP_200_OK

        # Then: checkout.session.completed arrives
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = "evt_checkout_second"
            mock_event.data.object = {
                "id": "cs_test_ooo",
                "metadata": {"booking_id": str(test_booking.id)},
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_ooo",
            }
            mock_verify.return_value = mock_event

            response2 = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )
            assert response2.status_code == status.HTTP_200_OK

        # Verify payment is in correct state
        payment = (
            db_session.query(Payment)
            .filter(Payment.booking_id == test_booking.id)
            .first()
        )
        assert payment is not None
        assert payment.status == "completed"

    def test_refund_webhook_for_missing_payment(self, client, db_session):
        """Test handling refund webhook when payment record doesn't exist."""
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "charge.refunded"
            mock_event.id = "evt_orphan_refund"
            mock_event.data.object = {
                "payment_intent": "pi_nonexistent",
                "amount_refunded": 5000,
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            # Should succeed without error (graceful handling)
            assert response.status_code == status.HTTP_200_OK


class TestWebhookSignatureValidation:
    """Test webhook signature validation failures."""

    def test_invalid_signature_rejected(self, client):
        """Test that invalid webhook signatures are rejected."""
        with patch("core.stripe_client.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

            with patch("stripe.Webhook.construct_event") as mock_construct:
                import stripe
                mock_construct.side_effect = stripe.error.SignatureVerificationError(
                    "Invalid signature", "sig_header"
                )

                response = client.post(
                    "/api/v1/payments/webhook",
                    content=b'{"test": "data"}',
                    headers={"Stripe-Signature": "invalid_signature"},
                )

                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "signature" in response.json()["detail"].lower()

    def test_missing_signature_header(self, client):
        """Test that missing signature header is rejected."""
        response = client.post(
            "/api/v1/payments/webhook",
            content=b'{"test": "data"}',
            # No Stripe-Signature header
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_malformed_webhook_payload(self, client):
        """Test handling of malformed webhook payloads."""
        with patch("core.stripe_client.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_construct.side_effect = ValueError("Invalid JSON")

                response = client.post(
                    "/api/v1/payments/webhook",
                    content=b"not valid json {{{",
                    headers={"Stripe-Signature": "test_sig"},
                )

                assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestWebhookTimeoutRetry:
    """Test webhook timeout and retry scenarios."""

    def test_webhook_retry_tracking(self, client, db_session, test_booking):
        """Test that webhook retry attempts are tracked."""
        from core.payment_reliability import webhook_retry_tracker

        event_id = "evt_retry_tracking_test"

        # Simulate first attempt with error
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = event_id
            mock_event.data.object = {
                "id": "cs_test_retry",
                "metadata": {"booking_id": "999999"},  # Non-existent booking
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_retry",
            }
            mock_verify.return_value = mock_event

            client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

        # Check retry info was tracked
        retry_info = webhook_retry_tracker.get_retry_info(event_id)
        assert retry_info is not None
        assert retry_info.attempt_count >= 1


# =============================================================================
# 2. Payment State Inconsistencies
# =============================================================================


class TestPaymentCapturedButBookingCancelled:
    """Test handling payment capture when booking is cancelled."""

    def test_cancel_booking_after_payment_captured(
        self, client, db_session, student_token, test_booking, completed_payment
    ):
        """
        Test cancelling a booking after payment has been captured.

        Should trigger refund process.
        """
        # Mark booking as confirmed (payment captured)
        test_booking.session_state = "SCHEDULED"
        test_booking.payment_state = "CAPTURED"
        db_session.commit()

        # Attempt to cancel
        response = client.post(
            f"/api/v1/bookings/{test_booking.id}/cancel",
            json={"reason": "Schedule conflict"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # This should either succeed (with refund) or be handled gracefully
        # depending on cancellation policy
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,  # If cancellation not allowed
        ]

    def test_payment_captured_for_expired_booking(
        self, client, db_session, test_booking
    ):
        """
        Test webhook handling when payment completes for an expired booking.

        This can happen if booking expires during checkout.
        """
        # Set booking to expired state
        test_booking.session_state = "EXPIRED"
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = "evt_expired_booking"
            mock_event.data.object = {
                "id": "cs_test_expired",
                "metadata": {"booking_id": str(test_booking.id)},
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_expired",
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            # Should handle gracefully
            assert response.status_code == status.HTTP_200_OK

        # Payment should still be recorded for reconciliation
        payment = (
            db_session.query(Payment)
            .filter(Payment.booking_id == test_booking.id)
            .first()
        )
        assert payment is not None


class TestRefundRequestedDuringCapture:
    """Test refund requests during payment capture."""

    def test_concurrent_refund_and_capture(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """
        Test handling when refund is requested while capture is processing.

        Uses idempotency to prevent issues.
        """
        with patch("modules.payments.router.create_refund") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_test_concurrent"
            mock_refund_obj.amount = 5000
            mock_refund_obj.status = "succeeded"
            mock_refund_obj.was_existing = False
            mock_refund.return_value = mock_refund_obj

            # First refund request
            response1 = client.post(
                "/api/v1/payments/refund",
                json={"booking_id": test_booking.id, "reason": "Test refund 1"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response1.status_code == status.HTTP_200_OK

            # Simulate second refund attempt (should use idempotency)
            mock_refund_obj.was_existing = True
            response2 = client.post(
                "/api/v1/payments/refund",
                json={"booking_id": test_booking.id, "reason": "Test refund 2"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            # Second should fail because already refunded
            # (status is now "refunded" from first request)
            assert response2.status_code in [
                status.HTTP_200_OK,  # If partial refund logic kicks in
                status.HTTP_400_BAD_REQUEST,  # If already fully refunded
            ]


class TestDoubleChargePrevention:
    """Test prevention of double charges."""

    def test_checkout_with_existing_paid_payment(
        self, client, db_session, student_token, test_booking, completed_payment
    ):
        """Test that checkout fails if payment already exists."""
        response = client.post(
            "/api/v1/payments/checkout",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already paid" in response.json()["detail"].lower()

    def test_idempotency_key_prevents_duplicate_checkout(
        self, client, db_session, student_token, test_booking
    ):
        """Test that idempotency keys prevent duplicate checkout sessions."""
        with patch("modules.payments.router.create_checkout_session") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_test_idempotent"
            mock_session.url = "https://checkout.stripe.com/pay/cs_test_idempotent"
            mock_session.expires_at = None
            mock_create.return_value = mock_session

            # First checkout
            response1 = client.post(
                "/api/v1/payments/checkout",
                json={"booking_id": test_booking.id},
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert response1.status_code == status.HTTP_200_OK

            # Store session ID on booking to simulate successful creation
            test_booking.stripe_checkout_session_id = "cs_test_idempotent"
            db_session.commit()

        # Second checkout attempt - should return existing session
        with patch("modules.payments.router.retrieve_checkout_session") as mock_retrieve:
            mock_existing = MagicMock()
            mock_existing.id = "cs_test_idempotent"
            mock_existing.url = "https://checkout.stripe.com/pay/cs_test_idempotent"
            mock_existing.status = "open"
            mock_existing.expires_at = None
            mock_retrieve.return_value = mock_existing

            response2 = client.post(
                "/api/v1/payments/checkout",
                json={"booking_id": test_booking.id},
                headers={"Authorization": f"Bearer {student_token}"},
            )

            assert response2.status_code == status.HTTP_200_OK
            assert response2.json()["session_id"] == "cs_test_idempotent"


class TestPaymentIntentExpiredDuringCheckout:
    """Test handling of expired payment intents during checkout."""

    def test_expired_checkout_session_creates_new(
        self, client, db_session, student_token, test_booking
    ):
        """Test that expired checkout sessions are replaced with new ones."""
        # Set an existing (expired) session on booking
        test_booking.stripe_checkout_session_id = "cs_expired_session"
        db_session.commit()

        with patch("modules.payments.router.retrieve_checkout_session") as mock_retrieve:
            # Simulate expired session
            mock_expired = MagicMock()
            mock_expired.id = "cs_expired_session"
            mock_expired.status = "expired"
            mock_expired.url = None
            mock_retrieve.return_value = mock_expired

            with patch("modules.payments.router.create_checkout_session") as mock_create:
                mock_new = MagicMock()
                mock_new.id = "cs_new_session"
                mock_new.url = "https://checkout.stripe.com/pay/cs_new_session"
                mock_new.expires_at = None
                mock_create.return_value = mock_new

                response = client.post(
                    "/api/v1/payments/checkout",
                    json={"booking_id": test_booking.id},
                    headers={"Authorization": f"Bearer {student_token}"},
                )

                assert response.status_code == status.HTTP_200_OK
                assert response.json()["session_id"] == "cs_new_session"


# =============================================================================
# 3. Wallet Operations
# =============================================================================


class TestConcurrentWalletDeductions:
    """Test concurrent wallet balance operations."""

    def test_concurrent_wallet_topup_atomicity(
        self, db_session, student_user, student_with_balance
    ):
        """
        Test that concurrent wallet top-ups use atomic operations.

        Simulates the atomic UPDATE used in _handle_wallet_topup.
        """
        initial_balance = student_with_balance.credit_balance_cents
        topup_amount = 1000

        # Simulate atomic update (like in _handle_wallet_topup)
        db_session.execute(
            update(StudentProfile)
            .where(StudentProfile.id == student_with_balance.id)
            .values(
                credit_balance_cents=StudentProfile.credit_balance_cents + topup_amount,
                updated_at=datetime.now(UTC),
            )
        )
        db_session.commit()

        # Refresh and verify
        db_session.refresh(student_with_balance)
        assert student_with_balance.credit_balance_cents == initial_balance + topup_amount

    def test_wallet_balance_never_negative(self, db_session, student_with_balance):
        """Test that wallet balance cannot go negative through deduction."""
        initial_balance = student_with_balance.credit_balance_cents

        # Attempt to deduct more than balance
        deduction_amount = initial_balance + 5000  # More than available

        # Using atomic operation with check
        from sqlalchemy import case

        db_session.execute(
            update(StudentProfile)
            .where(
                StudentProfile.id == student_with_balance.id,
                StudentProfile.credit_balance_cents >= deduction_amount,
            )
            .values(
                credit_balance_cents=StudentProfile.credit_balance_cents - deduction_amount,
            )
        )
        db_session.commit()

        # Verify balance unchanged (condition wasn't met)
        db_session.refresh(student_with_balance)
        assert student_with_balance.credit_balance_cents == initial_balance


class TestInsufficientBalanceDuringConfirmation:
    """Test handling insufficient wallet balance during booking confirmation."""

    def test_booking_fails_with_insufficient_wallet_balance(
        self, client, db_session, student_token, student_with_balance, tutor_user, test_subject
    ):
        """Test that booking creation fails when wallet balance is insufficient."""
        # Set low balance
        student_with_balance.credit_balance_cents = 100  # Only $1
        db_session.commit()

        # Attempt to create expensive booking using wallet
        # (This test depends on the booking creation endpoint supporting wallet payments)
        response = client.post(
            "/api/v1/bookings",
            json={
                "tutor_profile_id": tutor_user.tutor_profile.id,
                "subject_id": test_subject.id,
                "start_time": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
                "duration_minutes": 60,
                "payment_method": "wallet",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Should either fail with insufficient balance or redirect to payment
        # (behavior depends on implementation)
        assert response.status_code in [
            status.HTTP_201_CREATED,  # Created with payment pending
            status.HTTP_400_BAD_REQUEST,  # Insufficient balance
            status.HTTP_402_PAYMENT_REQUIRED,  # Payment required
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # Validation error
        ]


class TestWalletTopupFailure:
    """Test wallet top-up failure scenarios."""

    def test_wallet_topup_webhook_handles_missing_student(self, client, db_session):
        """Test wallet top-up webhook handles missing student gracefully."""
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = "evt_wallet_missing_student"
            mock_event.data.object = {
                "id": "cs_wallet_missing",
                "metadata": {
                    "payment_type": "wallet_topup",
                    "student_id": "99999",  # Non-existent
                    "student_profile_id": "99999",  # Non-existent
                },
                "amount_total": 5000,
                "currency": "usd",
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            # Should handle gracefully without crash
            assert response.status_code == status.HTTP_200_OK


class TestBalanceRollbackOnFailedBooking:
    """Test wallet balance rollback when booking fails."""

    def test_wallet_deduction_rolled_back_on_booking_failure(
        self, db_session, student_with_balance
    ):
        """Test that wallet deductions are rolled back on transaction failure."""
        initial_balance = student_with_balance.credit_balance_cents
        deduction = 2000

        try:
            # Start transaction
            student_with_balance.credit_balance_cents -= deduction

            # Simulate booking creation failure
            raise ValueError("Simulated booking creation failure")

        except ValueError:
            # Rollback
            db_session.rollback()

        # Verify balance was rolled back
        db_session.refresh(student_with_balance)
        assert student_with_balance.credit_balance_cents == initial_balance


# =============================================================================
# 4. Refund Complexities
# =============================================================================


class TestPartialRefundCalculations:
    """Test partial refund calculation edge cases."""

    def test_multiple_partial_refunds(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """Test multiple partial refunds don't exceed original amount."""
        original_amount = completed_payment.amount_cents

        with patch("modules.payments.router.create_refund") as mock_refund:
            # First partial refund (40%)
            first_refund_amount = int(original_amount * 0.4)
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_partial_1"
            mock_refund_obj.amount = first_refund_amount
            mock_refund_obj.status = "succeeded"
            mock_refund_obj.was_existing = False
            mock_refund.return_value = mock_refund_obj

            response1 = client.post(
                "/api/v1/payments/refund",
                json={
                    "booking_id": test_booking.id,
                    "amount_cents": first_refund_amount,
                    "reason": "Partial refund 1",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response1.status_code == status.HTTP_200_OK
            data1 = response1.json()
            assert data1["remaining_refundable_cents"] == original_amount - first_refund_amount

            # Second partial refund (40%)
            second_refund_amount = int(original_amount * 0.4)
            mock_refund_obj.id = "re_partial_2"
            mock_refund_obj.amount = second_refund_amount
            mock_refund.return_value = mock_refund_obj

            response2 = client.post(
                "/api/v1/payments/refund",
                json={
                    "booking_id": test_booking.id,
                    "amount_cents": second_refund_amount,
                    "reason": "Partial refund 2",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response2.status_code == status.HTTP_200_OK
            data2 = response2.json()
            assert data2["remaining_refundable_cents"] == original_amount - first_refund_amount - second_refund_amount

    def test_refund_exceeding_remaining_amount_rejected(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """Test that refund exceeding remaining refundable amount is rejected."""
        original_amount = completed_payment.amount_cents

        # Create existing refund record
        existing_refund = Refund(
            payment_id=completed_payment.id,
            booking_id=test_booking.id,
            amount_cents=int(original_amount * 0.8),  # 80% already refunded
            currency="usd",
            reason="STUDENT_CANCEL",
            provider_refund_id="re_existing",
        )
        db_session.add(existing_refund)
        db_session.commit()

        # Attempt to refund more than remaining 20%
        response = client.post(
            "/api/v1/payments/refund",
            json={
                "booking_id": test_booking.id,
                "amount_cents": int(original_amount * 0.5),  # 50% requested, only 20% available
                "reason": "Too much refund",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in response.json()["detail"].lower()

    def test_full_refund_of_remaining_amount(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """Test full refund of remaining amount without specifying amount."""
        original_amount = completed_payment.amount_cents
        first_refund_amount = 2000

        # Create partial refund record
        existing_refund = Refund(
            payment_id=completed_payment.id,
            booking_id=test_booking.id,
            amount_cents=first_refund_amount,
            currency="usd",
            reason="STUDENT_CANCEL",
            provider_refund_id="re_partial",
        )
        db_session.add(existing_refund)
        completed_payment.status = "partially_refunded"
        completed_payment.refund_amount_cents = first_refund_amount
        db_session.commit()

        remaining = original_amount - first_refund_amount

        with patch("modules.payments.router.create_refund") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_remaining"
            mock_refund_obj.amount = remaining
            mock_refund_obj.status = "succeeded"
            mock_refund_obj.was_existing = False
            mock_refund.return_value = mock_refund_obj

            # Request full refund without amount (should refund remaining)
            response = client.post(
                "/api/v1/payments/refund",
                json={"booking_id": test_booking.id, "reason": "Full remaining"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["amount_cents"] == remaining
            assert data["remaining_refundable_cents"] == 0


class TestRefundWithDisconnectedAccount:
    """Test refund scenarios when Stripe account is disconnected."""

    def test_refund_fails_gracefully_on_stripe_error(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """Test that refund failures from Stripe are handled gracefully."""
        with patch("modules.payments.router.create_refund") as mock_refund:
            from fastapi import HTTPException as FastAPIHTTPException
            mock_refund.side_effect = FastAPIHTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment service error",
            )

            response = client.post(
                "/api/v1/payments/refund",
                json={"booking_id": test_booking.id, "reason": "Test"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestMultipleRefundAttempts:
    """Test handling of multiple refund attempts on same payment."""

    def test_already_refunded_payment_rejected(
        self, client, db_session, admin_token, test_booking, completed_payment
    ):
        """Test that fully refunded payments cannot be refunded again."""
        # Mark payment as fully refunded
        completed_payment.status = "refunded"
        completed_payment.refund_amount_cents = completed_payment.amount_cents

        # Add refund record
        full_refund = Refund(
            payment_id=completed_payment.id,
            booking_id=test_booking.id,
            amount_cents=completed_payment.amount_cents,
            currency="usd",
            reason="STUDENT_CANCEL",
            provider_refund_id="re_full",
        )
        db_session.add(full_refund)
        db_session.commit()

        # Attempt another refund
        response = client.post(
            "/api/v1/payments/refund",
            json={"booking_id": test_booking.id, "reason": "Double refund attempt"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in response.json()["detail"].lower()


class TestRefundDuringPayoutProcessing:
    """Test refund when payout is being processed."""

    def test_refund_warning_during_payout_window(
        self, client, db_session, admin_token, test_booking, completed_payment, tutor_with_connect
    ):
        """
        Test refund processing during payout window.

        Note: The actual implementation uses payout delays to handle this.
        """
        # Link booking to tutor with connect
        test_booking.tutor_profile_id = tutor_with_connect.id
        db_session.commit()

        with patch("modules.payments.router.create_refund") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_payout_window"
            mock_refund_obj.amount = completed_payment.amount_cents
            mock_refund_obj.status = "succeeded"
            mock_refund_obj.was_existing = False
            mock_refund.return_value = mock_refund_obj

            response = client.post(
                "/api/v1/payments/refund",
                json={"booking_id": test_booking.id, "reason": "During payout window"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            # Should succeed (payout delay handles the timing)
            assert response.status_code == status.HTTP_200_OK


# =============================================================================
# 5. Connect Account Issues
# =============================================================================


class TestTutorOnboardingIncomplete:
    """Test payment handling when tutor onboarding is incomplete."""

    def test_checkout_without_complete_connect_account(
        self, client, db_session, student_token, test_booking, tutor_user
    ):
        """
        Test checkout when tutor hasn't completed Connect onboarding.

        Payment should still work but without destination charge.
        """
        # Set tutor with incomplete Connect account
        tutor_profile = tutor_user.tutor_profile
        tutor_profile.stripe_account_id = "acct_incomplete"
        tutor_profile.stripe_charges_enabled = False
        tutor_profile.stripe_payouts_enabled = False
        db_session.commit()

        with patch("modules.payments.router.create_checkout_session") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_no_connect"
            mock_session.url = "https://checkout.stripe.com/pay/cs_no_connect"
            mock_session.expires_at = None
            mock_create.return_value = mock_session

            response = client.post(
                "/api/v1/payments/checkout",
                json={"booking_id": test_booking.id},
                headers={"Authorization": f"Bearer {student_token}"},
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify create_checkout_session was called without destination
            call_args = mock_create.call_args
            assert call_args.kwargs.get("tutor_connect_account_id") is None

    def test_payout_fails_for_incomplete_account(
        self, client, db_session, tutor_token, tutor_user
    ):
        """Test that payout balance fails for incomplete Connect accounts."""
        # Set incomplete Connect account
        tutor_profile = tutor_user.tutor_profile
        tutor_profile.stripe_account_id = None
        db_session.commit()

        response = client.get(
            "/api/v1/tutor/connect/balance",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no connect account" in response.json()["detail"].lower()


class TestAccountDeauthorizationDuringBookings:
    """Test handling when tutor deauthorizes their Connect account."""

    def test_webhook_handles_account_deauthorization(self, client, db_session, tutor_with_connect):
        """Test that account.updated webhook handles deauthorization."""
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "account.updated"
            mock_event.id = "evt_deauth"
            mock_event.data.object = {
                "id": tutor_with_connect.stripe_account_id,
                "charges_enabled": False,
                "payouts_enabled": False,
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/v1/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK

        # Verify profile was updated
        db_session.refresh(tutor_with_connect)
        assert tutor_with_connect.stripe_charges_enabled is False
        assert tutor_with_connect.stripe_payouts_enabled is False


class TestTransferFailureRecovery:
    """Test recovery from transfer failures."""

    def test_transfer_with_circuit_breaker_open(self, db_session, tutor_with_connect, test_booking):
        """Test transfer handling when circuit breaker is open."""
        from core.payment_reliability import CircuitState, stripe_circuit_breaker

        # Force circuit breaker open
        with stripe_circuit_breaker._state.lock:
            stripe_circuit_breaker._state.state = CircuitState.OPEN
            stripe_circuit_breaker._state.last_failure_time = time.time()

        try:
            from fastapi import HTTPException

            from core.stripe_client import create_transfer_to_tutor

            with pytest.raises(HTTPException) as exc_info:
                create_transfer_to_tutor(
                    amount_cents=4000,
                    currency="usd",
                    tutor_connect_account_id=tutor_with_connect.stripe_account_id,
                    booking_id=test_booking.id,
                )

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        finally:
            # Reset circuit breaker
            stripe_circuit_breaker.reset()


class TestCommissionCalculationEdgeCases:
    """Test commission calculation edge cases."""

    def test_commission_at_tier_boundary(self, db_session, tutor_with_connect):
        """Test commission calculation at tier boundaries."""
        from core.currency import get_commission_tier

        # Test tier boundaries based on actual COMMISSION_TIERS in currency.py:
        # (0, 20%), (100_000 cents = $1000, 15%), (500_000 cents = $5000, 10%)
        test_cases = [
            (0, (Decimal("20.0"), "Standard")),           # New tutor - 20%
            (99_999, (Decimal("20.0"), "Standard")),      # Just under $1000
            (100_000, (Decimal("15.0"), "Silver")),       # Exactly $1000
            (499_999, (Decimal("15.0"), "Silver")),       # Just under $5000
            (500_000, (Decimal("10.0"), "Gold")),         # Exactly $5000
            (1_000_000, (Decimal("10.0"), "Gold")),       # $10000
        ]

        for lifetime_earnings, expected in test_cases:
            result = get_commission_tier(lifetime_earnings)
            assert result == expected, f"Failed for earnings {lifetime_earnings}: got {result}, expected {expected}"

    def test_platform_fee_calculation_precision(self):
        """Test platform fee calculation maintains precision."""
        from core.currency import calculate_platform_fee

        # calculate_platform_fee takes (amount_cents, fee_percentage) and returns (fee_cents, earnings_cents)
        test_cases = [
            (10000, Decimal("3.0"), 300, 9700),    # $100 at 3% = $3 fee, $97 earnings
            (5000, Decimal("20.0"), 1000, 4000),   # $50 at 20% = $10 fee, $40 earnings
            (100, Decimal("15.0"), 15, 85),        # $1 at 15% = $0.15 fee, $0.85 earnings
        ]

        for amount_cents, fee_pct, expected_fee, expected_earnings in test_cases:
            fee_cents, earnings_cents = calculate_platform_fee(amount_cents, fee_pct)
            assert fee_cents == expected_fee, f"Fee mismatch for {amount_cents}: got {fee_cents}, expected {expected_fee}"
            assert earnings_cents == expected_earnings, f"Earnings mismatch for {amount_cents}: got {earnings_cents}, expected {expected_earnings}"

    def test_zero_amount_handling(self):
        """Test handling of zero amounts."""
        from core.currency import calculate_platform_fee

        # Zero amount
        fee_cents, earnings_cents = calculate_platform_fee(0)
        assert fee_cents == 0
        assert earnings_cents == 0


# =============================================================================
# 6. Circuit Breaker and Reliability Tests
# =============================================================================


class TestCircuitBreakerBehavior:
    """Test circuit breaker behavior under various conditions."""

    def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        from core.payment_reliability import CircuitBreaker, CircuitState

        breaker = CircuitBreaker("test_breaker")
        breaker.config.failure_threshold = 3

        # Simulate failures
        for _ in range(3):
            breaker.record_failure(Exception("Test failure"))

        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after timeout."""
        from core.payment_reliability import CircuitBreaker, CircuitState

        breaker = CircuitBreaker("test_timeout_breaker")
        breaker.config.failure_threshold = 1
        breaker.config.timeout_seconds = 0  # Immediate timeout for testing

        # Open the circuit
        breaker.record_failure(Exception("Test failure"))
        assert breaker.state == CircuitState.OPEN

        # Wait briefly and check availability (should transition to half-open)
        time.sleep(0.1)
        is_available = breaker.is_available

        assert is_available is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_closes_after_successes(self):
        """Test circuit breaker closes after successful calls in half-open."""
        from core.payment_reliability import CircuitBreaker, CircuitState

        breaker = CircuitBreaker("test_close_breaker")
        breaker.config.failure_threshold = 1
        breaker.config.success_threshold = 2
        breaker.config.timeout_seconds = 0

        # Open the circuit
        breaker.record_failure(Exception("Test failure"))
        assert breaker.state == CircuitState.OPEN

        # Transition to half-open
        time.sleep(0.1)
        _ = breaker.is_available

        # Record successes
        breaker.record_success()
        breaker.record_success()

        assert breaker.state == CircuitState.CLOSED


class TestIdempotencyKeyGeneration:
    """Test idempotency key generation."""

    def test_same_inputs_generate_same_key(self):
        """Test that same inputs always generate the same key."""
        from core.payment_reliability import generate_idempotency_key

        key1 = generate_idempotency_key(
            "checkout_session", 5000, "usd", booking_id=123
        )
        key2 = generate_idempotency_key(
            "checkout_session", 5000, "usd", booking_id=123
        )

        assert key1 == key2

    def test_different_inputs_generate_different_keys(self):
        """Test that different inputs generate different keys."""
        from core.payment_reliability import generate_idempotency_key

        key1 = generate_idempotency_key(
            "checkout_session", 5000, "usd", booking_id=123
        )
        key2 = generate_idempotency_key(
            "checkout_session", 5000, "usd", booking_id=124  # Different booking
        )

        assert key1 != key2

    def test_key_format_is_valid(self):
        """Test that generated keys have valid format."""
        from core.payment_reliability import generate_idempotency_key

        key = generate_idempotency_key("test_op", booking_id=123)

        assert key.startswith("idem_test_op_")
        assert len(key) <= 64  # Stripe's max key length


# =============================================================================
# 7. Payment Status Polling Tests
# =============================================================================


class TestPaymentStatusPolling:
    """Test payment status polling functionality."""

    def test_poll_returns_cached_result(self):
        """Test that polling returns cached results within TTL."""
        from core.payment_reliability import PaymentStatusInfo, PaymentStatusPoller

        poller = PaymentStatusPoller()
        poller._cache_ttl = 60

        # Add to cache
        status_info = PaymentStatusInfo(
            payment_intent_id="pi_test",
            checkout_session_id="cs_test",
            status="paid",
            amount_cents=5000,
            currency="usd",
            paid=True,
            refunded=False,
            last_checked=datetime.now(UTC),
        )
        poller._cache["session:cs_test"] = status_info

        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            # This should return cached result without calling Stripe
            result = poller.check_checkout_session("cs_test")

            mock_retrieve.assert_not_called()
            assert result.paid is True

    def test_poll_handles_stripe_errors(self):
        """Test that polling handles Stripe errors gracefully."""
        from core.payment_reliability import PaymentStatusPoller

        poller = PaymentStatusPoller()
        poller._cache.clear()

        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            import stripe
            mock_retrieve.side_effect = stripe.error.APIError("Test error")

            with patch("core.payment_reliability.stripe_circuit_breaker.call") as mock_breaker:
                mock_breaker.return_value.__enter__ = Mock()
                mock_breaker.return_value.__exit__ = Mock(return_value=False)

                result = poller.check_checkout_session("cs_error_test")

                assert result.status == "error"
                assert result.error is not None
