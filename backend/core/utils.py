"""Common utility functions."""

import functools
import inspect
import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

T = TypeVar("T")

logger = logging.getLogger(__name__)


def handle_db_errors(
    operation: str = "perform operation",
    rollback: bool = True,
) -> Callable:
    """
    Decorator to handle database errors consistently across endpoints.

    Centralizes the 146+ duplicate try/except/HTTPException patterns.

    Args:
        operation: Description of the operation for error messages
        rollback: Whether to rollback the database session on error

    Usage:
        @handle_db_errors("create user")
        async def create_user_endpoint(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            db: Session | None = None
            # Try to find db session in kwargs or args
            if "db" in kwargs:
                db = kwargs["db"]
            else:
                # Check positional args for Session object
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break

            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions as-is (client errors)
                raise
            except Exception as e:
                # Rollback database transaction if available
                if db and rollback:
                    db.rollback()

                # Log the error with full context
                logger.error(f"Error in {operation}: {str(e)}", exc_info=True)

                # Raise generic 500 error to client
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation}",
                ) from e

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            db: Session | None = None
            # Try to find db session in kwargs or args
            if "db" in kwargs:
                db = kwargs["db"]
            else:
                # Check positional args for Session object
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break

            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions as-is (client errors)
                raise
            except Exception as e:
                # Rollback database transaction if available
                if db and rollback:
                    db.rollback()

                # Log the error with full context
                logger.error(f"Error in {operation}: {str(e)}", exc_info=True)

                # Raise generic 500 error to client
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation}",
                ) from e

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class DateTimeUtils:
    """Utilities for datetime operations."""

    @staticmethod
    def now() -> datetime:
        """Get current UTC datetime."""
        return utc_now()

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
        return dt > utc_now()

    @staticmethod
    def is_in_past(dt: datetime) -> bool:
        """Check if datetime is in the past."""
        return dt < utc_now()


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

    @staticmethod
    def format_display_name(first_name: str | None, last_name: str | None, fallback: str | None = None) -> str:
        """
        Centralized utility for formatting display names.

        Combines first and last name, or returns fallback if no names available.
        Used consistently across the application for name display.
        """
        if first_name or last_name:
            return f"{first_name or ''} {last_name or ''}".strip()
        return fallback or ""


class ValidationUtils:
    """Common validation utilities."""

    @staticmethod
    def validate_time_range(start: datetime, end: datetime, max_hours: int | None = None) -> tuple[bool, str | None]:
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


class PaginatedResponse[T](BaseModel):
    """Paginated response schema."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


def get_user_or_404(db: Session, user_id: int):
    """
    Get user by ID or raise 404.

    Centralizes 25+ duplicate user lookup queries across the codebase.

    Args:
        db: Database session
        user_id: User ID to lookup

    Returns:
        User object

    Raises:
        HTTPException: 404 if user not found
    """
    from backend.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


def get_tutor_profile_or_404(db: Session, tutor_id: int):
    """
    Get tutor profile by ID or raise 404.

    Centralizes 15+ duplicate tutor profile lookup queries.

    Args:
        db: Database session
        tutor_id: Tutor profile ID to lookup

    Returns:
        TutorProfile object

    Raises:
        HTTPException: 404 if tutor profile not found
    """
    from backend.models import TutorProfile

    tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == tutor_id).first()
    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor profile with ID {tutor_id} not found",
        )
    return tutor_profile


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
