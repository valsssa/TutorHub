"""Pagination utilities for list endpoints."""

from math import ceil
from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def skip(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper."""

    items: list[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """
        Create paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Number of items per page

        Returns:
            PaginatedResponse instance
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


def paginate[T](
    query_result: list[T],
    total: int,
    params: PaginationParams,
) -> PaginatedResponse[T]:
    """
    Helper function to create paginated response.

    Args:
        query_result: List of items from database query
        total: Total count from database
        params: Pagination parameters

    Returns:
        PaginatedResponse with metadata
    """
    return PaginatedResponse.create(
        items=query_result,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
