"""Tests for user locale fields."""
from sqlalchemy import inspect

from models.auth import User


def test_user_has_detected_language():
    """Test User model has detected_language column."""
    mapper = inspect(User)
    assert "detected_language" in [c.key for c in mapper.columns]


def test_user_has_locale():
    """Test User model has locale column."""
    mapper = inspect(User)
    assert "locale" in [c.key for c in mapper.columns]


def test_user_has_detected_locale():
    """Test User model has detected_locale column."""
    mapper = inspect(User)
    assert "detected_locale" in [c.key for c in mapper.columns]


def test_user_has_locale_detection_confidence():
    """Test User model has locale_detection_confidence column."""
    mapper = inspect(User)
    assert "locale_detection_confidence" in [c.key for c in mapper.columns]
