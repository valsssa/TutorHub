"""
Comprehensive tests for payment flow functionality.

Tests cover:
- Checkout session creation
- Webhook handling for various Stripe events
- Refund processing
- Payment status queries
- Wallet top-ups
- Edge cases and error handling
"""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


class TestPaymentCheckout:
    """Test checkout session creation."""

    def test_create_checkout_success(
        self, client, student_token, db_session, test_booking
    ):
        """Test successful checkout session creation."""
        with patch("modules.payments.router.create_checkout_session") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_test_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
            mock_session.expires_at = None
            mock_create.return_value = mock_session

            response = client.post(
                "/api/payments/checkout",
                json={"booking_id": test_booking.id},
                headers={"Authorization": f"Bearer {student_token}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"
            assert data["session_id"] == "cs_test_123"

    def test_create_checkout_booking_not_found(self, client, student_token):
        """Test checkout with non-existent booking."""
        response = client.post(
            "/api/payments/checkout",
            json={"booking_id": 99999},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_create_checkout_not_owner(
        self, client, db_session, tutor_token, test_booking
    ):
        """Test checkout fails when user doesn't own booking."""
        response = client.post(
            "/api/payments/checkout",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "own bookings" in response.json()["detail"].lower()

    def test_create_checkout_invalid_status(
        self, client, student_token, db_session, test_booking
    ):
        """Test checkout fails for completed bookings."""
        test_booking.status = "COMPLETED"
        db_session.commit()

        response = client.post(
            "/api/payments/checkout",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot pay" in response.json()["detail"].lower()

    def test_create_checkout_already_paid(
        self, client, student_token, db_session, test_booking
    ):
        """Test checkout fails when booking already paid."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            paid_at=datetime.now(UTC),
        )
        db_session.add(payment)
        db_session.commit()

        response = client.post(
            "/api/payments/checkout",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already paid" in response.json()["detail"].lower()

    def test_create_checkout_requires_auth(self, client, test_booking):
        """Test checkout requires authentication."""
        response = client.post(
            "/api/payments/checkout",
            json={"booking_id": test_booking.id},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPaymentStatus:
    """Test payment status queries."""

    def test_get_payment_status_pending(
        self, client, student_token, db_session, test_booking
    ):
        """Test getting status for pending payment."""
        response = client.get(
            f"/api/payments/status/{test_booking.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["booking_id"] == test_booking.id
        assert data["status"] == "pending"
        assert data["paid_at"] is None

    def test_get_payment_status_completed(
        self, client, student_token, db_session, test_booking
    ):
        """Test getting status for completed payment."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id="pi_test_123",
            paid_at=datetime.now(UTC),
        )
        db_session.add(payment)
        db_session.commit()

        response = client.get(
            f"/api/payments/status/{test_booking.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["stripe_payment_intent_id"] == "pi_test_123"
        assert data["paid_at"] is not None

    def test_get_payment_status_booking_not_found(self, client, student_token):
        """Test getting status for non-existent booking."""
        response = client.get(
            "/api/payments/status/99999",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_payment_status_access_denied(
        self, client, db_session, test_booking
    ):
        """Test access denied when not booking participant."""
        from models import User
        from auth import get_password_hash
        from core.security import TokenManager

        other_user = User(
            email="other@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        token = TokenManager.create_access_token({"sub": other_user.email})

        response = client.get(
            f"/api/payments/status/{test_booking.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tutor_can_view_payment_status(
        self, client, tutor_token, db_session, test_booking
    ):
        """Test tutor can view payment status for their booking."""
        response = client.get(
            f"/api/payments/status/{test_booking.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_200_OK


class TestWebhookHandling:
    """Test Stripe webhook event handling."""

    def _create_webhook_request(self, event_type: str, data: dict) -> tuple[bytes, str]:
        """Create a mock webhook payload and signature."""
        event = {
            "id": f"evt_test_{event_type}",
            "type": event_type,
            "data": {"object": data},
        }
        payload = json.dumps(event).encode()
        return payload, "test_signature"

    def test_webhook_checkout_completed(self, client, db_session, test_booking):
        """Test handling checkout.session.completed webhook."""
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = "evt_test_123"
            mock_event.data.object = {
                "id": "cs_test_123",
                "metadata": {"booking_id": str(test_booking.id)},
                "amount_total": 5000,
                "currency": "usd",
                "payment_intent": "pi_test_123",
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "success"

            from models import Payment

            payment = (
                db_session.query(Payment)
                .filter(Payment.booking_id == test_booking.id)
                .first()
            )
            assert payment is not None
            assert payment.status == "completed"

    def test_webhook_payment_intent_succeeded(self, client, db_session, test_booking):
        """Test handling payment_intent.succeeded webhook."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="pending",
            stripe_payment_intent_id="pi_test_456",
        )
        db_session.add(payment)
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "payment_intent.succeeded"
            mock_event.id = "evt_test_456"
            mock_event.data.object = {
                "id": "pi_test_456",
                "metadata": {"booking_id": str(test_booking.id)},
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK

            db_session.refresh(payment)
            assert payment.status == "completed"
            assert payment.paid_at is not None

    def test_webhook_payment_failed(self, client, db_session, test_booking):
        """Test handling payment_intent.payment_failed webhook."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="pending",
            stripe_payment_intent_id="pi_test_789",
        )
        db_session.add(payment)
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "payment_intent.payment_failed"
            mock_event.id = "evt_test_789"
            mock_event.data.object = {
                "id": "pi_test_789",
                "metadata": {"booking_id": str(test_booking.id)},
                "last_payment_error": {"message": "Card declined"},
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK

            db_session.refresh(payment)
            assert payment.status == "failed"
            assert payment.error_message == "Card declined"

    def test_webhook_charge_refunded(self, client, db_session, test_booking):
        """Test handling charge.refunded webhook."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id="pi_test_refund",
            paid_at=datetime.now(UTC),
        )
        db_session.add(payment)
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "charge.refunded"
            mock_event.id = "evt_test_refund"
            mock_event.data.object = {
                "payment_intent": "pi_test_refund",
                "amount_refunded": 5000,
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK

            db_session.refresh(payment)
            assert payment.status == "refunded"
            assert payment.refund_amount_cents == 5000

    def test_webhook_partial_refund(self, client, db_session, test_booking):
        """Test handling partial refund webhook."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id="pi_test_partial",
            paid_at=datetime.now(UTC),
        )
        db_session.add(payment)
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "charge.refunded"
            mock_event.id = "evt_test_partial"
            mock_event.data.object = {
                "payment_intent": "pi_test_partial",
                "amount_refunded": 2500,
            }
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK

            db_session.refresh(payment)
            assert payment.status == "partially_refunded"
            assert payment.refund_amount_cents == 2500

    def test_webhook_idempotency(self, client, db_session, test_booking):
        """Test webhook idempotency - same event processed only once."""
        from models import WebhookEvent

        existing_event = WebhookEvent(
            stripe_event_id="evt_duplicate",
            event_type="checkout.session.completed",
        )
        db_session.add(existing_event)
        db_session.commit()

        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "checkout.session.completed"
            mock_event.id = "evt_duplicate"
            mock_event.data.object = {}
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "already_processed"

    def test_webhook_unhandled_event(self, client, db_session):
        """Test unhandled webhook event type is logged but accepted."""
        with patch("modules.payments.router.verify_webhook_signature") as mock_verify:
            mock_event = MagicMock()
            mock_event.type = "unknown.event.type"
            mock_event.id = "evt_unknown"
            mock_event.data.object = {}
            mock_verify.return_value = mock_event

            response = client.post(
                "/api/payments/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test_sig"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "success"


class TestRefunds:
    """Test refund processing."""

    def test_refund_success(self, client, admin_token, db_session, test_booking):
        """Test successful refund by admin."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id="pi_test_admin_refund",
            paid_at=datetime.now(UTC),
        )
        db_session.add(payment)
        db_session.commit()

        with patch("modules.payments.router.create_refund") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_test_123"
            mock_refund_obj.amount = 5000
            mock_refund.return_value = mock_refund_obj

            response = client.post(
                "/api/payments/refund",
                json={"booking_id": test_booking.id, "reason": "Customer request"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["refund_id"] == "re_test_123"
            assert data["amount_cents"] == 5000
            assert data["status"] == "succeeded"

    def test_refund_requires_admin(self, client, student_token, db_session, test_booking):
        """Test refund requires admin access."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id="pi_test_student_refund",
        )
        db_session.add(payment)
        db_session.commit()

        response = client.post(
            "/api/payments/refund",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["detail"].lower()

    def test_refund_booking_not_found(self, client, admin_token):
        """Test refund for non-existent booking."""
        response = client.post(
            "/api/payments/refund",
            json={"booking_id": 99999},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_refund_no_completed_payment(self, client, admin_token, db_session, test_booking):
        """Test refund fails when no completed payment exists."""
        response = client.post(
            "/api/payments/refund",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no completed payment" in response.json()["detail"].lower()

    def test_refund_non_stripe_payment(self, client, admin_token, db_session, test_booking):
        """Test refund fails for non-Stripe payments."""
        from models import Payment

        payment = Payment(
            booking_id=test_booking.id,
            amount_cents=5000,
            currency="usd",
            status="completed",
            stripe_payment_intent_id=None,
        )
        db_session.add(payment)
        db_session.commit()

        response = client.post(
            "/api/payments/refund",
            json={"booking_id": test_booking.id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "stripe" in response.json()["detail"].lower()


class TestWalletTopup:
    """Test wallet credit top-up functionality."""

    def test_wallet_balance_initial(self, client, student_token):
        """Test getting initial wallet balance."""
        response = client.get(
            "/api/wallet/balance",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["balance_cents"] == 0
        assert data["currency"] == "USD"

    def test_wallet_checkout_creation(self, client, student_token):
        """Test creating wallet top-up checkout session."""
        with patch("modules.payments.wallet_router.create_checkout_session") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_wallet_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_wallet_123"
            mock_create.return_value = mock_session

            response = client.post(
                "/api/wallet/checkout",
                json={"amount_cents": 5000, "currency": "USD"},
                headers={"Authorization": f"Bearer {student_token}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_wallet_123"
            assert data["amount_cents"] == 5000

    def test_wallet_checkout_invalid_amount(self, client, student_token):
        """Test wallet checkout fails with invalid amount."""
        response = client.post(
            "/api/wallet/checkout",
            json={"amount_cents": 0, "currency": "USD"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_wallet_checkout_max_amount(self, client, student_token):
        """Test wallet checkout fails when exceeding max amount."""
        response = client.post(
            "/api/wallet/checkout",
            json={"amount_cents": 10000001, "currency": "USD"},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_wallet_requires_student(self, client, tutor_token):
        """Test wallet endpoints require student role."""
        response = client.get(
            "/api/wallet/balance",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStripeConnect:
    """Test Stripe Connect functionality for tutor payouts."""

    def test_connect_status_no_account(self, client, tutor_token, db_session, tutor_user):
        """Test Connect status when tutor has no account."""
        response = client.get(
            "/api/tutor/connect/status",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_account"] is False
        assert "set up" in data["status_message"].lower()

    def test_connect_create_account(self, client, tutor_token, db_session, tutor_user):
        """Test creating a Connect account."""
        with patch("modules.payments.connect_router.create_connect_account") as mock_create:
            mock_account = MagicMock()
            mock_account.id = "acct_test_123"
            mock_create.return_value = mock_account

            with patch("modules.payments.connect_router.create_connect_account_link") as mock_link:
                mock_link_obj = MagicMock()
                mock_link_obj.url = "https://connect.stripe.com/setup/acct_test_123"
                mock_link.return_value = mock_link_obj

                response = client.post(
                    "/api/tutor/connect/create?country=US",
                    headers={"Authorization": f"Bearer {tutor_token}"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "stripe.com" in data["url"]

    def test_connect_requires_tutor(self, client, student_token):
        """Test Connect endpoints require tutor role."""
        response = client.get(
            "/api/tutor/connect/status",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPaymentAmountFormatting:
    """Test payment amount display formatting."""

    def test_format_usd_amount(self):
        """Test USD amount formatting."""
        from core.stripe_client import format_amount_for_display

        assert format_amount_for_display(5000, "usd") == "$50.00"
        assert format_amount_for_display(99, "usd") == "$0.99"
        assert format_amount_for_display(10050, "usd") == "$100.50"

    def test_format_eur_amount(self):
        """Test EUR amount formatting."""
        from core.stripe_client import format_amount_for_display

        assert format_amount_for_display(5000, "eur") == "\u20ac50.00"

    def test_format_gbp_amount(self):
        """Test GBP amount formatting."""
        from core.stripe_client import format_amount_for_display

        assert format_amount_for_display(5000, "gbp") == "\u00a350.00"

    def test_format_unknown_currency(self):
        """Test unknown currency formatting."""
        from core.stripe_client import format_amount_for_display

        assert format_amount_for_display(5000, "xyz") == "XYZ 50.00"
