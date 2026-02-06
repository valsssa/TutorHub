"""Tests for bookings list pagination."""

import pytest


def test_bookings_list_returns_pagination_fields():
    """Verify response includes standard pagination fields."""
    from modules.bookings.schemas import BookingListResponse

    # Verify the response model has pagination fields
    fields = BookingListResponse.model_fields.keys()
    expected_pagination_fields = ["total", "page", "page_size", "bookings"]
    for field in expected_pagination_fields:
        assert field in fields, f"BookingListResponse missing {field}"


def test_bookings_list_response_structure():
    """Verify BookingListResponse has the expected field types."""
    from modules.bookings.schemas import BookingListResponse, BookingDTO

    # Check field annotations
    fields = BookingListResponse.model_fields

    # bookings should be a list of BookingDTO
    assert fields["bookings"].annotation == list[BookingDTO]

    # pagination fields should be integers
    assert fields["total"].annotation == int
    assert fields["page"].annotation == int
    assert fields["page_size"].annotation == int


def test_booking_list_response_can_be_instantiated():
    """Verify BookingListResponse can be instantiated with valid data."""
    from modules.bookings.schemas import BookingListResponse

    # Should be able to create a response with empty bookings
    response = BookingListResponse(
        bookings=[],
        total=0,
        page=1,
        page_size=20,
    )

    assert response.bookings == []
    assert response.total == 0
    assert response.page == 1
    assert response.page_size == 20


@pytest.mark.integration
class TestBookingsListPagination:
    """Integration tests for bookings list pagination."""

    def test_list_bookings_returns_pagination_fields(self, client, student_token):
        """Test that list bookings endpoint returns all pagination fields."""
        response = client.get(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify all pagination fields are present
        assert "bookings" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        # Verify types
        assert isinstance(data["bookings"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)

    def test_list_bookings_default_pagination(self, client, student_token):
        """Test default pagination values."""
        response = client.get(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Default values from endpoint: page=1, page_size=20
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_bookings_custom_pagination(self, client, student_token):
        """Test custom pagination parameters."""
        response = client.get(
            "/api/v1/bookings?page=2&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_list_bookings_page_size_limit(self, client, student_token):
        """Test that page_size is limited to maximum of 100."""
        response = client.get(
            "/api/v1/bookings?page_size=150",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should return 422 for page_size > 100
        assert response.status_code == 422

    def test_list_bookings_page_minimum(self, client, student_token):
        """Test that page must be >= 1."""
        response = client.get(
            "/api/v1/bookings?page=0",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should return 422 for page < 1
        assert response.status_code == 422
