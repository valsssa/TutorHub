"""Tests for User locale and language detection fields."""

from sqlalchemy import Numeric, String, inspect

from models.auth import User


def test_user_has_detected_language():
    """User should have detected_language column."""
    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    assert "detected_language" in columns


def test_user_detected_language_is_string_2():
    """detected_language should be String(2)."""
    mapper = inspect(User)
    col = mapper.columns["detected_language"]
    assert isinstance(col.type, String)
    assert col.type.length == 2


def test_user_has_locale():
    """User should have locale column."""
    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    assert "locale" in columns


def test_user_locale_is_string_10():
    """locale should be String(10)."""
    mapper = inspect(User)
    col = mapper.columns["locale"]
    assert isinstance(col.type, String)
    assert col.type.length == 10


def test_user_has_detected_locale():
    """User should have detected_locale column."""
    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    assert "detected_locale" in columns


def test_user_detected_locale_is_string_10():
    """detected_locale should be String(10)."""
    mapper = inspect(User)
    col = mapper.columns["detected_locale"]
    assert isinstance(col.type, String)
    assert col.type.length == 10


def test_user_has_locale_detection_confidence():
    """User should have locale_detection_confidence column."""
    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    assert "locale_detection_confidence" in columns


def test_user_locale_detection_confidence_is_numeric_3_2():
    """locale_detection_confidence should be Numeric(3, 2)."""
    mapper = inspect(User)
    col = mapper.columns["locale_detection_confidence"]
    assert isinstance(col.type, Numeric)
    assert col.type.precision == 3
    assert col.type.scale == 2


def test_user_locale_fields_are_nullable():
    """All locale detection fields should be nullable."""
    mapper = inspect(User)
    for field in ["detected_language", "locale", "detected_locale", "locale_detection_confidence"]:
        col = mapper.columns[field]
        assert col.nullable is True, f"{field} should be nullable"
