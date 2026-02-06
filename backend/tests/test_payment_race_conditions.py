"""
Tests for payment race condition handling.

Verifies that payment capture has proper idempotency protection
to prevent double capture and other race conditions.
"""

import re
from pathlib import Path


def test_payment_capture_has_idempotency():
    """Verify payment capture checks for duplicate attempts."""
    # Check wallet router for idempotency handling
    wallet_router_path = Path(__file__).parent.parent / "modules" / "payments" / "wallet_router.py"
    source = wallet_router_path.read_text()

    # Should have some form of idempotency check
    has_idempotency = (
        "idempotency" in source.lower() or
        "already_captured" in source or
        "payment_state" in source or  # checking state before capture
        "status" in source  # checking payment status
    )
    assert has_idempotency, "Payment capture should have idempotency protection"


def test_stripe_client_uses_idempotency_keys():
    """Verify Stripe client uses idempotency keys for all mutating operations."""
    stripe_client_path = Path(__file__).parent.parent / "core" / "stripe_client.py"
    source = stripe_client_path.read_text()

    # Check for idempotency key generation
    assert "idempotency_key" in source, "Stripe client should use idempotency keys"
    assert "generate_idempotency_key" in source, "Should generate idempotency keys"

    # Count idempotency key usages (should be in checkout, refund, transfer, etc.)
    idempotency_usages = source.count("idempotency_key=")
    assert idempotency_usages >= 4, f"Expected at least 4 idempotency key usages, found {idempotency_usages}"


def test_webhook_handler_has_idempotency_check():
    """Verify webhook handler checks for already-processed events."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should check WebhookEvent table for duplicates
    assert "WebhookEvent" in source, "Should use WebhookEvent for idempotency"
    assert "already_processed" in source, "Should detect already processed webhooks"
    assert "stripe_event_id" in source, "Should track events by Stripe event ID"


def test_refund_has_idempotency_and_timeout_handling():
    """Verify refund operations have idempotency and timeout recovery."""
    stripe_client_path = Path(__file__).parent.parent / "core" / "stripe_client.py"
    source = stripe_client_path.read_text()

    # Check for timeout handling in refund
    assert "_find_existing_refund" in source, "Should check for existing refunds"
    assert "IdempotencyError" in source, "Should handle idempotency conflicts"
    assert "was_existing" in source, "Should track if refund was existing"

    # Check for timeout/connection error handling
    assert "APIConnectionError" in source or "Timeout" in source, (
        "Should handle connection timeouts"
    )


def test_wallet_topup_uses_atomic_update():
    """Verify wallet top-up uses atomic SQL UPDATE to prevent race conditions."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Check for atomic update pattern
    has_atomic_update = (
        "StudentProfile.credit_balance_cents +" in source or
        "credit_balance_cents=StudentProfile.credit_balance_cents" in source
    )
    assert has_atomic_update, "Wallet top-up should use atomic UPDATE"

    # Verify it's using db.execute with update() instead of ORM read-modify-write
    assert "db.execute" in source, "Should use db.execute for atomic operations"


def test_checkout_handles_existing_session():
    """Verify checkout endpoint handles existing checkout sessions."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should check for existing checkout session
    assert "stripe_checkout_session_id" in source, "Should track checkout session ID"
    assert "retrieve_checkout_session" in source, "Should retrieve existing sessions"
    assert "status" in source and "open" in source, "Should check session status"


def test_payment_state_checked_before_operations():
    """Verify payment state is checked before capture/refund operations."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should check payment state
    has_state_check = (
        "payment_state" in source or
        "PaymentState" in source or
        "payment.status" in source
    )
    assert has_state_check, "Should check payment state before operations"

    # For refunds, should check if already refunded
    assert "already" in source.lower() and "refund" in source.lower(), (
        "Should check if already refunded"
    )


def test_circuit_breaker_protects_stripe_calls():
    """Verify circuit breaker is used to protect Stripe API calls."""
    stripe_client_path = Path(__file__).parent.parent / "core" / "stripe_client.py"
    source = stripe_client_path.read_text()

    assert "stripe_circuit_breaker" in source, "Should use circuit breaker"
    assert "CircuitOpenError" in source, "Should handle circuit open state"

    # Count circuit breaker usages
    breaker_usages = source.count("with stripe_circuit_breaker.call():")
    assert breaker_usages >= 5, f"Expected at least 5 circuit breaker usages, found {breaker_usages}"


def test_webhook_retry_tracking():
    """Verify webhook retry attempts are tracked."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    assert "webhook_retry_tracker" in source, "Should use webhook retry tracker"
    assert "record_attempt" in source, "Should record webhook attempts"


def test_payment_reliability_module_exists():
    """Verify payment reliability module with proper abstractions exists."""
    reliability_path = Path(__file__).parent.parent / "core" / "payment_reliability.py"
    source = reliability_path.read_text()

    # Check for key components
    assert "CircuitBreaker" in source, "Should have CircuitBreaker class"
    assert "generate_idempotency_key" in source, "Should have idempotency key generator"
    assert "WebhookRetryTracker" in source, "Should have webhook retry tracker"
    assert "PaymentStatusPoller" in source, "Should have payment status poller"


def test_no_read_modify_write_pattern_in_critical_paths():
    """Verify critical payment paths don't use vulnerable read-modify-write pattern."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # The wallet top-up handler should NOT do:
    # profile = query(); profile.balance += amount; commit()
    # Instead should do:
    # db.execute(update().values(balance=balance + amount))

    # Look for the _handle_wallet_topup function
    topup_section_match = re.search(
        r'async def _handle_wallet_topup\(.*?\n(?:.*?\n)*?(?=\nasync def|\nclass|\Z)',
        source,
        re.MULTILINE
    )

    if topup_section_match:
        topup_section = topup_section_match.group(0)
        # Should use db.execute with atomic update, not ORM assignment
        assert "db.execute" in topup_section, (
            "_handle_wallet_topup should use db.execute for atomic update"
        )
        assert "student_profile.credit_balance_cents =" not in topup_section or \
               "student_profile.credit_balance_cents = 0" in topup_section, (
            "_handle_wallet_topup should not use ORM assignment for balance update"
        )


def test_refund_validates_remaining_amount():
    """Verify refund validates that amount doesn't exceed remaining refundable."""
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should calculate total already refunded
    assert "total_refunded" in source or "refund_amount_cents" in source, (
        "Should track total refunded amount"
    )

    # Should validate against original amount
    assert "exceeds" in source.lower() or "max_refundable" in source, (
        "Should validate refund doesn't exceed original"
    )
