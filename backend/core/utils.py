"""Common utility functions."""

from datetime import datetime, timedelta
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DateTimeUtils:
    """Utilities for datetime operations."""

    @staticmethod
    def now() -> datetime:
        """Get current UTC datetime."""
        return datetime.utcnow()

    @staticmethod
    def add_minutes(dt: datetime, minutes: int) -> datetime:
        """Add minutes to a datetime."""
        return dt + timedelta(minutes=minutes)

    @staticmethod
    def calculate_hours_between(start: datetime, end: datetime) -> float:
        """Calculate hours between two datetimes."""
        delta = end - start
        return delta.total_seconds() / 3600

    @staticmethod
    def is_in_future(dt: datetime) -> bool:
        """Check if datetime is in the future."""
        return dt > datetime.utcnow()

    @staticmethod
    def is_in_past(dt: datetime) -> bool:
        """Check if datetime is in the past."""
        return dt < datetime.utcnow()


class StringUtils:
    """Utilities for string operations."""

    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email to lowercase and strip whitespace."""
        return email.lower().strip()

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to max length with suffix."""
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix


class ValidationUtils:
    """Common validation utilities."""

    @staticmethod
    def validate_time_range(
        start: datetime, end: datetime, max_hours: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate time range."""
        if start >= end:
            return False, "End time must be after start time"

        if max_hours:
            hours = DateTimeUtils.calculate_hours_between(start, end)
            if hours > max_hours:
                return False, f"Duration cannot exceed {max_hours} hours"

        if DateTimeUtils.is_in_past(start):
            return False, "Start time must be in the future"

        return True, None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


def paginate(query, page: int = 1, page_size: int = 50):
    """Paginate SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)

    Returns:
        PaginatedResponse with items and pagination metadata
    """
    # Validate and limit page_size
    page_size = min(max(1, page_size), 100)
    page = max(1, page)

    # Get total count
    total = query.count()

    # Get paginated items
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
