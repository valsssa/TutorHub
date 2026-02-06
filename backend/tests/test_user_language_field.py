"""Tests for user language field."""
from sqlalchemy import inspect

from models.auth import User


def test_preferred_language_max_length():
    """preferred_language should be max 2 chars to match CHAR(2) in DB."""
    mapper = inspect(User)
    col = mapper.columns.get("preferred_language")
    assert col is not None
    # Should be 2 chars, not 5
    assert col.type.length == 2


def test_preferred_language_has_default():
    """preferred_language should default to 'en'."""
    mapper = inspect(User)
    col = mapper.columns.get("preferred_language")
    assert col is not None
    assert col.default is not None
    assert col.default.arg == "en"


def test_preferred_language_not_nullable():
    """preferred_language should not be nullable."""
    mapper = inspect(User)
    col = mapper.columns.get("preferred_language")
    assert col is not None
    assert col.nullable is False
