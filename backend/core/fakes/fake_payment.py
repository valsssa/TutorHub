"""
Fake Payment - In-memory implementation of PaymentPort for testing.

Provides configurable success/failure scenarios and transaction history
for test assertions.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid

from core.ports.payment import (
    CheckoutSessionResult,
    ConnectAccountResult,
    PaymentResult,
    PaymentStatus,
    RefundResult,
    WebhookVerificationResult,
)


@dataclass
class FakePaymentCall:
    """Record of a payment method call."""

    method: str
    timestamp: datetime
    args: dict[str, Any]
    result: Any


@dataclass
class FakePayment:
    """
    In-memory fake implementation of PaymentPort for testing.

    Features:
    - Tracks all method calls for assertions
    - Configurable success/failure modes
    - Simulated payment/refund tracking
    """

    calls: list[FakePaymentCall] = field(default_factory=list)
    should_fail: bool = False
    failure_message: str = "Simulated payment failure"

    # Simulated data stores
    checkout_sessions: dict[str, dict] = field(default_factory=dict)
    refunds: dict[str, dict] = field(default_factory=dict)
    connect_accounts: dict[str, dict] = field(default_factory=dict)
    transfers: list[dict] = field(default_factory=list)

    def _record_call(self, method: str, args: dict, result: Any) -> None:
        """Record a method call for assertions."""
        self.calls.append(
            FakePaymentCall(
                method=method,
                timestamp=datetime.now(UTC),
                args=args,
                result=result,
            )
        )

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        metadata: dict[str, Any] | None = None,
        booking_id: int | None = None,
        tutor_connect_account_id: str | None = None,
        platform_fee_cents: int = 0,
    ) -> CheckoutSessionResult:
        """Create a fake checkout session."""
        args = {
            "amount_cents": amount_cents,
            "currency": currency,
            "description": description,
            "booking_id": booking_id,
        }

        if self.should_fail:
            result = CheckoutSessionResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            session_id = f"cs_test_{uuid.uuid4().hex[:16]}"
            self.checkout_sessions[session_id] = {
                "id": session_id,
                "amount_cents": amount_cents,
                "currency": currency,
                "status": "open",
                "payment_status": "unpaid",
                "metadata": metadata or {},
                "booking_id": booking_id,
            }
            result = CheckoutSessionResult(
                success=True,
                session_id=session_id,
                checkout_url=f"https://checkout.fake.com/pay/{session_id}",
            )

        self._record_call("create_checkout_session", args, result)
        return result

    def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve a fake checkout session."""
        session = self.checkout_sessions.get(session_id, {})
        self._record_call("retrieve_checkout_session", {"session_id": session_id}, session)
        return session

    def create_refund(
        self,
        *,
        payment_intent_id: str,
        amount_cents: int | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RefundResult:
        """Process a fake refund."""
        args = {
            "payment_intent_id": payment_intent_id,
            "amount_cents": amount_cents,
            "reason": reason,
        }

        if self.should_fail:
            result = RefundResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            refund_id = f"re_test_{uuid.uuid4().hex[:16]}"
            self.refunds[refund_id] = {
                "id": refund_id,
                "payment_intent_id": payment_intent_id,
                "amount_cents": amount_cents,
                "status": "succeeded",
            }
            result = RefundResult(
                success=True,
                refund_id=refund_id,
                amount_cents=amount_cents or 0,
                status="succeeded",
            )

        self._record_call("create_refund", args, result)
        return result

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> WebhookVerificationResult:
        """Verify a fake webhook."""
        args = {"payload_length": len(payload), "signature": signature[:20]}

        if self.should_fail:
            result = WebhookVerificationResult(
                valid=False,
                error_message="Invalid signature",
            )
        else:
            result = WebhookVerificationResult(
                valid=True,
                event_type="checkout.session.completed",
                event_id=f"evt_test_{uuid.uuid4().hex[:16]}",
                payload={"type": "checkout.session.completed"},
            )

        self._record_call("verify_webhook", args, result)
        return result

    def create_connect_account(
        self,
        *,
        user_id: int,
        email: str,
        country: str = "US",
    ) -> ConnectAccountResult:
        """Create a fake Connect account."""
        args = {"user_id": user_id, "email": email, "country": country}

        if self.should_fail:
            result = ConnectAccountResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            account_id = f"acct_test_{uuid.uuid4().hex[:16]}"
            self.connect_accounts[account_id] = {
                "id": account_id,
                "user_id": user_id,
                "email": email,
                "country": country,
                "charges_enabled": False,
                "payouts_enabled": False,
            }
            result = ConnectAccountResult(
                success=True,
                account_id=account_id,
            )

        self._record_call("create_connect_account", args, result)
        return result

    def create_connect_onboarding_link(
        self,
        account_id: str,
        *,
        refresh_url: str,
        return_url: str,
    ) -> ConnectAccountResult:
        """Create a fake onboarding link."""
        args = {"account_id": account_id}

        if self.should_fail or account_id not in self.connect_accounts:
            result = ConnectAccountResult(
                success=False,
                error_message=self.failure_message if self.should_fail else "Account not found",
            )
        else:
            result = ConnectAccountResult(
                success=True,
                account_id=account_id,
                onboarding_url=f"https://connect.fake.com/onboard/{account_id}",
            )

        self._record_call("create_connect_onboarding_link", args, result)
        return result

    def get_connect_account_status(self, account_id: str) -> ConnectAccountResult:
        """Get fake Connect account status."""
        args = {"account_id": account_id}

        if account_id not in self.connect_accounts:
            result = ConnectAccountResult(
                success=False,
                error_message="Account not found",
            )
        else:
            acct = self.connect_accounts[account_id]
            result = ConnectAccountResult(
                success=True,
                account_id=account_id,
                is_ready=acct.get("charges_enabled") and acct.get("payouts_enabled"),
                charges_enabled=acct.get("charges_enabled", False),
                payouts_enabled=acct.get("payouts_enabled", False),
            )

        self._record_call("get_connect_account_status", args, result)
        return result

    def create_transfer(
        self,
        *,
        amount_cents: int,
        currency: str,
        destination_account_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Create a fake transfer."""
        args = {
            "amount_cents": amount_cents,
            "currency": currency,
            "destination_account_id": destination_account_id,
        }

        if self.should_fail:
            result = PaymentResult(
                success=False,
                error_message=self.failure_message,
            )
        else:
            transfer_id = f"tr_test_{uuid.uuid4().hex[:16]}"
            self.transfers.append({
                "id": transfer_id,
                "amount_cents": amount_cents,
                "currency": currency,
                "destination": destination_account_id,
            })
            result = PaymentResult(
                success=True,
                payment_id=transfer_id,
                status=PaymentStatus.CAPTURED,
                amount_cents=amount_cents,
                currency=currency,
            )

        self._record_call("create_transfer", args, result)
        return result

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def mark_session_paid(self, session_id: str) -> None:
        """Mark a checkout session as paid (for testing)."""
        if session_id in self.checkout_sessions:
            self.checkout_sessions[session_id]["status"] = "complete"
            self.checkout_sessions[session_id]["payment_status"] = "paid"

    def enable_connect_account(self, account_id: str) -> None:
        """Enable a Connect account (for testing)."""
        if account_id in self.connect_accounts:
            self.connect_accounts[account_id]["charges_enabled"] = True
            self.connect_accounts[account_id]["payouts_enabled"] = True

    def get_calls(self, method: str) -> list[FakePaymentCall]:
        """Get all calls to a specific method."""
        return [c for c in self.calls if c.method == method]

    def reset(self) -> None:
        """Reset all state."""
        self.calls.clear()
        self.checkout_sessions.clear()
        self.refunds.clear()
        self.connect_accounts.clear()
        self.transfers.clear()
        self.should_fail = False
