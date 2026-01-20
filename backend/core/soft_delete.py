"""Soft delete utilities."""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: datetime | None = None
    deleted_by: int | None = None

    def soft_delete(self, deleted_by_id: int) -> None:
        """Mark record as soft deleted."""
        self.deleted_at = datetime.now(UTC)
        self.deleted_by = deleted_by_id

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None


def apply_soft_delete_filter(query, include_deleted: bool = False):
    """
    Apply soft delete filter to query.

    Args:
        query: SQLAlchemy query
        include_deleted: If True, include soft-deleted records

    Returns:
        Filtered query
    """
    if not include_deleted:
        # Assume the model has deleted_at column
        query = query.filter_by(deleted_at=None)
    return query


def soft_delete_user(db: Session, user_id: int, deleted_by_id: int) -> None:
    """
    Soft delete user and cascade to related records.

    Args:
        db: Database session
        user_id: User ID to soft delete
        deleted_by_id: ID of user performing the deletion
    """
    from sqlalchemy import text

    try:
        # Set PostgreSQL app context for audit trail (parameterized to prevent SQL injection)
        db.execute(
            text("SELECT set_config('app.current_user_id', :user_id, TRUE)"),
            {"user_id": str(deleted_by_id)},
        )

        # Call stored procedure
        db.execute(
            text("SELECT soft_delete_user(:user_id, :deleted_by)"),
            {"user_id": user_id, "deleted_by": deleted_by_id},
        )
        db.commit()

        logger.info(f"User {user_id} soft deleted by {deleted_by_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error soft deleting user {user_id}: {e}")
        raise


def restore_user(db: Session, user_id: int, restored_by_id: int) -> None:
    """
    Restore soft deleted user and related records.

    Args:
        db: Database session
        user_id: User ID to restore
        restored_by_id: ID of user performing the restoration
    """
    from sqlalchemy import text

    try:
        # Set PostgreSQL app context for audit trail (parameterized to prevent SQL injection)
        db.execute(
            text("SELECT set_config('app.current_user_id', :user_id, TRUE)"),
            {"user_id": str(restored_by_id)},
        )

        # Call stored procedure
        db.execute(
            text("SELECT restore_user(:user_id, :restored_by)"),
            {"user_id": user_id, "restored_by": restored_by_id},
        )
        db.commit()

        logger.info(f"User {user_id} restored by {restored_by_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error restoring user {user_id}: {e}")
        raise


def purge_old_soft_deletes(db: Session, days_threshold: int = 90) -> dict:
    """
    Permanently delete records that have been soft-deleted for longer than threshold.

    Args:
        db: Database session
        days_threshold: Number of days after which to purge (default 90)

    Returns:
        Dictionary with purge results
    """
    from sqlalchemy import text

    try:
        result = db.execute(
            text("SELECT * FROM purge_old_soft_deletes(:days)"),
            {"days": days_threshold},
        )

        purge_results = {row[0]: row[1] for row in result}
        db.commit()

        logger.info(f"Purged old soft deletes: {purge_results}")
        return purge_results
    except Exception as e:
        db.rollback()
        logger.error(f"Error purging old soft deletes: {e}")
        raise
