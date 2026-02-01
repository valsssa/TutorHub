"""
Transaction Management Utilities

Provides helpers for safe database transaction handling with proper
error handling and automatic rollback on failures.
"""

import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

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


@contextmanager
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


@contextmanager
def atomic_operation(db: Session) -> Generator[Session, None, None]:
    """
    Context manager ensuring all operations commit together or roll back.

    Use this for multi-table inserts to prevent orphaned records from
    partial failures. All database operations within the context are
    committed atomically on success, or completely rolled back on failure.

    Usage:
        with atomic_operation(db) as session:
            user = User(email="test@example.com")
            session.add(user)
            session.flush()  # Get user.id for foreign key

            profile = UserProfile(user_id=user.id)
            session.add(profile)
            # Both committed together on context exit

    Args:
        db: SQLAlchemy database session

    Yields:
        The same session for use within the context

    Raises:
        TransactionError: On database integrity or operational errors
        Exception: Re-raises any other exceptions after rollback
    """
    try:
        yield db
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error in atomic operation: {e}")
        raise TransactionError("Data integrity violation", original_error=e)
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database operational error in atomic operation: {e}")
        raise TransactionError("Database operation failed", original_error=e)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in atomic operation: {e}")
        raise TransactionError("Database error", original_error=e)
    except Exception:
        db.rollback()
        raise


def atomic[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for functions requiring atomic transaction handling.

    Automatically commits on success, rolls back on any failure.
    Use this decorator on service layer methods that perform multi-table
    operations to prevent orphaned records.

    The decorated function must accept a `db` keyword argument of type Session.

    Usage:
        class UserService:
            @atomic
            def register_user(self, registration_data, db: Session):
                user = User(email=registration_data.email)
                db.add(user)
                db.flush()  # Get user.id for profile

                profile = StudentProfile(user_id=user.id)
                db.add(profile)
                # Both committed together by decorator
                return user

    Note:
        - Works with both sync and async functions
        - Re-raises HTTPException without modification
        - Converts database errors to TransactionError
        - The db session should NOT call commit() inside the function;
          the decorator handles commit/rollback

    Raises:
        TransactionError: On database errors after rollback
        HTTPException: Re-raised without modification
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> T:
        db: Session | None = kwargs.get("db")
        if db is None:
            # Try to find db in positional args (for method calls)
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break

        if db is None:
            raise ValueError("atomic decorator requires a 'db' Session parameter")

        try:
            result = await func(*args, **kwargs)
            db.commit()
            return result
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error in atomic function {func.__name__}: {e}")
            raise TransactionError("Data integrity violation", original_error=e)
        except OperationalError as e:
            db.rollback()
            logger.error(f"Operational error in atomic function {func.__name__}: {e}")
            raise TransactionError("Database operation failed", original_error=e)
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in atomic function {func.__name__}: {e}")
            raise TransactionError("Database error", original_error=e)
        except Exception:
            db.rollback()
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> T:
        db: Session | None = kwargs.get("db")
        if db is None:
            # Try to find db in positional args (for method calls)
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break

        if db is None:
            raise ValueError("atomic decorator requires a 'db' Session parameter")

        try:
            result = func(*args, **kwargs)
            db.commit()
            return result
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error in atomic function {func.__name__}: {e}")
            raise TransactionError("Data integrity violation", original_error=e)
        except OperationalError as e:
            db.rollback()
            logger.error(f"Operational error in atomic function {func.__name__}: {e}")
            raise TransactionError("Database operation failed", original_error=e)
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in atomic function {func.__name__}: {e}")
            raise TransactionError("Database error", original_error=e)
        except Exception:
            db.rollback()
            raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
