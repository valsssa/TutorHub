"""
Tests for Payment Reliability Module

Tests circuit breaker, idempotency keys, webhook retry tracking,
and payment status polling functionality.
"""

import time
from datetime import datetime

from core.datetime_utils import utc_now
from unittest.mock import patch

import pytest

from backend.core.payment_reliability import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    PaymentStatusInfo,
    PaymentStatusPoller,
    WebhookRetryTracker,
    generate_idempotency_key,
    generate_unique_idempotency_key,
    get_payment_reliability_status,
    handle_stripe_error,
    stripe_circuit_breaker,
    webhook_retry_tracker,
)


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""

    def test_initial_state_is_closed(self):
        """Circuit breaker starts in closed state."""
        breaker = CircuitBreaker("test_initial")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_available is True

    def test_opens_after_failure_threshold(self):
        """Circuit opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_threshold", config)

        # Record failures
        for i in range(3):
            breaker.record_failure(Exception(f"Error {i}"))

        assert breaker.state == CircuitState.OPEN
        assert breaker.is_available is False

    def test_success_resets_failure_count(self):
        """Success resets failure count in closed state."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_reset", config)

        # Record 2 failures
        breaker.record_failure(Exception("Error 1"))
        breaker.record_failure(Exception("Error 2"))

        # Record success - should reset
        breaker.record_success()

        # Record 2 more failures - shouldn't open yet
        breaker.record_failure(Exception("Error 3"))
        breaker.record_failure(Exception("Error 4"))

        assert breaker.state == CircuitState.CLOSED

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=1,
        )
        breaker = CircuitBreaker("test_half_open", config)

        # Open the circuit
        breaker.record_failure(Exception("Error 1"))
        breaker.record_failure(Exception("Error 2"))
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Check availability - should transition to half-open
        assert breaker.is_available is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold_in_half_open(self):
        """Circuit closes after success threshold in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0,  # Immediate transition
        )
        breaker = CircuitBreaker("test_close", config)

        # Open and transition to half-open
        breaker.record_failure(Exception("Error 1"))
        breaker.record_failure(Exception("Error 2"))
        _ = breaker.is_available  # Trigger transition

        # Record successes
        breaker.record_success()
        breaker.record_success()

        assert breaker.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Circuit reopens on any failure in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=0,
        )
        breaker = CircuitBreaker("test_reopen", config)

        # Open and transition to half-open
        breaker.record_failure(Exception("Error 1"))
        breaker.record_failure(Exception("Error 2"))
        _ = breaker.is_available  # Trigger transition
        assert breaker.state == CircuitState.HALF_OPEN

        # Single failure reopens
        breaker.record_failure(Exception("Error 3"))
        assert breaker.state == CircuitState.OPEN

    def test_context_manager_records_success(self):
        """Context manager records success on normal exit."""
        breaker = CircuitBreaker("test_ctx_success")

        with breaker.call():
            pass  # Successful operation

        assert breaker._state.failure_count == 0

    def test_context_manager_records_failure(self):
        """Context manager records failure on exception."""
        breaker = CircuitBreaker("test_ctx_failure")

        with pytest.raises(ValueError), breaker.call():
            raise ValueError("Test error")

        assert breaker._state.failure_count == 1

    def test_context_manager_raises_when_open(self):
        """Context manager raises CircuitOpenError when open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test_ctx_open", config)

        breaker.record_failure(Exception("Error"))

        with pytest.raises(CircuitOpenError), breaker.call():
            pass

    def test_decorator_protects_function(self):
        """Decorator protects function with circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_decorator", config)

        call_count = 0

        @breaker
        def protected_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Error")
            return "success"

        # First two calls fail
        with pytest.raises(ValueError):
            protected_function()
        with pytest.raises(ValueError):
            protected_function()

        # Circuit is now open
        with pytest.raises(CircuitOpenError):
            protected_function()

    def test_excluded_exceptions_not_counted(self):
        """Excluded exceptions don't count as failures."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            excluded_exceptions=(ValueError,),
        )
        breaker = CircuitBreaker("test_excluded", config)

        # ValueError should not count
        breaker.record_failure(ValueError("Excluded"))
        breaker.record_failure(ValueError("Excluded"))
        breaker.record_failure(ValueError("Excluded"))

        assert breaker.state == CircuitState.CLOSED

        # RuntimeError should count
        breaker.record_failure(RuntimeError("Counted"))
        breaker.record_failure(RuntimeError("Counted"))

        assert breaker.state == CircuitState.OPEN

    def test_manual_reset(self):
        """Circuit can be manually reset."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test_manual_reset", config)

        breaker.record_failure(Exception("Error"))
        assert breaker.state == CircuitState.OPEN

        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._state.failure_count == 0

    def test_get_status(self):
        """Get status returns correct information."""
        breaker = CircuitBreaker("test_status")
        breaker.record_failure(Exception("Error"))

        status = breaker.get_status()

        assert status["name"] == "test_status"
        assert status["state"] == "closed"
        assert status["failure_count"] == 1
        assert status["is_available"] is True

    def test_get_instance_returns_same_instance(self):
        """get_instance returns the same instance for same name."""
        breaker1 = CircuitBreaker.get_instance("shared")
        breaker2 = CircuitBreaker.get_instance("shared")

        assert breaker1 is breaker2


class TestIdempotencyKeys:
    """Test idempotency key generation."""

    def test_deterministic_key_generation(self):
        """Same inputs produce same key."""
        key1 = generate_idempotency_key("checkout", 1000, "usd", booking_id=123)
        key2 = generate_idempotency_key("checkout", 1000, "usd", booking_id=123)

        assert key1 == key2

    def test_different_inputs_produce_different_keys(self):
        """Different inputs produce different keys."""
        key1 = generate_idempotency_key("checkout", 1000, "usd", booking_id=123)
        key2 = generate_idempotency_key("checkout", 2000, "usd", booking_id=123)

        assert key1 != key2

    def test_key_format(self):
        """Key has expected format."""
        key = generate_idempotency_key("checkout", booking_id=123)

        assert key.startswith("idem_checkout_")
        assert len(key) > 20

    def test_unique_key_generation(self):
        """Unique keys are different each time."""
        key1 = generate_unique_idempotency_key("refund")
        key2 = generate_unique_idempotency_key("refund")

        assert key1 != key2
        assert key1.startswith("idem_refund_")


class TestWebhookRetryTracker:
    """Test webhook retry tracking."""

    def test_records_first_attempt(self):
        """Records first webhook attempt."""
        tracker = WebhookRetryTracker()

        info = tracker.record_attempt(
            event_id="evt_123",
            event_type="checkout.session.completed",
        )

        assert info.event_id == "evt_123"
        assert info.event_type == "checkout.session.completed"
        assert info.attempt_count == 1
        assert info.processed is False

    def test_increments_attempt_count(self):
        """Increments attempt count on subsequent attempts."""
        tracker = WebhookRetryTracker()

        tracker.record_attempt("evt_123", "checkout.session.completed")
        info = tracker.record_attempt("evt_123", "checkout.session.completed")

        assert info.attempt_count == 2

    def test_marks_as_processed(self):
        """Marks event as processed."""
        tracker = WebhookRetryTracker()

        tracker.record_attempt("evt_123", "checkout.session.completed")
        info = tracker.record_attempt(
            "evt_123",
            "checkout.session.completed",
            processed=True,
        )

        assert info.processed is True

    def test_records_error_message(self):
        """Records error message."""
        tracker = WebhookRetryTracker()

        info = tracker.record_attempt(
            "evt_123",
            "checkout.session.completed",
            error_message="Database error",
        )

        assert info.error_message == "Database error"

    def test_get_retry_info(self):
        """Gets retry info by event ID."""
        tracker = WebhookRetryTracker()

        tracker.record_attempt("evt_123", "checkout.session.completed")

        info = tracker.get_retry_info("evt_123")
        assert info is not None
        assert info.event_id == "evt_123"

        assert tracker.get_retry_info("evt_nonexistent") is None

    def test_get_problematic_events(self):
        """Gets events with multiple retry attempts."""
        tracker = WebhookRetryTracker()

        # Add an event with 3 attempts (not processed)
        for _ in range(3):
            tracker.record_attempt("evt_problem", "payment_intent.failed")

        # Add an event with 1 attempt
        tracker.record_attempt("evt_ok", "checkout.session.completed")

        # Add a processed event with many attempts
        for _ in range(5):
            tracker.record_attempt(
                "evt_processed",
                "charge.refunded",
                processed=True,
            )

        problematic = tracker.get_problematic_events(min_attempts=3)

        assert len(problematic) == 1
        assert problematic[0].event_id == "evt_problem"

    def test_get_stats(self):
        """Gets webhook statistics."""
        tracker = WebhookRetryTracker()

        tracker.record_attempt("evt_1", "type_1", processed=True)
        tracker.record_attempt("evt_2", "type_2", processed=False)
        tracker.record_attempt("evt_2", "type_2", processed=False)  # Retry

        stats = tracker.get_stats()

        assert stats["total_events"] == 2
        assert stats["processed_events"] == 1
        assert stats["failed_events"] == 1
        assert stats["retried_events"] == 1
        assert stats["max_attempts"] == 2

    def test_max_entries_cleanup(self):
        """Cleans up old entries when at capacity."""
        tracker = WebhookRetryTracker(max_entries=5)

        # Add 5 entries
        for i in range(5):
            tracker.record_attempt(f"evt_{i}", "type")

        assert len(tracker._entries) == 5

        # Add one more - should trigger cleanup
        tracker.record_attempt("evt_new", "type")

        # Should still have at most max_entries
        assert len(tracker._entries) <= 5


class TestPaymentStatusPoller:
    """Test payment status polling."""

    def test_caches_results(self):
        """Caches results for TTL period."""
        poller = PaymentStatusPoller()
        poller._cache_ttl = 60

        # Manually add to cache
        cached = PaymentStatusInfo(
            payment_intent_id="pi_123",
            checkout_session_id="cs_123",
            status="paid",
            amount_cents=1000,
            currency="usd",
            paid=True,
            refunded=False,
            last_checked=utc_now(),
        )
        poller._cache["session:cs_123"] = cached

        # Should return cached result without calling Stripe
        with patch("backend.core.payment_reliability.stripe") as mock_stripe:
            result = poller.check_checkout_session("cs_123")
            mock_stripe.checkout.Session.retrieve.assert_not_called()

        assert result.status == "paid"
        assert result.paid is True


class TestHandleStripeError:
    """Test Stripe error handling."""

    def test_handles_card_error(self):
        """Handles CardError with user-friendly message."""
        import stripe

        error = stripe.error.CardError(
            message="Your card was declined",
            param="card",
            code="card_declined",
        )

        exc = handle_stripe_error(error)

        assert exc.status_code == 502
        assert "declined" in exc.detail.lower()

    def test_handles_rate_limit_error(self):
        """Handles RateLimitError."""
        import stripe

        error = stripe.error.RateLimitError(message="Too many requests")

        exc = handle_stripe_error(error)

        assert exc.status_code == 502
        assert "busy" in exc.detail.lower()

    def test_handles_circuit_open_error(self):
        """Handles CircuitOpenError."""
        error = CircuitOpenError("Circuit open")

        exc = handle_stripe_error(error)

        assert exc.status_code == 503
        assert "temporarily unavailable" in exc.detail.lower()


class TestReliabilityStatus:
    """Test overall reliability status."""

    def test_returns_status_dict(self):
        """Returns status dictionary with all components."""
        status = get_payment_reliability_status()

        assert "circuit_breaker" in status
        assert "webhook_tracker" in status
        assert "timestamp" in status

        assert "state" in status["circuit_breaker"]
        assert "total_events" in status["webhook_tracker"]


class TestGlobalInstances:
    """Test global singleton instances."""

    def test_stripe_circuit_breaker_exists(self):
        """Global Stripe circuit breaker is available."""
        assert stripe_circuit_breaker is not None
        assert stripe_circuit_breaker.name == "stripe"

    def test_webhook_retry_tracker_exists(self):
        """Global webhook retry tracker is available."""
        assert webhook_retry_tracker is not None
