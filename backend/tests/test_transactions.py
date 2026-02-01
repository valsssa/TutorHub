"""
Comprehensive tests for backend/core/transactions.py

Tests cover:
- TransactionError exception class
- transaction() context manager
- safe_commit() function
- commit_or_raise() function
- transactional() decorator (sync and async)
- with_savepoint() context manager
- atomic_operation() context manager
- atomic() decorator (sync and async)
- Error handling and rollback behavior
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from core.transactions import (
    TransactionError,
    atomic,
    atomic_operation,
    commit_or_raise,
    safe_commit,
    transaction,
    transactional,
    with_savepoint,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock(spec=Session)
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.begin_nested = MagicMock()
    return db


@pytest.fixture
def mock_savepoint():
    """Create a mock savepoint."""
    savepoint = MagicMock()
    savepoint.commit = MagicMock()
    savepoint.rollback = MagicMock()
    return savepoint


# =============================================================================
# Test: TransactionError Exception
# =============================================================================


class TestTransactionError:
    """Test TransactionError exception class."""

    def test_transaction_error_basic(self):
        """Test basic TransactionError creation."""
        error = TransactionError("Test error")

        assert error.message == "Test error"
        assert error.original_error is None
        assert str(error) == "Test error"

    def test_transaction_error_with_original(self):
        """Test TransactionError with original exception."""
        original = ValueError("Original error")
        error = TransactionError("Wrapped error", original_error=original)

        assert error.message == "Wrapped error"
        assert error.original_error == original

    def test_transaction_error_inheritance(self):
        """Test TransactionError is an Exception."""
        error = TransactionError("Test")

        assert isinstance(error, Exception)

        with pytest.raises(TransactionError):
            raise error


# =============================================================================
# Test: transaction() Context Manager
# =============================================================================


class TestTransactionContextManager:
    """Test the transaction() context manager."""

    def test_transaction_success(self, mock_db):
        """Test successful transaction commits."""
        with transaction(mock_db) as session:
            session.add(MagicMock())

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_transaction_yields_session(self, mock_db):
        """Test that transaction yields the database session."""
        with transaction(mock_db) as session:
            assert session == mock_db

    def test_transaction_integrity_error_rollback(self, mock_db):
        """Test IntegrityError causes rollback and raises TransactionError."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        with pytest.raises(TransactionError) as exc_info, transaction(mock_db):
            pass

        assert "integrity" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_transaction_operational_error_rollback(self, mock_db):
        """Test OperationalError causes rollback and raises TransactionError."""
        mock_db.commit.side_effect = OperationalError("stmt", {}, Exception())

        with pytest.raises(TransactionError) as exc_info, transaction(mock_db):
            pass

        assert "operation failed" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_transaction_sqlalchemy_error_rollback(self, mock_db):
        """Test generic SQLAlchemyError causes rollback and raises TransactionError."""
        mock_db.commit.side_effect = SQLAlchemyError("Generic error")

        with pytest.raises(TransactionError) as exc_info, transaction(mock_db):
            pass

        assert "database error" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_transaction_exception_in_body_rollback(self, mock_db):
        """Test exception in context body causes rollback."""
        with pytest.raises(ValueError), transaction(mock_db):
            raise ValueError("Test error in body")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_transaction_preserves_original_error(self, mock_db):
        """Test that original error is preserved in TransactionError."""
        original = IntegrityError("stmt", {}, Exception("unique constraint"))
        mock_db.commit.side_effect = original

        with pytest.raises(TransactionError) as exc_info, transaction(mock_db):
            pass

        assert exc_info.value.original_error == original


# =============================================================================
# Test: safe_commit() Function
# =============================================================================


