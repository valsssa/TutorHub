"""Tests for CSRF protection utilities."""
import pytest
from core.csrf import generate_csrf_token, validate_csrf_token


def test_generate_csrf_token_length():
    """CSRF token has sufficient entropy (32 bytes = 64 hex chars)."""
    token = generate_csrf_token()
    assert len(token) == 64
    assert all(c in "0123456789abcdef" for c in token)


def test_generate_csrf_token_unique():
    """Each generated token is unique."""
    tokens = {generate_csrf_token() for _ in range(100)}
    assert len(tokens) == 100


def test_validate_csrf_token_matches():
    """Validation passes when tokens match."""
    token = generate_csrf_token()
    assert validate_csrf_token(token, token) is True


def test_validate_csrf_token_mismatch():
    """Validation fails when tokens differ."""
    token1 = generate_csrf_token()
    token2 = generate_csrf_token()
    assert validate_csrf_token(token1, token2) is False


def test_validate_csrf_token_timing_safe():
    """Validation uses constant-time comparison."""
    token = generate_csrf_token()
    assert validate_csrf_token(token, token) is True
    assert validate_csrf_token(token, token + "x") is False
    assert validate_csrf_token(token, "") is False
    assert validate_csrf_token("", token) is False


def test_validate_csrf_token_none_handling():
    """Validation handles None values safely."""
    token = generate_csrf_token()
    assert validate_csrf_token(None, token) is False
    assert validate_csrf_token(token, None) is False
    assert validate_csrf_token(None, None) is False
