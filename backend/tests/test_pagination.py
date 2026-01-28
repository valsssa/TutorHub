"""Tests for pagination utilities."""

import pytest
from pydantic import ValidationError

from core.pagination import PaginatedResponse, PaginationParams, paginate


class TestPaginationParams:
    """Test PaginationParams model."""

    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50

    def test_skip_calculation(self):
        """Test skip calculation for database offset."""
        params = PaginationParams(page=1, page_size=20)
        assert params.skip == 0

        params = PaginationParams(page=2, page_size=20)
        assert params.skip == 20

        params = PaginationParams(page=3, page_size=10)
        assert params.skip == 20

    def test_limit_property(self):
        """Test limit property."""
        params = PaginationParams(page=1, page_size=50)
        assert params.limit == 50

    def test_page_minimum(self):
        """Test page minimum validation."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_page_size_minimum(self):
        """Test page_size minimum validation."""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

        with pytest.raises(ValidationError):
            PaginationParams(page_size=-1)

    def test_page_size_maximum(self):
        """Test page_size maximum validation (100)."""
        # Should work at max
        params = PaginationParams(page_size=100)
        assert params.page_size == 100

        # Should fail above max
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

    def test_skip_for_large_page(self):
        """Test skip calculation for large page numbers."""
        params = PaginationParams(page=100, page_size=20)
        assert params.skip == 1980  # (100-1) * 20


class TestPaginatedResponse:
    """Test PaginatedResponse model."""

    def test_create_first_page(self):
        """Test creating response for first page."""
        response = PaginatedResponse.create(
            items=[1, 2, 3],
            total=10,
            page=1,
            page_size=3,
        )
        assert response.items == [1, 2, 3]
        assert response.total == 10
        assert response.page == 1
        assert response.page_size == 3
        assert response.total_pages == 4
        assert response.has_next is True
        assert response.has_prev is False

    def test_create_middle_page(self):
        """Test creating response for middle page."""
        response = PaginatedResponse.create(
            items=[4, 5, 6],
            total=10,
            page=2,
            page_size=3,
        )
        assert response.page == 2
        assert response.has_next is True
        assert response.has_prev is True

    def test_create_last_page(self):
        """Test creating response for last page."""
        response = PaginatedResponse.create(
            items=[10],
            total=10,
            page=4,
            page_size=3,
        )
        assert response.page == 4
        assert response.total_pages == 4
        assert response.has_next is False
        assert response.has_prev is True

    def test_single_page_result(self):
        """Test response when all items fit on one page."""
        response = PaginatedResponse.create(
            items=[1, 2, 3],
            total=3,
            page=1,
            page_size=10,
        )
        assert response.total_pages == 1
        assert response.has_next is False
        assert response.has_prev is False

    def test_empty_result(self):
        """Test response with empty results."""
        response = PaginatedResponse.create(
            items=[],
            total=0,
            page=1,
            page_size=10,
        )
        assert response.items == []
        assert response.total == 0
        assert response.total_pages == 0
        assert response.has_next is False
        assert response.has_prev is False

    def test_total_pages_calculation(self):
        """Test total pages calculation."""
        # 10 items, 3 per page = 4 pages (ceiling division)
        response = PaginatedResponse.create(
            items=[],
            total=10,
            page=1,
            page_size=3,
        )
        assert response.total_pages == 4

        # 9 items, 3 per page = 3 pages (exact division)
        response = PaginatedResponse.create(
            items=[],
            total=9,
            page=1,
            page_size=3,
        )
        assert response.total_pages == 3

    def test_typed_items(self):
        """Test that items can be any type."""
        # String items
        response = PaginatedResponse.create(
            items=["a", "b", "c"],
            total=3,
            page=1,
            page_size=10,
        )
        assert response.items == ["a", "b", "c"]

        # Dict items
        response = PaginatedResponse.create(
            items=[{"id": 1}, {"id": 2}],
            total=2,
            page=1,
            page_size=10,
        )
        assert response.items == [{"id": 1}, {"id": 2}]


class TestPaginateFunction:
    """Test paginate helper function."""

    def test_basic_pagination(self):
        """Test basic pagination."""
        params = PaginationParams(page=1, page_size=10)
        result = paginate(
            query_result=[1, 2, 3],
            total=30,
            params=params,
        )
        assert isinstance(result, PaginatedResponse)
        assert result.items == [1, 2, 3]
        assert result.total == 30
        assert result.page == 1
        assert result.page_size == 10

    def test_pagination_with_different_params(self):
        """Test pagination with different parameters."""
        params = PaginationParams(page=3, page_size=5)
        result = paginate(
            query_result=[11, 12, 13, 14, 15],
            total=50,
            params=params,
        )
        assert result.page == 3
        assert result.page_size == 5
        assert result.total_pages == 10
        assert result.has_next is True
        assert result.has_prev is True

    def test_pagination_metadata_correct(self):
        """Test that pagination metadata is correct."""
        params = PaginationParams(page=5, page_size=20)
        result = paginate(
            query_result=list(range(20)),
            total=100,
            params=params,
        )
        # Page 5 of 5 (100 / 20)
        assert result.total_pages == 5
        assert result.has_next is False
        assert result.has_prev is True


class TestPaginationEdgeCases:
    """Test edge cases in pagination."""

    def test_page_beyond_total(self):
        """Test page number beyond total pages."""
        response = PaginatedResponse.create(
            items=[],
            total=10,
            page=100,  # Way beyond actual pages
            page_size=10,
        )
        assert response.page == 100
        assert response.total_pages == 1
        # has_next should be False since we're way past
        assert response.has_next is False
        assert response.has_prev is True

    def test_large_total_count(self):
        """Test with large total count."""
        response = PaginatedResponse.create(
            items=list(range(20)),
            total=1_000_000,
            page=1,
            page_size=20,
        )
        assert response.total_pages == 50_000
        assert response.has_next is True

    def test_page_size_equals_total(self):
        """Test when page size equals total."""
        response = PaginatedResponse.create(
            items=list(range(10)),
            total=10,
            page=1,
            page_size=10,
        )
        assert response.total_pages == 1
        assert response.has_next is False
        assert response.has_prev is False

    def test_page_size_greater_than_total(self):
        """Test when page size is greater than total."""
        response = PaginatedResponse.create(
            items=list(range(5)),
            total=5,
            page=1,
            page_size=100,
        )
        assert response.total_pages == 1
        assert response.has_next is False

    def test_skip_calculation_boundary(self):
        """Test skip calculation at boundaries."""
        params = PaginationParams(page=1, page_size=1)
        assert params.skip == 0

        params = PaginationParams(page=2, page_size=1)
        assert params.skip == 1

        params = PaginationParams(page=1000, page_size=100)
        assert params.skip == 99900
