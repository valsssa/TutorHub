"""
Payment Reliability Module

Provides circuit breaker, idempotency, and retry handling for Stripe operations.

Features:
- Circuit breaker pattern for Stripe API calls
- Idempotency key generation and tracking
- Webhook retry tracking
- Payment status polling for timeout recovery
- Graceful degradation when Stripe is unavailable
"""

import hashlib
import logging
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    timeout_seconds: int = 60  # Time before trying half-open
    excluded_exceptions: tuple = ()  # Exceptions that don't count as failures


@dataclass
class CircuitBreakerState:
    """Internal state for circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class CircuitBreaker:
    """
    Circuit breaker implementation for Stripe API calls.

    Prevents cascading failures by temporarily disabling calls to a
    failing service.

    Usage:
        stripe_breaker = CircuitBreaker("stripe")

        @stripe_breaker
        def create_payment():
            return stripe.PaymentIntent.create(...)

        # Or as context manager:
        with stripe_breaker.call():
            stripe.PaymentIntent.create(...)
    """

    _instances: dict[str, "CircuitBreaker"] = {}

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()

    @classmethod
    def get_instance(cls, name: str) -> "CircuitBreaker":
        """Get or create a circuit breaker instance by name."""
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state.state

    @property
    def is_available(self) -> bool:
        """Check if the circuit allows requests."""
        with self._state.lock:
            if self._state.state == CircuitState.CLOSED:
                return True

            if self._state.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if self._state.last_failure_time is not None:
                    elapsed = time.time() - self._state.last_failure_time
                    if elapsed >= self.config.timeout_seconds:
                        self._state.state = CircuitState.HALF_OPEN
                        self._state.success_count = 0
                        logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                        return True
                return False

            # HALF_OPEN allows requests
            return True

    def record_success(self) -> None:
        """Record a successful call."""
        with self._state.lock:
            if self._state.state == CircuitState.HALF_OPEN:
                self._state.success_count += 1
                if self._state.success_count >= self.config.success_threshold:
                    self._state.state = CircuitState.CLOSED
                    self._state.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery")

            elif self._state.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._state.failure_count = 0

    def record_failure(self, exception: BaseException) -> None:
        """Record a failed call."""
        # Check if this exception should be excluded
        if isinstance(exception, self.config.excluded_exceptions):
            return

        with self._state.lock:
            self._state.failure_count += 1
            self._state.last_failure_time = time.time()

            if self._state.state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens the circuit
                self._state.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' reopened after failure in HALF_OPEN: {exception}"
                )

            elif self._state.state == CircuitState.CLOSED:
                if self._state.failure_count >= self.config.failure_threshold:
                    self._state.state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker '{self.name}' OPENED after {self._state.failure_count} failures"
                    )

    @contextmanager
    def call(self):
        """Context manager for protected calls."""
        if not self.is_available:
            raise CircuitOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service temporarily unavailable."
            )

        try:
            yield
            self.record_success()
        except Exception as e:
            self.record_failure(e)
            raise

    def __call__(self, func):
        """Decorator for protected functions."""

        def wrapper(*args, **kwargs):
            with self.call():
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._state.lock:
            self._state.state = CircuitState.CLOSED
            self._state.failure_count = 0
            self._state.success_count = 0
            self._state.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        with self._state.lock:
            return {
                "name": self.name,
                "state": self._state.state.value,
                "failure_count": self._state.failure_count,
                "success_count": self._state.success_count,
                "last_failure_time": self._state.last_failure_time,
                "is_available": self.is_available,
            }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


# Global Stripe circuit breaker instance
stripe_circuit_breaker = CircuitBreaker.get_instance("stripe")


def generate_idempotency_key(
    operation: str,
    *args: Any,
    user_id: int | None = None,
    booking_id: int | None = None,
) -> str:
    """
    Generate a deterministic idempotency key for Stripe operations.

    The key is based on:
    - Operation type (e.g., "checkout", "refund")
    - Relevant IDs (user, booking, etc.)
    - Additional arguments

    This ensures the same operation with same parameters always
    generates the same key, preventing duplicate charges.

    Args:
        operation: Type of operation (e.g., "checkout_session")
        *args: Additional values to include in key
        user_id: Optional user ID
        booking_id: Optional booking ID

    Returns:
        A deterministic idempotency key string
    """
    components = [operation]

    if user_id is not None:
        components.append(f"user:{user_id}")

    if booking_id is not None:
        components.append(f"booking:{booking_id}")

    for arg in args:
        components.append(str(arg))

    # Create deterministic hash
    key_string = "|".join(components)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]

    return f"idem_{operation}_{key_hash}"


def generate_unique_idempotency_key(prefix: str = "op") -> str:
    """
    Generate a unique idempotency key for one-time operations.

    Use this when you need a unique key that won't repeat,
    but still want idempotency protection for retries.

    Args:
        prefix: Optional prefix for the key

    Returns:
        A unique idempotency key
    """
    return f"idem_{prefix}_{uuid.uuid4().hex}"


@dataclass
class WebhookRetryInfo:
    """Information about webhook retry attempts."""

    event_id: str
    event_type: str
    first_received_at: datetime
    last_received_at: datetime
    attempt_count: int
    processed: bool
    error_message: str | None = None


class WebhookRetryTracker:
    """
    Track webhook retry attempts for monitoring and debugging.

    Stripe may retry webhooks multiple times. This tracker helps
    identify problematic webhooks and understand retry patterns.
    """

    def __init__(self, max_entries: int = 1000):
        self._entries: dict[str, WebhookRetryInfo] = {}
        self._max_entries = max_entries
        self._lock = threading.Lock()

    def record_attempt(
        self,
        event_id: str,
        event_type: str,
        processed: bool = False,
        error_message: str | None = None,
    ) -> WebhookRetryInfo:
        """Record a webhook attempt."""
        now = datetime.now(UTC)

        with self._lock:
            if event_id in self._entries:
                entry = self._entries[event_id]
                entry.last_received_at = now
                entry.attempt_count += 1
                entry.processed = processed or entry.processed
                if error_message:
                    entry.error_message = error_message
            else:
                # Clean up old entries if we're at capacity
                if len(self._entries) >= self._max_entries:
                    self._cleanup_old_entries()

                entry = WebhookRetryInfo(
                    event_id=event_id,
                    event_type=event_type,
                    first_received_at=now,
                    last_received_at=now,
                    attempt_count=1,
                    processed=processed,
                    error_message=error_message,
                )
                self._entries[event_id] = entry

            return entry

    def get_retry_info(self, event_id: str) -> WebhookRetryInfo | None:
        """Get retry info for an event."""
        with self._lock:
            return self._entries.get(event_id)

    def get_problematic_events(self, min_attempts: int = 3) -> list[WebhookRetryInfo]:
        """Get events that have been retried multiple times."""
        with self._lock:
            return [
                entry
                for entry in self._entries.values()
                if entry.attempt_count >= min_attempts and not entry.processed
            ]

    def get_stats(self) -> dict[str, Any]:
        """Get webhook retry statistics."""
        with self._lock:
            total = len(self._entries)
            processed = sum(1 for e in self._entries.values() if e.processed)
            retried = sum(1 for e in self._entries.values() if e.attempt_count > 1)
            max_attempts = max(
                (e.attempt_count for e in self._entries.values()),
                default=0,
            )

            return {
                "total_events": total,
                "processed_events": processed,
                "failed_events": total - processed,
                "retried_events": retried,
                "max_attempts": max_attempts,
            }

    def _cleanup_old_entries(self) -> None:
        """Remove old entries to prevent memory growth."""
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        keys_to_remove = [
            key
            for key, entry in self._entries.items()
            if entry.last_received_at < cutoff
        ]
        for key in keys_to_remove:
            del self._entries[key]


# Global webhook retry tracker
webhook_retry_tracker = WebhookRetryTracker()


@dataclass
class PaymentStatusInfo:
    """Payment status information."""

    payment_intent_id: str | None
    checkout_session_id: str | None
    status: str
    amount_cents: int
    currency: str
    paid: bool
    refunded: bool
    last_checked: datetime
    error: str | None = None


class PaymentStatusPoller:
    """
    Poll Stripe for payment status when webhooks may have been missed.

    Use this for:
    - Timeout recovery (webhook didn't arrive)
    - Manual status checks
    - Payment reconciliation
    """

    def __init__(self):
        self._cache: dict[str, PaymentStatusInfo] = {}
        self._cache_ttl = 60  # seconds
        self._lock = threading.Lock()

    def check_checkout_session(self, session_id: str) -> PaymentStatusInfo:
        """
        Check the status of a checkout session.

        Returns cached result if available and fresh.
        """
        import stripe

        from core.config import settings

        cache_key = f"session:{session_id}"

        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                age = (datetime.now(UTC) - cached.last_checked).total_seconds()
                if age < self._cache_ttl:
                    return cached

        # Fetch from Stripe
        try:
            if not settings.STRIPE_SECRET_KEY:
                raise PaymentServiceUnavailable("Stripe not configured")

            stripe.api_key = settings.STRIPE_SECRET_KEY

            with stripe_circuit_breaker.call():
                session = stripe.checkout.Session.retrieve(session_id)

            status_info = PaymentStatusInfo(
                payment_intent_id=session.payment_intent,
                checkout_session_id=session_id,
                status=session.payment_status or "unknown",
                amount_cents=session.amount_total or 0,
                currency=session.currency or "usd",
                paid=session.payment_status == "paid",
                refunded=False,  # Check payment intent for refund status
                last_checked=datetime.now(UTC),
            )

            with self._lock:
                self._cache[cache_key] = status_info

            return status_info

        except stripe.error.StripeError as e:
            logger.error(f"Error checking checkout session {session_id}: {e}")
            return PaymentStatusInfo(
                payment_intent_id=None,
                checkout_session_id=session_id,
                status="error",
                amount_cents=0,
                currency="usd",
                paid=False,
                refunded=False,
                last_checked=datetime.now(UTC),
                error=str(e),
            )
        except CircuitOpenError:
            logger.warning(f"Circuit breaker open, cannot check session {session_id}")
            raise PaymentServiceUnavailable("Payment service temporarily unavailable")

    def check_payment_intent(self, payment_intent_id: str) -> PaymentStatusInfo:
        """Check the status of a payment intent."""
        import stripe

        from core.config import settings

        cache_key = f"intent:{payment_intent_id}"

        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                age = (datetime.now(UTC) - cached.last_checked).total_seconds()
                if age < self._cache_ttl:
                    return cached

        try:
            if not settings.STRIPE_SECRET_KEY:
                raise PaymentServiceUnavailable("Stripe not configured")

            stripe.api_key = settings.STRIPE_SECRET_KEY

            with stripe_circuit_breaker.call():
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Check if refunded
            refunded = False
            if intent.charges and intent.charges.data:
                charge = intent.charges.data[0]
                refunded = charge.refunded

            status_info = PaymentStatusInfo(
                payment_intent_id=payment_intent_id,
                checkout_session_id=None,
                status=intent.status,
                amount_cents=intent.amount,
                currency=intent.currency,
                paid=intent.status == "succeeded",
                refunded=refunded,
                last_checked=datetime.now(UTC),
            )

            with self._lock:
                self._cache[cache_key] = status_info

            return status_info

        except stripe.error.StripeError as e:
            logger.error(f"Error checking payment intent {payment_intent_id}: {e}")
            return PaymentStatusInfo(
                payment_intent_id=payment_intent_id,
                checkout_session_id=None,
                status="error",
                amount_cents=0,
                currency="usd",
                paid=False,
                refunded=False,
                last_checked=datetime.now(UTC),
                error=str(e),
            )
        except CircuitOpenError:
            logger.warning(f"Circuit breaker open, cannot check intent {payment_intent_id}")
            raise PaymentServiceUnavailable("Payment service temporarily unavailable")


# Global payment status poller
payment_status_poller = PaymentStatusPoller()


class PaymentServiceUnavailable(Exception):
    """Raised when payment service is unavailable."""

    pass


def handle_stripe_error(error: Exception) -> HTTPException:
    """
    Convert Stripe errors to appropriate HTTP exceptions.

    Provides user-friendly messages while logging technical details.
    """
    import stripe

    error_messages = {
        stripe.error.CardError: "Your card was declined. Please try a different payment method.",
        stripe.error.RateLimitError: "Payment service is busy. Please try again in a moment.",
        stripe.error.InvalidRequestError: "Invalid payment request. Please contact support.",
        stripe.error.AuthenticationError: "Payment configuration error. Please contact support.",
        stripe.error.APIConnectionError: "Could not connect to payment service. Please try again.",
        stripe.error.StripeError: "Payment processing error. Please try again.",
    }

    for error_type, message in error_messages.items():
        if isinstance(error, error_type):
            logger.error(f"Stripe error: {type(error).__name__}: {error}")
            return HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            )

    if isinstance(error, CircuitOpenError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again later.",
        )

    if isinstance(error, PaymentServiceUnavailable):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error) or "Payment service unavailable",
        )

    logger.error(f"Unknown payment error: {type(error).__name__}: {error}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred processing your payment.",
    )


def get_payment_reliability_status() -> dict[str, Any]:
    """Get overall payment reliability status for monitoring."""
    return {
        "circuit_breaker": stripe_circuit_breaker.get_status(),
        "webhook_tracker": webhook_retry_tracker.get_stats(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
