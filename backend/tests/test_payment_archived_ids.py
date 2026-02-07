"""Tests for Payment archived_student_id and Payout archived_tutor_id fields."""

from sqlalchemy import inspect

from models.payments import Payment, Payout, Refund, Wallet, WalletTransaction


def test_payment_has_archived_student_id():
    """Payment should have archived_student_id for deleted user references."""
    mapper = inspect(Payment)
    columns = {c.key for c in mapper.columns}
    assert "archived_student_id" in columns


def test_payment_archived_student_id_is_nullable():
    """archived_student_id should be nullable."""
    mapper = inspect(Payment)
    col = mapper.columns["archived_student_id"]
    assert col.nullable is True


def test_payout_has_archived_tutor_id():
    """Payout should have archived_tutor_id for deleted user references."""
    mapper = inspect(Payout)
    columns = {c.key for c in mapper.columns}
    assert "archived_tutor_id" in columns


def test_payout_archived_tutor_id_is_nullable():
    """archived_tutor_id should be nullable."""
    mapper = inspect(Payout)
    col = mapper.columns["archived_tutor_id"]
    assert col.nullable is True


def test_refund_has_soft_delete():
    """Refund should have deleted_at and deleted_by columns."""
    mapper = inspect(Refund)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_payout_has_soft_delete():
    """Payout should have deleted_at and deleted_by columns."""
    mapper = inspect(Payout)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_wallet_has_soft_delete():
    """Wallet should have deleted_at and deleted_by columns."""
    mapper = inspect(Wallet)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_wallet_transaction_has_soft_delete():
    """WalletTransaction should have deleted_at and deleted_by columns."""
    mapper = inspect(WalletTransaction)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_payment_has_soft_delete():
    """Payment should have deleted_at and deleted_by columns."""
    mapper = inspect(Payment)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns
