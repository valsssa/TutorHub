"""Tests for User preferred_language field type."""

from sqlalchemy import String, inspect

from models.auth import User


def test_user_has_preferred_language():
    """User should have preferred_language column."""
    mapper = inspect(User)
    columns = {c.key for c in mapper.columns}
    assert "preferred_language" in columns


def test_preferred_language_is_string_2():
    """preferred_language should be String(2), not String(5)."""
    mapper = inspect(User)
    col = mapper.columns["preferred_language"]
    assert isinstance(col.type, String)
    assert col.type.length == 2


def test_preferred_language_default_is_en():
    """preferred_language should default to 'en'."""
    user = User()
    assert user.preferred_language == "en"


def test_preferred_language_is_not_nullable():
    """preferred_language should not be nullable."""
    mapper = inspect(User)
    col = mapper.columns["preferred_language"]
    assert col.nullable is False
