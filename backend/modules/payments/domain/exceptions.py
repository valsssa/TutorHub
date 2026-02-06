"""
Domain exceptions for payments module.

These exceptions represent business rule violations specific to payments.
"""


class PaymentError(Exception):
    """Base exception for payment domain errors."""

    pass


class PaymentNotFoundError(PaymentError):
    """Raised when a payment is not found."""

    def __init__(self, identifier: str | int | None = None):
        self.identifier = identifier
        message = f"Payment not found: {identifier}" if identifier else "Payment not found"
        super().__init__(message)


class InsufficientFundsError(PaymentError):
    """Raised when wallet balance is insufficient for the operation."""

    def __init__(
        self,
        required_cents: int,
        available_cents: int,
        currency: str = "USD",
    ):
        self.required_cents = required_cents
        self.available_cents = available_cents
        self.currency = currency
        message = (
            f"Insufficient funds: required {required_cents} cents, "
            f"available {available_cents} cents ({currency})"
        )
        super().__init__(message)


class InvalidAmountError(PaymentError):
    """Raised when a payment amount is invalid."""

    def __init__(
        self,
        amount_cents: int,
        reason: str = "Amount must be positive",
    ):
        self.amount_cents = amount_cents
        self.reason = reason
        message = f"Invalid amount {amount_cents} cents: {reason}"
        super().__init__(message)


class RefundNotAllowedError(PaymentError):
    """Raised when a refund cannot be processed."""

    def __init__(
        self,
        payment_id: int | str | None = None,
        reason: str = "Refund not allowed",
    ):
        self.payment_id = payment_id
        self.reason = reason
        if payment_id:
            message = f"Refund not allowed for payment {payment_id}: {reason}"
        else:
            message = f"Refund not allowed: {reason}"
        super().__init__(message)


class WalletNotFoundError(PaymentError):
    """Raised when a wallet is not found."""

    def __init__(
        self,
        user_id: int | None = None,
        wallet_id: int | None = None,
    ):
        self.user_id = user_id
        self.wallet_id = wallet_id
        if user_id:
            message = f"Wallet not found for user: {user_id}"
        elif wallet_id:
            message = f"Wallet not found: {wallet_id}"
        else:
            message = "Wallet not found"
        super().__init__(message)


class TransferFailedError(PaymentError):
    """Raised when a wallet transfer fails."""

    def __init__(
        self,
        from_wallet_id: int | None = None,
        to_wallet_id: int | None = None,
        reason: str = "Transfer failed",
    ):
        self.from_wallet_id = from_wallet_id
        self.to_wallet_id = to_wallet_id
        self.reason = reason
        if from_wallet_id and to_wallet_id:
            message = (
                f"Transfer failed from wallet {from_wallet_id} "
                f"to wallet {to_wallet_id}: {reason}"
            )
        else:
            message = f"Transfer failed: {reason}"
        super().__init__(message)


class PayoutFailedError(PaymentError):
    """Raised when a payout to a tutor fails."""

    def __init__(
        self,
        tutor_id: int | None = None,
        payout_id: int | str | None = None,
        reason: str = "Payout failed",
    ):
        self.tutor_id = tutor_id
        self.payout_id = payout_id
        self.reason = reason
        if tutor_id:
            message = f"Payout failed for tutor {tutor_id}: {reason}"
        elif payout_id:
            message = f"Payout {payout_id} failed: {reason}"
        else:
            message = f"Payout failed: {reason}"
        super().__init__(message)
