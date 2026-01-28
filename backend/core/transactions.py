"""
Transaction Management Utilities

Provides helpers for safe database transaction handling with proper
error handling and automatic rollback on failures.
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TransactionError(Exception):
    """Base exception for transaction errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for safe database transactions.

    Automatically commits on success, rolls back on failure.

    Usage:
        with transaction(db):
            db.add(new_item)
            # Commits automatically on exit

        # Or with explicit return value:
        with transaction(db) as session:
            session.add(new_item)
            session.flush()  # Get ID before commit

    Raises:
        TransactionError: On database errors with rollback
    """
    try:
        yield db
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error in transaction: {e}")
        raise TransactionError("Data integrity violation", original_error=e)
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database operational error: {e}")
        raise TransactionError("Database operation failed", original_error=e)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in transaction: {e}")
        raise TransactionError("Database error", original_error=e)
    except Exception:
        db.rollback()
        raise


def safe_commit(db: Session, error_message: str = "Database operation failed") -> bool:
    """
    Safely commit database changes with error handling.

    Args:
        db: Database session
        error_message: Message to log on failure

    Returns:
        True if commit succeeded, False otherwise
    """
    try:
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        logger.error(f"{error_message} - Integrity error: {e}")
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"{error_message} - Database error: {e}")
        return False


def commit_or_raise(
    db: Session,
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_detail: str = "Database operation failed",
) -> None:
    """
    Commit database changes or raise HTTPException on failure.

    Args:
        db: Database session
        http_status: HTTP status code on failure
        error_detail: Error detail message

    Raises:
        HTTPException: On database error
    """
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error during commit: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data integrity violation - this operation conflicts with existing data",
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during commit: {e}")
        raise HTTPException(
            status_code=http_status,
            detail=error_detail,
        )


def transactional(error_message: str = "Operation failed") -> Callable:
    """
    Decorator for endpoint functions that need transaction handling.

    Wraps the function to handle database errors consistently.

    Usage:
        @router.post("/items")
        @transactional("Failed to create item")
        async def create_item(db: Session = Depends(get_db)):
            item = Item(name="new")
            db.add(item)
            db.commit()  # Errors handled by decorator
            return item

    Note: This decorator should be applied AFTER route decorators.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except TransactionError as e:
                logger.error(f"{error_message}: {e.message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )
            except SQLAlchemyError as e:
                logger.error(f"{error_message} - Database error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except TransactionError as e:
                logger.error(f"{error_message}: {e.message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )
            except SQLAlchemyError as e:
                logger.error(f"{error_message} - Database error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_savepoint(db: Session, name: str | None = None) -> Generator[Session, None, None]:
    """
    Create a savepoint for nested transaction handling.

    Usage:
        with transaction(db):
            # Main work
            db.add(parent)
            db.flush()

            with with_savepoint(db, "child_work"):
                # Nested work - can be rolled back independently
                db.add(child)
    """
    savepoint = db.begin_nested()
    try:
        yield db
        savepoint.commit()
    except Exception:
        savepoint.rollback()
        raise
