"""Tests for payment metadata field naming.

The database schema uses 'metadata' as the column name, but SQLAlchemy's
Declarative API reserves 'metadata' as an attribute name. Therefore, we use
descriptive Python attribute names (payment_metadata, refund_metadata,
payout_metadata) that map to the 'metadata' database column.
"""
from sqlalchemy import inspect
from models.payments import Payment, Refund, Payout


def test_payment_metadata_maps_to_database_column():
    """Payment.payment_metadata should map to 'metadata' database column."""
    mapper = inspect(Payment)
    # Get the column object for payment_metadata attribute
    column = mapper.columns["payment_metadata"]
    # Verify it maps to the 'metadata' database column name
    assert column.name == "metadata"


def test_refund_metadata_maps_to_database_column():
    """Refund.refund_metadata should map to 'metadata' database column."""
    mapper = inspect(Refund)
    column = mapper.columns["refund_metadata"]
    assert column.name == "metadata"


def test_payout_metadata_maps_to_database_column():
    """Payout.payout_metadata should map to 'metadata' database column."""
    mapper = inspect(Payout)
    column = mapper.columns["payout_metadata"]
    assert column.name == "metadata"
