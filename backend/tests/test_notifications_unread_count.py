"""Tests for notifications unread count endpoint."""

import pytest


def test_unread_count_response_has_count_field():
    """Verify UnreadCountResponse schema uses 'count' field."""
    from modules.notifications.presentation.api import UnreadCountResponse

    fields = UnreadCountResponse.model_fields.keys()
    assert "count" in fields, "UnreadCountResponse should use 'count' field"
    assert "unread_count" not in fields, "Should use 'count' not 'unread_count'"


def test_unread_count_response_schema_structure():
    """Verify the structure of UnreadCountResponse."""
    from modules.notifications.presentation.api import UnreadCountResponse

    # Verify we can create an instance
    response = UnreadCountResponse(count=5)
    assert response.count == 5

    # Verify serialization uses correct field name
    response_dict = response.model_dump()
    assert "count" in response_dict
    assert response_dict["count"] == 5
