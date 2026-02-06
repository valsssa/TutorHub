"""Query helper utilities for common database operations.

This module provides standardized helpers for common query patterns like
fetching entities with 404 handling, reducing duplicate code across modules.
"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session


def get_or_404[T](
    db: Session,
    model: type[T],
    filters: dict[str, Any],
    *,
    detail: str = "Resource not found",
    include_deleted: bool = False,
) -> T:
    """
    Query for a single record and raise 404 if not found.

    This helper consolidates the common pattern of:
        entity = db.query(Model).filter_by(**filters).first()
        if not entity:
            raise HTTPException(status_code=404, detail="...")

    Args:
        db: SQLAlchemy database session
        model: SQLAlchemy model class to query
        filters: Dictionary of filter conditions (passed to filter_by)
        detail: Error message for 404 response (default: "Resource not found")
        include_deleted: If False (default), excludes soft-deleted records

    Returns:
        The found entity

    Raises:
        HTTPException: 404 if no matching record found

    Example:
        # Simple lookup
        user = get_or_404(db, User, {"id": user_id})

        # With custom error message
        booking = get_or_404(db, Booking, {"id": booking_id}, detail="Booking not found")

        # Include soft-deleted records
        user = get_or_404(db, User, {"id": user_id}, include_deleted=True)
    """
    query = db.query(model).filter_by(**filters)

    # Apply soft-delete filter if model supports it
    if not include_deleted and hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))

    entity = query.first()
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return entity


def get_or_none[T](
    db: Session,
    model: type[T],
    filters: dict[str, Any],
    *,
    include_deleted: bool = False,
) -> T | None:
    """
    Query for a single record and return None if not found.

    Similar to get_or_404 but returns None instead of raising an exception.
    Useful when you need to handle the not-found case differently.

    Args:
        db: SQLAlchemy database session
        model: SQLAlchemy model class to query
        filters: Dictionary of filter conditions (passed to filter_by)
        include_deleted: If False (default), excludes soft-deleted records

    Returns:
        The found entity or None

    Example:
        user = get_or_none(db, User, {"email": email})
        if user:
            # Handle existing user
        else:
            # Handle new user
    """
    query = db.query(model).filter_by(**filters)

    # Apply soft-delete filter if model supports it
    if not include_deleted and hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))

    return query.first()


def exists_or_404[T](
    db: Session,
    model: type[T],
    filters: dict[str, Any],
    *,
    detail: str = "Resource not found",
    include_deleted: bool = False,
) -> bool:
    """
    Check if a record exists and raise 404 if not.

    More efficient than get_or_404 when you only need to verify existence
    without loading the full entity.

    Args:
        db: SQLAlchemy database session
        model: SQLAlchemy model class to query
        filters: Dictionary of filter conditions (passed to filter_by)
        detail: Error message for 404 response (default: "Resource not found")
        include_deleted: If False (default), excludes soft-deleted records

    Returns:
        True (always, as 404 is raised if not exists)

    Raises:
        HTTPException: 404 if no matching record found

    Example:
        exists_or_404(db, TutorProfile, {"id": tutor_id}, detail="Tutor not found")
        # If we get here, tutor exists
    """
    query = db.query(model).filter_by(**filters)

    # Apply soft-delete filter if model supports it
    if not include_deleted and hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))

    exists = db.query(query.exists()).scalar()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return True


def get_by_id_or_404[T](
    db: Session,
    model: type[T],
    entity_id: int,
    *,
    detail: str | None = None,
    include_deleted: bool = False,
) -> T:
    """
    Query for a single record by ID and raise 404 if not found.

    Convenience function for the most common lookup pattern - by primary key ID.

    Args:
        db: SQLAlchemy database session
        model: SQLAlchemy model class to query
        entity_id: The ID to look up
        detail: Error message for 404 response (auto-generated if not provided)
        include_deleted: If False (default), excludes soft-deleted records

    Returns:
        The found entity

    Raises:
        HTTPException: 404 if no matching record found

    Example:
        user = get_by_id_or_404(db, User, user_id)
        booking = get_by_id_or_404(db, Booking, booking_id, detail="Booking not found")
    """
    if detail is None:
        # Generate detail from model name: "UserProfile" -> "User profile not found"
        model_name = model.__name__
        # Convert CamelCase to spaces
        import re

        readable_name = re.sub(r"(?<!^)(?=[A-Z])", " ", model_name)
        detail = f"{readable_name} not found"

    return get_or_404(db, model, {"id": entity_id}, detail=detail, include_deleted=include_deleted)


def get_with_options_or_404[T](
    query: Query[T],
    *,
    detail: str = "Resource not found",
) -> T:
    """
    Execute a pre-built query and raise 404 if no result.

    Use this when you need complex queries with joins, eager loading, or
    row-level locking that can't be expressed with simple filters.

    Args:
        query: Pre-built SQLAlchemy query (with options, joins, etc.)
        detail: Error message for 404 response (default: "Resource not found")

    Returns:
        The found entity

    Raises:
        HTTPException: 404 if no matching record found

    Example:
        # Complex query with eager loading and row locking
        query = (
            db.query(StudentPackage)
            .options(joinedload(StudentPackage.pricing_option))
            .filter(StudentPackage.id == package_id)
            .with_for_update(nowait=False)
        )
        package = get_with_options_or_404(query, detail="Package not found")
    """
    entity = query.first()
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return entity


def exists_or_409[T](
    db: Session,
    model: type[T],
    filters: dict[str, Any],
    *,
    detail: str = "Resource already exists",
    include_deleted: bool = False,
) -> None:
    """
    Check if a record exists and raise 409 Conflict if it does.

    Useful for preventing duplicate creation (e.g., user already favorited).

    Args:
        db: SQLAlchemy database session
        model: SQLAlchemy model class to query
        filters: Dictionary of filter conditions (passed to filter_by)
        detail: Error message for 409 response
        include_deleted: If False (default), excludes soft-deleted records

    Raises:
        HTTPException: 409 if matching record exists

    Example:
        exists_or_409(
            db, FavoriteTutor,
            {"student_id": student.id, "tutor_id": tutor_id},
            detail="Already favorited"
        )
    """
    query = db.query(model).filter_by(**filters)

    # Apply soft-delete filter if model supports it
    if not include_deleted and hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))

    exists = db.query(query.exists()).scalar()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
