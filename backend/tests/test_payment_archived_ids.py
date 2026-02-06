"""Tests for payment archived ID fields."""

from sqlalchemy import inspect

from models.payments import Payment, Payout


def test_payment_has_archived_student_id():
    """Verify Payment model has archived_student_id column for preserving references."""
    mapper = inspect(Payment)
    assert "archived_student_id" in [c.key for c in mapper.columns]


def test_payout_has_archived_tutor_id():
    """Verify Payout model has archived_tutor_id column for preserving references."""
    mapper = inspect(Payout)
    assert "archived_tutor_id" in [c.key for c in mapper.columns]
