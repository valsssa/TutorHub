"""Tests for Payment, Refund, and Payout metadata field naming."""

from sqlalchemy import inspect

from models.payments import Payment, Payout, Refund


def test_payment_metadata_column_name():
    """Payment.payment_metadata should map to 'metadata' DB column."""
    mapper = inspect(Payment)
    col = mapper.columns["payment_metadata"]
    assert col.name == "metadata"


def test_refund_metadata_column_name():
    """Refund.refund_metadata should map to 'metadata' DB column."""
    mapper = inspect(Refund)
    col = mapper.columns["refund_metadata"]
    assert col.name == "metadata"


def test_payout_metadata_column_name():
    """Payout.payout_metadata should map to 'metadata' DB column."""
    mapper = inspect(Payout)
    col = mapper.columns["payout_metadata"]
    assert col.name == "metadata"


def test_payment_has_metadata_attribute():
    """Payment should have payment_metadata as a Python attribute."""
    p = Payment()
    p.payment_metadata = {"key": "value"}
    assert p.payment_metadata == {"key": "value"}


def test_refund_has_metadata_attribute():
    """Refund should have refund_metadata as a Python attribute."""
    r = Refund()
    r.refund_metadata = {"reason": "test"}
    assert r.refund_metadata == {"reason": "test"}


def test_payout_has_metadata_attribute():
    """Payout should have payout_metadata as a Python attribute."""
    p = Payout()
    p.payout_metadata = {"batch": "001"}
    assert p.payout_metadata == {"batch": "001"}
