"""Tests for cookie-based token extraction in dependencies."""

import pytest
from unittest.mock import MagicMock
from fastapi import Request

from core.dependencies import extract_token_from_request


@pytest.fixture
def mock_request():
    """Create mock request with configurable cookies and headers."""
    request = MagicMock(spec=Request)
    request.cookies = {}
    request.headers = {}
    return request


def test_extract_token_from_cookie(mock_request):
    """Token extracted from cookie when present."""
    mock_request.cookies = {"access_token": "cookie_token_value"}
    mock_request.headers = {}
    token = extract_token_from_request(mock_request)
    assert token == "cookie_token_value"


def test_extract_token_from_header(mock_request):
    """Token extracted from Authorization header when no cookie."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer header_token_value"}
    token = extract_token_from_request(mock_request)
    assert token == "header_token_value"


def test_cookie_takes_precedence_over_header(mock_request):
    """Cookie token preferred over header for gradual migration."""
    mock_request.cookies = {"access_token": "cookie_token"}
    mock_request.headers = {"authorization": "Bearer header_token"}
    token = extract_token_from_request(mock_request)
    assert token == "cookie_token"


def test_extract_token_returns_none_when_missing(mock_request):
    """None returned when no token found anywhere."""
    mock_request.cookies = {}
    mock_request.headers = {}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_malformed_header(mock_request):
    """Malformed Authorization header returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "InvalidFormat"}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_empty_bearer(mock_request):
    """Empty Bearer token returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer "}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_bearer_only(mock_request):
    """'Bearer' without space or token returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer"}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_case_insensitive_header(mock_request):
    """Authorization header lookup should work with lowercase."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer case_insensitive_token"}
    token = extract_token_from_request(mock_request)
    assert token == "case_insensitive_token"


def test_extract_token_handles_empty_cookie(mock_request):
    """Empty cookie value falls back to header."""
    mock_request.cookies = {"access_token": ""}
    mock_request.headers = {"authorization": "Bearer fallback_token"}
    token = extract_token_from_request(mock_request)
    assert token == "fallback_token"
