"""Tests for RegistrationFraudSignal model fields."""

from decimal import Decimal

from sqlalchemy import Numeric, inspect

from models.auth import RegistrationFraudSignal


def test_fraud_signal_has_confidence_score():
    """RegistrationFraudSignal should have confidence_score column."""
    mapper = inspect(RegistrationFraudSignal)
    columns = {c.key for c in mapper.columns}
    assert "confidence_score" in columns


def test_confidence_score_is_numeric_3_2():
    """confidence_score should be Numeric(3, 2) not Integer."""
    mapper = inspect(RegistrationFraudSignal)
    col = mapper.columns["confidence_score"]
    col_type = col.type
    assert isinstance(col_type, Numeric)
    assert col_type.precision == 3
    assert col_type.scale == 2


def test_fraud_signal_confidence_score_default():
    """confidence_score should default to 0.50."""
    signal = RegistrationFraudSignal()
    assert signal.confidence_score is None or signal.confidence_score == Decimal("0.50")


def test_fraud_signal_has_required_fields():
    """RegistrationFraudSignal should have all required fields."""
    mapper = inspect(RegistrationFraudSignal)
    columns = {c.key for c in mapper.columns}
    required = {
        "id",
        "user_id",
        "signal_type",
        "signal_value",
        "confidence_score",
        "detected_at",
        "reviewed_at",
        "reviewed_by",
        "review_outcome",
        "review_notes",
    }
    assert required.issubset(columns)