class TestSafeCommit:
    """Test the safe_commit() function."""

    def test_safe_commit_success(self, mock_db):
        """Test successful commit returns True."""
        result = safe_commit(mock_db)

        assert result is True
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_safe_commit_integrity_error(self, mock_db):
        """Test IntegrityError returns False and rolls back."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        result = safe_commit(mock_db, error_message="Custom error")

        assert result is False
        mock_db.rollback.assert_called_once()

    def test_safe_commit_sqlalchemy_error(self, mock_db):
        """Test SQLAlchemyError returns False and rolls back."""
        mock_db.commit.side_effect = SQLAlchemyError("Database error")

        result = safe_commit(mock_db, error_message="Operation failed")

        assert result is False
        mock_db.rollback.assert_called_once()

    def test_safe_commit_custom_error_message(self, mock_db):
        """Test custom error message is used in logging."""
        mock_db.commit.side_effect = SQLAlchemyError("Error")

        with patch("core.transactions.logger") as mock_logger:
            safe_commit(mock_db, error_message="Custom error message")

        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0][0]
        assert "Custom error message" in call_args


# =============================================================================
# Test: commit_or_raise() Function
# =============================================================================


class TestCommitOrRaise:
    """Test the commit_or_raise() function."""

    def test_commit_or_raise_success(self, mock_db):
        """Test successful commit does not raise."""
        # Should not raise
        commit_or_raise(mock_db)

        mock_db.commit.assert_called_once()

    def test_commit_or_raise_integrity_error(self, mock_db):
        """Test IntegrityError raises HTTPException with 400 status."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        with pytest.raises(HTTPException) as exc_info:
            commit_or_raise(mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "integrity" in exc_info.value.detail.lower()
        mock_db.rollback.assert_called_once()

    def test_commit_or_raise_sqlalchemy_error_default_status(self, mock_db):
        """Test SQLAlchemyError raises HTTPException with default 500 status."""
        mock_db.commit.side_effect = SQLAlchemyError("Error")

        with pytest.raises(HTTPException) as exc_info:
            commit_or_raise(mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_db.rollback.assert_called_once()

    def test_commit_or_raise_custom_status(self, mock_db):
        """Test custom HTTP status code is used."""
        mock_db.commit.side_effect = SQLAlchemyError("Error")

        with pytest.raises(HTTPException) as exc_info:
            commit_or_raise(
                mock_db,
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_detail="Service unavailable",
            )

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc_info.value.detail == "Service unavailable"

    def test_commit_or_raise_custom_error_detail(self, mock_db):
        """Test custom error detail is used."""
        mock_db.commit.side_effect = SQLAlchemyError("Error")

        with pytest.raises(HTTPException) as exc_info:
            commit_or_raise(mock_db, error_detail="Custom error detail")

        assert exc_info.value.detail == "Custom error detail"


# =============================================================================
# Test: transactional() Decorator
# =============================================================================


class TestTransactionalDecorator:
    """Test the transactional() decorator."""

    def test_transactional_sync_success(self, mock_db):
        """Test transactional decorator with sync function success."""

        @transactional("Create item failed")
        def create_item(db: Session):
            db.add(MagicMock())
            db.commit()
            return {"id": 1}

        result = create_item(db=mock_db)

        assert result == {"id": 1}

    def test_transactional_sync_transaction_error(self, mock_db):
        """Test transactional decorator handles TransactionError."""

        @transactional("Failed to process")
        def failing_func(db: Session):
            raise TransactionError("Database failed")

        with pytest.raises(HTTPException) as exc_info:
            failing_func(db=mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to process"

    def test_transactional_sync_sqlalchemy_error(self, mock_db):
        """Test transactional decorator handles SQLAlchemyError."""

        @transactional("Database operation failed")
        def db_failing_func(db: Session):
            raise SQLAlchemyError("Connection lost")

        with pytest.raises(HTTPException) as exc_info:
            db_failing_func(db=mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Database operation failed"

    def test_transactional_sync_http_exception_passthrough(self, mock_db):
        """Test transactional decorator passes through HTTPException."""

        @transactional("Should not override")
        def http_raising_func(db: Session):
            raise HTTPException(status_code=404, detail="Not found")

        with pytest.raises(HTTPException) as exc_info:
            http_raising_func(db=mock_db)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not found"

    @pytest.mark.asyncio
    async def test_transactional_async_success(self, mock_db):
        """Test transactional decorator with async function success."""

        @transactional("Async operation failed")
        async def async_create_item(db: Session):
            db.add(MagicMock())
            return {"id": 2}

        result = await async_create_item(db=mock_db)

        assert result == {"id": 2}

    @pytest.mark.asyncio
    async def test_transactional_async_transaction_error(self, mock_db):
        """Test transactional decorator handles TransactionError in async."""

        @transactional("Async failed")
        async def async_failing_func(db: Session):
            raise TransactionError("Async database failed")

        with pytest.raises(HTTPException) as exc_info:
            await async_failing_func(db=mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Async failed"

    @pytest.mark.asyncio
    async def test_transactional_async_http_exception_passthrough(self, mock_db):
        """Test transactional decorator passes through HTTPException in async."""

        @transactional("Should not override")
        async def async_http_raising_func(db: Session):
            raise HTTPException(status_code=403, detail="Forbidden")

        with pytest.raises(HTTPException) as exc_info:
            await async_http_raising_func(db=mock_db)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Forbidden"

    def test_transactional_preserves_function_name(self, mock_db):
        """Test that decorator preserves the original function name."""

        @transactional("Error")
        def my_named_function(db: Session):
            return "result"

        assert my_named_function.__name__ == "my_named_function"


# =============================================================================
# Test: with_savepoint() Context Manager
# =============================================================================


class TestWithSavepoint:
    """Test the with_savepoint() context manager."""

    def test_savepoint_success(self, mock_db, mock_savepoint):
        """Test successful savepoint commits nested transaction."""
        mock_db.begin_nested.return_value = mock_savepoint

        with with_savepoint(mock_db, "test_savepoint") as session:
            session.add(MagicMock())

        mock_db.begin_nested.assert_called_once()
        mock_savepoint.commit.assert_called_once()
        mock_savepoint.rollback.assert_not_called()

    def test_savepoint_yields_session(self, mock_db, mock_savepoint):
        """Test that savepoint yields the database session."""
        mock_db.begin_nested.return_value = mock_savepoint

        with with_savepoint(mock_db) as session:
            assert session == mock_db

    def test_savepoint_rollback_on_error(self, mock_db, mock_savepoint):
        """Test savepoint rolls back on exception."""
        mock_db.begin_nested.return_value = mock_savepoint

        with pytest.raises(ValueError), with_savepoint(mock_db):
            raise ValueError("Error in nested transaction")

        mock_savepoint.rollback.assert_called_once()
        mock_savepoint.commit.assert_not_called()

    def test_savepoint_exception_propagates(self, mock_db, mock_savepoint):
        """Test that exceptions propagate after savepoint rollback."""
        mock_db.begin_nested.return_value = mock_savepoint

        with pytest.raises(RuntimeError), with_savepoint(mock_db):
            raise RuntimeError("Propagated error")


# =============================================================================
# Test: atomic_operation() Context Manager
# =============================================================================


class TestAtomicOperation:
    """Test the atomic_operation() context manager."""

    def test_atomic_operation_success(self, mock_db):
        """Test successful atomic operation commits."""
        with atomic_operation(mock_db) as session:
            session.add(MagicMock())

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_atomic_operation_yields_session(self, mock_db):
        """Test that atomic_operation yields the database session."""
        with atomic_operation(mock_db) as session:
            assert session == mock_db

    def test_atomic_operation_integrity_error(self, mock_db):
        """Test IntegrityError in atomic operation raises TransactionError."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        with pytest.raises(TransactionError) as exc_info, atomic_operation(mock_db):
            pass

        assert "integrity" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_atomic_operation_operational_error(self, mock_db):
        """Test OperationalError in atomic operation raises TransactionError."""
        mock_db.commit.side_effect = OperationalError("stmt", {}, Exception())

        with pytest.raises(TransactionError) as exc_info, atomic_operation(mock_db):
            pass

        assert "operation failed" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_atomic_operation_sqlalchemy_error(self, mock_db):
        """Test SQLAlchemyError in atomic operation raises TransactionError."""
        mock_db.commit.side_effect = SQLAlchemyError("Generic error")

        with pytest.raises(TransactionError) as exc_info, atomic_operation(mock_db):
            pass

        assert "database error" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_atomic_operation_general_exception(self, mock_db):
        """Test general exception in atomic operation body rolls back."""
        with pytest.raises(RuntimeError), atomic_operation(mock_db):
            raise RuntimeError("Unexpected error")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_atomic_operation_preserves_original_error(self, mock_db):
        """Test that original error is preserved in TransactionError."""
        original = IntegrityError("stmt", {}, Exception("fk violation"))
        mock_db.commit.side_effect = original

        with pytest.raises(TransactionError) as exc_info, atomic_operation(mock_db):
            pass

        assert exc_info.value.original_error == original


# =============================================================================
# Test: atomic() Decorator
# =============================================================================


class TestAtomicDecorator:
    """Test the atomic() decorator."""

    def test_atomic_sync_success(self, mock_db):
        """Test atomic decorator with sync function commits on success."""

        @atomic
        def create_user(db: Session):
            db.add(MagicMock())
            return {"user_id": 1}

        result = create_user(db=mock_db)

        assert result == {"user_id": 1}
        mock_db.commit.assert_called_once()

    def test_atomic_sync_integrity_error(self, mock_db):
        """Test atomic decorator handles IntegrityError."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        @atomic
        def failing_create(db: Session):
            db.add(MagicMock())
            return {"id": 1}

        with pytest.raises(TransactionError) as exc_info:
            failing_create(db=mock_db)

        assert "integrity" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    def test_atomic_sync_operational_error(self, mock_db):
        """Test atomic decorator handles OperationalError."""
        mock_db.commit.side_effect = OperationalError("stmt", {}, Exception())

        @atomic
        def db_op(db: Session):
            return "result"

        with pytest.raises(TransactionError) as exc_info:
            db_op(db=mock_db)

        assert "operation failed" in exc_info.value.message.lower()

    def test_atomic_sync_http_exception_rollback(self, mock_db):
        """Test atomic decorator rolls back on HTTPException."""

        @atomic
        def http_error_func(db: Session):
            raise HTTPException(status_code=400, detail="Bad request")

        with pytest.raises(HTTPException) as exc_info:
            http_error_func(db=mock_db)

        assert exc_info.value.status_code == 400
        mock_db.rollback.assert_called_once()

    def test_atomic_sync_general_exception_rollback(self, mock_db):
        """Test atomic decorator rolls back on general exception."""

        @atomic
        def error_func(db: Session):
            raise ValueError("Value error")

        with pytest.raises(ValueError):
            error_func(db=mock_db)

        mock_db.rollback.assert_called_once()

    def test_atomic_sync_no_db_parameter(self):
        """Test atomic decorator raises ValueError without db parameter."""

        @atomic
        def no_db_func():
            return "result"

        with pytest.raises(ValueError) as exc_info:
            no_db_func()

        assert "db" in str(exc_info.value).lower()

    def test_atomic_sync_db_in_positional_args(self, mock_db):
        """Test atomic decorator finds db in positional args."""

        @atomic
        def with_positional_db(first_arg, db):
            db.add(MagicMock())
            return first_arg

        result = with_positional_db("test", mock_db)

        assert result == "test"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_async_success(self, mock_db):
        """Test atomic decorator with async function commits on success."""

        @atomic
        async def async_create_user(db: Session):
            db.add(MagicMock())
            return {"user_id": 2}

        result = await async_create_user(db=mock_db)

        assert result == {"user_id": 2}
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_async_integrity_error(self, mock_db):
        """Test atomic decorator handles IntegrityError in async function."""
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception())

        @atomic
        async def async_failing_create(db: Session):
            db.add(MagicMock())
            return {"id": 1}

        with pytest.raises(TransactionError) as exc_info:
            await async_failing_create(db=mock_db)

        assert "integrity" in exc_info.value.message.lower()
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_async_http_exception_rollback(self, mock_db):
        """Test atomic decorator rolls back on HTTPException in async."""

        @atomic
        async def async_http_error(db: Session):
            raise HTTPException(status_code=404, detail="Not found")

        with pytest.raises(HTTPException) as exc_info:
            await async_http_error(db=mock_db)

        assert exc_info.value.status_code == 404
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_async_no_db_parameter(self):
        """Test atomic decorator raises ValueError without db in async."""

        @atomic
        async def async_no_db():
            return "result"

        with pytest.raises(ValueError) as exc_info:
            await async_no_db()

        assert "db" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_atomic_async_db_in_positional_args(self, mock_db):
        """Test atomic decorator finds db in positional args for async."""

        @atomic
        async def async_with_positional(first_arg, db):
            db.add(MagicMock())
            return first_arg

        result = await async_with_positional("async_test", mock_db)

        assert result == "async_test"
        mock_db.commit.assert_called_once()

    def test_atomic_preserves_function_name(self, mock_db):
        """Test that atomic decorator preserves the original function name."""

        @atomic
        def my_atomic_function(db: Session):
            return "result"

        assert my_atomic_function.__name__ == "my_atomic_function"

    @pytest.mark.asyncio
    async def test_atomic_async_preserves_function_name(self, mock_db):
        """Test that atomic decorator preserves async function name."""

        @atomic
        async def my_async_atomic_function(db: Session):
            return "result"

        assert my_async_atomic_function.__name__ == "my_async_atomic_function"


# =============================================================================
# Test: Integration Scenarios
# =============================================================================


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple transaction utilities."""

    def test_nested_savepoint_in_transaction(self, mock_db, mock_savepoint):
        """Test using savepoint inside a transaction context."""
        mock_db.begin_nested.return_value = mock_savepoint

        with transaction(mock_db):
            mock_db.add(MagicMock())
            mock_db.flush()

            with with_savepoint(mock_db, "nested"):
                mock_db.add(MagicMock())

        mock_db.commit.assert_called_once()
        mock_savepoint.commit.assert_called_once()

    def test_savepoint_rollback_outer_continues(self, mock_db, mock_savepoint):
        """Test that savepoint rollback doesn't affect outer transaction."""
        mock_db.begin_nested.return_value = mock_savepoint

        with transaction(mock_db):
            mock_db.add(MagicMock())

            try:
                with with_savepoint(mock_db):
                    raise ValueError("Nested error")
            except ValueError:
                pass  # Catch and continue

            # Outer transaction should still work
            mock_db.add(MagicMock())

        mock_db.commit.assert_called_once()
        mock_savepoint.rollback.assert_called_once()

    def test_transactional_with_atomic_operation(self, mock_db):
        """Test combining transactional decorator with atomic_operation."""

        @transactional("Combined operation failed")
        def combined_operation(db: Session):
            with atomic_operation(db):
                db.add(MagicMock())
            return {"success": True}

        result = combined_operation(db=mock_db)

        assert result == {"success": True}
        # atomic_operation commits
        mock_db.commit.assert_called()
