"""Tests for fraud detection model fields."""
from sqlalchemy import Numeric, inspect

from models.auth import RegistrationFraudSignal


def test_confidence_score_is_numeric():
    """confidence_score should be Numeric(3,2), not Integer."""
    mapper = inspect(RegistrationFraudSignal)
    col = mapper.columns.get("confidence_score")
    assert col is not None
    # Should be Numeric type, not Integer
    assert isinstance(col.type, Numeric), f"Expected Numeric, got {type(col.type).__name__}"


def test_confidence_score_precision_and_scale():
    """confidence_score should have precision 3 and scale 2."""
    mapper = inspect(RegistrationFraudSignal)
    col = mapper.columns.get("confidence_score")
    assert col is not None
    assert col.type.precision == 3, f"Expected precision 3, got {col.type.precision}"
    assert col.type.scale == 2, f"Expected scale 2, got {col.type.scale}"


def test_confidence_score_default():
    """confidence_score should default to 0.50."""
    mapper = inspect(RegistrationFraudSignal)
    col = mapper.columns.get("confidence_score")
    assert col is not None
    # Check the default value (should be 0.50, not 50)
    assert col.default is not None
    assert col.default.arg == 0.50, f"Expected default 0.50, got {col.default.arg}"
