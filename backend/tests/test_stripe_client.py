"""
Comprehensive tests for backend/core/stripe_client.py

Tests cover:
- Stripe client initialization and configuration
- Checkout session creation with various scenarios
- Connect account management
- Transfer operations
- Refund processing with idempotency
- Webhook signature verification
- Amount formatting utilities
- Error handling and circuit breaker integration
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import stripe
from fastapi import HTTPException

from core.payment_reliability import CircuitOpenError, stripe_circuit_breaker
from core.stripe_client import (
    RefundResult,
    _ensure_stripe_configured,
    _find_existing_refund,
    create_checkout_session,
    create_connect_account,
    create_connect_account_link,
    create_refund,
    create_transfer_to_tutor,
    format_amount_for_display,
    get_connect_account,
    get_stripe_client,
    is_connect_account_ready,
    retrieve_checkout_session,
    update_connect_account_payout_settings,
    verify_webhook_signature,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """Reset the circuit breaker before each test."""
    stripe_circuit_breaker.reset()
    yield
    stripe_circuit_breaker.reset()


@pytest.fixture
def mock_settings():
    """Mock settings with Stripe configuration."""
    with patch("core.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_mock_key"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        mock_settings.STRIPE_SUCCESS_URL = "https://example.com/success/{booking_id}"
        mock_settings.STRIPE_CANCEL_URL = "https://example.com/cancel/{booking_id}"
        mock_settings.STRIPE_CONNECT_REFRESH_URL = "https://example.com/connect/refresh"
        mock_settings.STRIPE_CONNECT_RETURN_URL = "https://example.com/connect/return"
        mock_settings.STRIPE_PAYOUT_DELAY_DAYS = 7
        mock_settings.FRONTEND_URL = "https://example.com"
        yield mock_settings


@pytest.fixture
def mock_stripe():
    """Mock the stripe module."""
    with patch("core.stripe_client.stripe") as mock_stripe:
        yield mock_stripe


# =============================================================================
# Test: Stripe Client Initialization
# =============================================================================


class TestStripeClientInitialization:
    """Test Stripe client configuration and initialization."""

    def test_ensure_stripe_configured_success(self, mock_settings):
        """Test successful Stripe configuration check."""
        # Should not raise when key is configured
        _ensure_stripe_configured()

    def test_ensure_stripe_configured_no_key(self):
        """Test configuration check fails without secret key."""
        with patch("core.stripe_client.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = None

            with pytest.raises(HTTPException) as exc_info:
                _ensure_stripe_configured()

            assert exc_info.value.status_code == 503
            assert "not configured" in exc_info.value.detail

    def test_ensure_stripe_configured_empty_key(self):
        """Test configuration check fails with empty secret key."""
        with patch("core.stripe_client.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = ""

            with pytest.raises(HTTPException) as exc_info:
                _ensure_stripe_configured()

            assert exc_info.value.status_code == 503

    def test_get_stripe_client_sets_api_key(self, mock_settings, mock_stripe):
        """Test that get_stripe_client sets the API key."""
        client = get_stripe_client()

        assert mock_stripe.api_key == "sk_test_mock_key"
        assert client == mock_stripe


# =============================================================================
# Test: Checkout Session Creation
# =============================================================================


class TestCreateCheckoutSession:
    """Test checkout session creation functionality."""

    def test_create_checkout_session_basic(self, mock_settings, mock_stripe):
        """Test basic checkout session creation for a booking."""
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_checkout_session(
                booking_id=1,
                amount_cents=5000,
                currency="usd",
                tutor_name="John Doe",
                subject_name="Mathematics",
                student_email="student@test.com",
            )

            assert result.id == "cs_test_123"
            mock_stripe.checkout.Session.create.assert_called_once()

    def test_create_checkout_session_with_connect_account(self, mock_settings, mock_stripe):
        """Test checkout session with tutor Connect account."""
        mock_session = MagicMock()
        mock_session.id = "cs_test_connect"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_checkout_session(
                booking_id=1,
                amount_cents=5000,
                currency="usd",
                tutor_name="Jane Tutor",
                subject_name="Physics",
                tutor_connect_account_id="acct_test_tutor",
                platform_fee_cents=500,
            )

            call_args = mock_stripe.checkout.Session.create.call_args
            assert "payment_intent_data" in call_args.kwargs
            assert call_args.kwargs["payment_intent_data"]["transfer_data"]["destination"] == "acct_test_tutor"
            assert call_args.kwargs["payment_intent_data"]["transfer_data"]["amount"] == 4500

    def test_create_checkout_session_wallet_topup(self, mock_settings, mock_stripe):
        """Test checkout session for wallet top-up (no booking_id)."""
        mock_session = MagicMock()
        mock_session.id = "cs_wallet_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_checkout_session(
                booking_id=None,
                amount_cents=10000,
                currency="usd",
                tutor_name=None,
                subject_name="Wallet Top-up",
                customer_email="user@test.com",
                user_id=123,
            )

            call_args = mock_stripe.checkout.Session.create.call_args
            assert call_args.kwargs["metadata"]["type"] == "wallet_topup"
            assert "booking_id" not in call_args.kwargs["metadata"]

    def test_create_checkout_session_custom_urls(self, mock_settings, mock_stripe):
        """Test checkout session with custom success/cancel URLs."""
        mock_session = MagicMock()
        mock_session.id = "cs_custom_urls"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_checkout_session(
                booking_id=1,
                amount_cents=5000,
                currency="usd",
                tutor_name="Tutor",
                subject_name="Subject",
                success_url="https://custom.com/success",
                cancel_url="https://custom.com/cancel",
            )

            call_args = mock_stripe.checkout.Session.create.call_args
            assert call_args.kwargs["success_url"] == "https://custom.com/success"
            assert call_args.kwargs["cancel_url"] == "https://custom.com/cancel"

    def test_create_checkout_session_circuit_breaker_open(self, mock_settings):
        """Test checkout session fails when circuit breaker is open."""
        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock(
                side_effect=CircuitOpenError("Circuit is open")
            )

            with pytest.raises(HTTPException) as exc_info:
                create_checkout_session(
                    booking_id=1,
                    amount_cents=5000,
                    currency="usd",
                    tutor_name="Tutor",
                    subject_name="Subject",
                )

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    def test_create_checkout_session_idempotency_error(self, mock_settings, mock_stripe):
        """Test handling of idempotency conflict."""
        mock_stripe.checkout.Session.create.side_effect = stripe.error.IdempotencyError(
            "Conflict", code="idempotency_error"
        )

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                create_checkout_session(
                    booking_id=1,
                    amount_cents=5000,
                    currency="usd",
                    tutor_name="Tutor",
                    subject_name="Subject",
                )

            assert exc_info.value.status_code == 409
            assert "already being created" in exc_info.value.detail

    def test_create_checkout_session_stripe_error(self, mock_settings, mock_stripe):
        """Test handling of generic Stripe errors."""
        mock_stripe.checkout.Session.create.side_effect = stripe.error.StripeError("Test error")

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            with patch("core.stripe_client.handle_stripe_error") as mock_handler:
                mock_handler.return_value = HTTPException(status_code=502, detail="Payment error")

                with pytest.raises(HTTPException) as exc_info:
                    create_checkout_session(
                        booking_id=1,
                        amount_cents=5000,
                        currency="usd",
                        tutor_name="Tutor",
                        subject_name="Subject",
                    )

                assert exc_info.value.status_code == 502


class TestRetrieveCheckoutSession:
    """Test checkout session retrieval."""

    def test_retrieve_checkout_session_success(self, mock_settings, mock_stripe):
        """Test successful session retrieval."""
        mock_session = MagicMock()
        mock_session.id = "cs_test_retrieve"
        mock_stripe.checkout.Session.retrieve.return_value = mock_session

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = retrieve_checkout_session("cs_test_retrieve")

            assert result.id == "cs_test_retrieve"

    def test_retrieve_checkout_session_circuit_open(self, mock_settings):
        """Test retrieval fails when circuit breaker is open."""
        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock(
                side_effect=CircuitOpenError("Circuit is open")
            )

            with pytest.raises(HTTPException) as exc_info:
                retrieve_checkout_session("cs_test_123")

            assert exc_info.value.status_code == 503


# =============================================================================
# Test: Stripe Connect
# =============================================================================


class TestStripeConnect:
    """Test Stripe Connect account management."""

    def test_create_connect_account_success(self, mock_settings, mock_stripe):
        """Test successful Connect account creation."""
        mock_account = MagicMock()
        mock_account.id = "acct_test_new"
        mock_stripe.Account.create.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_connect_account(
                tutor_user_id=123,
                tutor_email="tutor@test.com",
                country="US",
            )

            assert result.id == "acct_test_new"
            call_args = mock_stripe.Account.create.call_args
            assert call_args.kwargs["type"] == "express"
            assert call_args.kwargs["email"] == "tutor@test.com"
            assert call_args.kwargs["settings"]["payouts"]["schedule"]["delay_days"] == 7

    def test_create_connect_account_with_custom_country(self, mock_settings, mock_stripe):
        """Test Connect account creation with non-US country."""
        mock_account = MagicMock()
        mock_account.id = "acct_test_uk"
        mock_stripe.Account.create.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_connect_account(
                tutor_user_id=456,
                tutor_email="tutor@uk.com",
                country="GB",
            )

            call_args = mock_stripe.Account.create.call_args
            assert call_args.kwargs["country"] == "GB"

    def test_create_connect_account_link_success(self, mock_settings, mock_stripe):
        """Test successful account link creation."""
        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/setup/acct_123"
        mock_stripe.AccountLink.create.return_value = mock_link

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_connect_account_link("acct_123")

            assert "stripe.com" in result.url

    def test_create_connect_account_link_custom_urls(self, mock_settings, mock_stripe):
        """Test account link with custom refresh/return URLs."""
        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/setup/acct_456"
        mock_stripe.AccountLink.create.return_value = mock_link

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_connect_account_link(
                "acct_456",
                refresh_url="https://custom.com/refresh",
                return_url="https://custom.com/return",
            )

            call_args = mock_stripe.AccountLink.create.call_args
            assert call_args.kwargs["refresh_url"] == "https://custom.com/refresh"
            assert call_args.kwargs["return_url"] == "https://custom.com/return"

    def test_get_connect_account_success(self, mock_settings, mock_stripe):
        """Test successful account retrieval."""
        mock_account = MagicMock()
        mock_account.id = "acct_test_get"
        mock_account.charges_enabled = True
        mock_stripe.Account.retrieve.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = get_connect_account("acct_test_get")

            assert result.id == "acct_test_get"

    def test_update_connect_account_payout_settings(self, mock_settings, mock_stripe):
        """Test updating payout settings."""
        mock_account = MagicMock()
        mock_account.id = "acct_update"
        mock_stripe.Account.modify.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            update_connect_account_payout_settings(
                "acct_update",
                delay_days=14,
                interval="daily",
            )

            call_args = mock_stripe.Account.modify.call_args
            assert call_args.kwargs["settings"]["payouts"]["schedule"]["delay_days"] == 14
            assert call_args.kwargs["settings"]["payouts"]["schedule"]["interval"] == "daily"

    def test_update_connect_account_uses_default_delay(self, mock_settings, mock_stripe):
        """Test update uses settings default delay when not specified."""
        mock_account = MagicMock()
        mock_stripe.Account.modify.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            update_connect_account_payout_settings("acct_default")

            call_args = mock_stripe.Account.modify.call_args
            assert call_args.kwargs["settings"]["payouts"]["schedule"]["delay_days"] == 7


class TestIsConnectAccountReady:
    """Test Connect account readiness checks."""

    def test_account_ready(self, mock_settings, mock_stripe):
        """Test account is ready when charges and payouts enabled."""
        mock_account = MagicMock()
        mock_account.charges_enabled = True
        mock_account.payouts_enabled = True
        mock_account.details_submitted = True
        mock_stripe.Account.retrieve.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            is_ready, message = is_connect_account_ready("acct_ready")

            assert is_ready is True
            assert "ready" in message.lower()

    def test_account_onboarding_incomplete(self, mock_settings, mock_stripe):
        """Test account not ready when onboarding incomplete."""
        mock_account = MagicMock()
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = False
        mock_stripe.Account.retrieve.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            is_ready, message = is_connect_account_ready("acct_incomplete")

            assert is_ready is False
            assert "incomplete" in message.lower()

    def test_account_verification_pending(self, mock_settings, mock_stripe):
        """Test account not ready when verification pending."""
        mock_account = MagicMock()
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = True
        mock_stripe.Account.retrieve.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            is_ready, message = is_connect_account_ready("acct_pending")

            assert is_ready is False
            assert "pending" in message.lower() or "verification" in message.lower()

    def test_account_payouts_disabled(self, mock_settings, mock_stripe):
        """Test account not ready when payouts disabled."""
        mock_account = MagicMock()
        mock_account.charges_enabled = True
        mock_account.payouts_enabled = False
        mock_account.details_submitted = True
        mock_stripe.Account.retrieve.return_value = mock_account

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            is_ready, message = is_connect_account_ready("acct_no_payout")

            assert is_ready is False
            assert "payout" in message.lower() or "incomplete" in message.lower()

    def test_account_not_found(self, mock_settings, mock_stripe):
        """Test handling of non-existent account."""
        mock_stripe.Account.retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such account", param="account"
        )

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            with patch("core.stripe_client.handle_stripe_error") as mock_handler:
                mock_handler.return_value = HTTPException(status_code=404, detail="Not found")

                is_ready, message = is_connect_account_ready("acct_missing")

                assert is_ready is False
                assert "not found" in message.lower()


# =============================================================================
# Test: Transfers
# =============================================================================


class TestCreateTransferToTutor:
    """Test transfer creation to tutors."""

    def test_create_transfer_success(self, mock_settings, mock_stripe):
        """Test successful transfer creation."""
        mock_transfer = MagicMock()
        mock_transfer.id = "tr_test_123"
        mock_stripe.Transfer.create.return_value = mock_transfer

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_transfer_to_tutor(
                amount_cents=4500,
                currency="usd",
                tutor_connect_account_id="acct_tutor",
                booking_id=123,
            )

            assert result.id == "tr_test_123"
            call_args = mock_stripe.Transfer.create.call_args
            assert call_args.kwargs["amount"] == 4500
            assert call_args.kwargs["destination"] == "acct_tutor"

    def test_create_transfer_with_description(self, mock_settings, mock_stripe):
        """Test transfer with custom description."""
        mock_transfer = MagicMock()
        mock_transfer.id = "tr_desc"
        mock_stripe.Transfer.create.return_value = mock_transfer

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_transfer_to_tutor(
                amount_cents=5000,
                currency="eur",
                tutor_connect_account_id="acct_tutor_eu",
                booking_id=456,
                description="Custom payout description",
            )

            call_args = mock_stripe.Transfer.create.call_args
            assert call_args.kwargs["description"] == "Custom payout description"
            assert call_args.kwargs["currency"] == "eur"


# =============================================================================
# Test: Refunds
# =============================================================================


class TestCreateRefund:
    """Test refund creation functionality."""

    def test_create_refund_full_success(self, mock_settings, mock_stripe):
        """Test successful full refund."""
        mock_refund = MagicMock()
        mock_refund.id = "re_test_123"
        mock_refund.amount = 5000
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_refund(
                payment_intent_id="pi_test_123",
                booking_id=1,
            )

            assert isinstance(result, RefundResult)
            assert result.id == "re_test_123"
            assert result.was_existing is False
            assert result.amount == 5000

    def test_create_refund_partial(self, mock_settings, mock_stripe):
        """Test partial refund."""
        mock_refund = MagicMock()
        mock_refund.id = "re_partial"
        mock_refund.amount = 2500
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_refund(
                payment_intent_id="pi_test_partial",
                booking_id=2,
                amount_cents=2500,
            )

            call_args = mock_stripe.Refund.create.call_args
            assert call_args.kwargs["amount"] == 2500

    def test_create_refund_with_reason(self, mock_settings, mock_stripe):
        """Test refund with custom reason."""
        mock_refund = MagicMock()
        mock_refund.id = "re_reason"
        mock_refund.amount = 5000
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            create_refund(
                payment_intent_id="pi_reason",
                booking_id=3,
                reason="duplicate",
            )

            call_args = mock_stripe.Refund.create.call_args
            assert call_args.kwargs["reason"] == "duplicate"

    def test_create_refund_without_booking_id(self, mock_settings, mock_stripe):
        """Test refund without booking_id uses payment_intent for idempotency."""
        mock_refund = MagicMock()
        mock_refund.id = "re_no_booking"
        mock_refund.amount = 3000
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_refund(
                payment_intent_id="pi_no_booking",
                booking_id=None,
            )

            assert result.id == "re_no_booking"

    def test_create_refund_timeout_with_existing_refund(self, mock_settings, mock_stripe):
        """Test refund timeout recovery when refund already exists."""
        # First call times out
        mock_stripe.Refund.create.side_effect = stripe.error.Timeout("Timeout")

        # But refund was actually created
        existing_refund = MagicMock()
        existing_refund.id = "re_existing"
        existing_refund.amount = 5000
        existing_refund.status = "succeeded"

        mock_refunds_list = MagicMock()
        mock_refunds_list.data = [existing_refund]
        mock_stripe.Refund.list.return_value = mock_refunds_list

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)
            mock_breaker.record_failure = MagicMock()

            result = create_refund(
                payment_intent_id="pi_timeout",
                booking_id=10,
            )

            assert result.was_existing is True
            assert result.id == "re_existing"

    def test_create_refund_timeout_no_existing_refund(self, mock_settings, mock_stripe):
        """Test refund timeout with no existing refund raises error."""
        mock_stripe.Refund.create.side_effect = stripe.error.Timeout("Timeout")

        mock_refunds_list = MagicMock()
        mock_refunds_list.data = []
        mock_stripe.Refund.list.return_value = mock_refunds_list

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)
            mock_breaker.record_failure = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                create_refund(
                    payment_intent_id="pi_timeout_fail",
                    booking_id=11,
                )

            assert exc_info.value.status_code == 503

    def test_create_refund_idempotency_conflict(self, mock_settings, mock_stripe):
        """Test handling idempotency conflict by returning existing refund."""
        mock_stripe.Refund.create.side_effect = stripe.error.IdempotencyError(
            "Conflict", code="idempotency_error"
        )

        existing_refund = MagicMock()
        existing_refund.id = "re_idem"
        existing_refund.amount = 5000
        existing_refund.status = "succeeded"

        mock_refunds_list = MagicMock()
        mock_refunds_list.data = [existing_refund]
        mock_stripe.Refund.list.return_value = mock_refunds_list

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_refund(
                payment_intent_id="pi_idem",
                booking_id=12,
            )

            assert result.was_existing is True

    def test_create_refund_already_refunded(self, mock_settings, mock_stripe):
        """Test handling of already-refunded payment."""
        mock_stripe.Refund.create.side_effect = stripe.error.InvalidRequestError(
            "Charge has already been refunded", param="payment_intent"
        )

        existing_refund = MagicMock()
        existing_refund.id = "re_prev"
        existing_refund.amount = 5000
        existing_refund.status = "succeeded"

        mock_refunds_list = MagicMock()
        mock_refunds_list.data = [existing_refund]
        mock_stripe.Refund.list.return_value = mock_refunds_list

        with patch("core.stripe_client.stripe_circuit_breaker") as mock_breaker:
            mock_breaker.call.return_value.__enter__ = MagicMock()
            mock_breaker.call.return_value.__exit__ = MagicMock(return_value=False)

            result = create_refund(
                payment_intent_id="pi_already",
                booking_id=13,
            )

            assert result.was_existing is True


class TestFindExistingRefund:
    """Test _find_existing_refund helper function."""

    def test_find_existing_refund_found(self, mock_stripe):
        """Test finding an existing refund."""
        mock_refund = MagicMock()
        mock_refund.id = "re_found"

        mock_refunds_list = MagicMock()
        mock_refunds_list.data = [mock_refund]
        mock_stripe.Refund.list.return_value = mock_refunds_list

        result = _find_existing_refund(mock_stripe, "pi_test")

        assert result.id == "re_found"

    def test_find_existing_refund_not_found(self, mock_stripe):
        """Test when no existing refund found."""
        mock_refunds_list = MagicMock()
        mock_refunds_list.data = []
        mock_stripe.Refund.list.return_value = mock_refunds_list

        result = _find_existing_refund(mock_stripe, "pi_no_refund")

        assert result is None

    def test_find_existing_refund_error(self, mock_stripe):
        """Test handling of errors when checking for refunds."""
        mock_stripe.Refund.list.side_effect = stripe.error.StripeError("API error")

        result = _find_existing_refund(mock_stripe, "pi_error")

        assert result is None


# =============================================================================
# Test: Webhook Verification
# =============================================================================


class TestVerifyWebhookSignature:
    """Test webhook signature verification."""

    def test_verify_webhook_success(self, mock_settings):
        """Test successful webhook verification."""
        mock_event = MagicMock()
        mock_event.type = "checkout.session.completed"
        mock_event.id = "evt_test_123"

        with patch("core.stripe_client.stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = mock_event

            result = verify_webhook_signature(
                payload=b'{"test": "data"}',
                sig_header="t=123,v1=abc",
            )

            assert result.id == "evt_test_123"

    def test_verify_webhook_no_secret_configured(self):
        """Test webhook verification fails without secret."""
        with patch("core.stripe_client.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = None

            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(
                    payload=b'{"test": "data"}',
                    sig_header="t=123,v1=abc",
                )

            assert exc_info.value.status_code == 503
            assert "not configured" in exc_info.value.detail

    def test_verify_webhook_invalid_signature(self, mock_settings):
        """Test webhook verification fails with invalid signature."""
        with patch("core.stripe_client.stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", sig_header="invalid"
            )

            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(
                    payload=b'{"test": "data"}',
                    sig_header="invalid_sig",
                )

            assert exc_info.value.status_code == 400
            assert "Invalid webhook signature" in exc_info.value.detail

    def test_verify_webhook_invalid_payload(self, mock_settings):
        """Test webhook verification fails with invalid payload."""
        with patch("core.stripe_client.stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = ValueError("Invalid JSON")

            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(
                    payload=b'invalid json',
                    sig_header="t=123,v1=abc",
                )

            assert exc_info.value.status_code == 400
            assert "Invalid webhook payload" in exc_info.value.detail


# =============================================================================
# Test: Amount Formatting
# =============================================================================


class TestFormatAmountForDisplay:
    """Test amount formatting utility."""

    def test_format_usd(self):
        """Test USD formatting."""
        assert format_amount_for_display(5000, "usd") == "$50.00"
        assert format_amount_for_display(99, "usd") == "$0.99"
        assert format_amount_for_display(0, "usd") == "$0.00"
        assert format_amount_for_display(100000, "usd") == "$1000.00"

    def test_format_eur(self):
        """Test EUR formatting."""
        assert format_amount_for_display(5000, "eur") == "\u20ac50.00"
        assert format_amount_for_display(1, "EUR") == "\u20ac0.01"

    def test_format_gbp(self):
        """Test GBP formatting."""
        assert format_amount_for_display(5000, "gbp") == "\u00a350.00"
        assert format_amount_for_display(150, "GBP") == "\u00a31.50"

    def test_format_unknown_currency(self):
        """Test unknown currency formatting."""
        assert format_amount_for_display(5000, "xyz") == "XYZ 50.00"
        assert format_amount_for_display(5000, "jpy") == "JPY 50.00"

    def test_format_case_insensitive(self):
        """Test that currency is case-insensitive."""
        assert format_amount_for_display(5000, "USD") == "$50.00"
        assert format_amount_for_display(5000, "Usd") == "$50.00"

    def test_format_decimal_precision(self):
        """Test that decimal places are always shown."""
        assert format_amount_for_display(1, "usd") == "$0.01"
        assert format_amount_for_display(10, "usd") == "$0.10"
        assert format_amount_for_display(100, "usd") == "$1.00"


# =============================================================================
# Test: RefundResult Class
# =============================================================================


class TestRefundResult:
    """Test RefundResult class."""

    def test_refund_result_properties(self):
        """Test RefundResult exposes refund properties."""
        mock_refund = MagicMock()
        mock_refund.id = "re_test"
        mock_refund.amount = 5000
        mock_refund.status = "succeeded"

        result = RefundResult(refund=mock_refund, was_existing=False)

        assert result.id == "re_test"
        assert result.amount == 5000
        assert result.status == "succeeded"
        assert result.was_existing is False
        assert result.refund == mock_refund

    def test_refund_result_existing_flag(self):
        """Test RefundResult with was_existing flag."""
        mock_refund = MagicMock()
        mock_refund.id = "re_existing"
        mock_refund.amount = 3000
        mock_refund.status = "succeeded"

        result = RefundResult(refund=mock_refund, was_existing=True)

        assert result.was_existing is True
