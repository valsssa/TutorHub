"""Audit logging system for tracking user decisions and data changes.

This module ensures audit logs are only recorded for actions that actually succeed.
It uses a deferred logging approach where audit data is collected during the request
and only written to the database after the main transaction commits successfully.
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from database import SessionLocal
from models import AuditLog

logger = logging.getLogger(__name__)


class DeferredAuditLog:
    """
    Container for audit log data that will be written after commit.

    This class holds the audit data and provides a method to write it
    to the database in a separate transaction after the main action commits.
    """

    def __init__(
        self,
        table_name: str,
        record_id: int,
        action: str,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
        changed_by: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        self.table_name = table_name
        self.record_id = record_id
        self.action = action
        self.old_data = old_data
        self.new_data = new_data
        self.changed_by = changed_by
        self.ip_address = ip_address
        self.user_agent = user_agent

    def write_to_db(self) -> None:
        """Write the audit log to database in a new session/transaction."""
        try:
            # Use a fresh session to avoid any transaction issues
            with SessionLocal() as new_session:
                old_data_json = json.dumps(self.old_data) if self.old_data else None
                new_data_json = json.dumps(self.new_data) if self.new_data else None

                audit_entry = AuditLog(
                    table_name=self.table_name,
                    record_id=self.record_id,
                    action=self.action,
                    old_data=old_data_json,
                    new_data=new_data_json,
                    changed_by=self.changed_by,
                    ip_address=self.ip_address,
                    user_agent=self.user_agent,
                )

                new_session.add(audit_entry)
                new_session.commit()

                logger.info(
                    f"Audit logged (post-commit): {self.action} on "
                    f"{self.table_name}#{self.record_id} by user#{self.changed_by}"
                )
        except Exception as e:
            logger.error(f"Failed to write deferred audit log: {e}")
            # Don't raise - audit failures shouldn't block business operations


class AuditLogger:
    """
    Central audit logging system for tracking all user decisions.

    This implementation ensures audit logs are only created for actions that
    actually succeed by deferring the log write until after commit.

    Two modes are available:
    1. Deferred logging (default, recommended): Uses post-commit hooks to ensure
       logs are only written after the main transaction succeeds.
    2. Immediate logging: Writes to the same transaction (legacy behavior,
       use only when you need the audit log ID immediately).
    """

    @staticmethod
    def _register_post_commit_handler(
        session: Session, deferred_log: DeferredAuditLog
    ) -> None:
        """
        Register a one-time post-commit handler to write the audit log.

        The handler is removed after execution to prevent memory leaks.
        """

        def write_after_commit(session: Session) -> None:
            """Write audit log after successful commit."""
            deferred_log.write_to_db()
            # Remove this listener after it fires (one-time use)
            event.remove(session, "after_commit", write_after_commit)

        # Register the handler - it will only fire once on commit
        event.listen(session, "after_commit", write_after_commit)

    @staticmethod
    def log_action(
        db: Session,
        table_name: str,
        record_id: int,
        action: str,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
        changed_by: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        immediate: bool = False,
    ) -> None:
        """
        Log an audit action.

        Following the "Store Decisions" philosophy: every log entry captures
        WHAT was decided, WHEN, and WHO made the decision.

        By default, uses deferred logging to ensure the audit log is only
        written after the main transaction commits successfully. This prevents
        recording actions that were rolled back.

        Args:
            db: Database session
            table_name: Name of the table being modified
            record_id: ID of the record
            action: Action type (INSERT, UPDATE, DELETE, SOFT_DELETE, RESTORE)
            old_data: Previous state of the record
            new_data: New state of the record
            changed_by: User ID who made the change
            ip_address: IP address of the request
            user_agent: User agent string
            immediate: If True, write to same transaction (legacy behavior).
                      If False (default), defer until after commit.
        """
        if immediate:
            # Legacy behavior: write in the same transaction
            AuditLogger._log_immediate(
                db=db,
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_data=old_data,
                new_data=new_data,
                changed_by=changed_by,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            # Deferred behavior: register post-commit handler
            deferred_log = DeferredAuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_data=old_data,
                new_data=new_data,
                changed_by=changed_by,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            AuditLogger._register_post_commit_handler(db, deferred_log)
            logger.debug(
                f"Audit log deferred: {action} on {table_name}#{record_id} "
                f"(will write after commit)"
            )

    @staticmethod
    def _log_immediate(
        db: Session,
        table_name: str,
        record_id: int,
        action: str,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
        changed_by: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Write audit log immediately in the current transaction.

        WARNING: This can record actions that are later rolled back.
        Use deferred logging (default) unless you specifically need
        the audit log to be part of the same transaction.
        """
        try:
            # Serialize data to JSON strings
            old_data_json = json.dumps(old_data) if old_data else None
            new_data_json = json.dumps(new_data) if new_data else None

            audit_entry = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_data=old_data_json,
                new_data=new_data_json,
                changed_by=changed_by,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(audit_entry)
            db.flush()  # Don't commit here - let the caller handle transaction

            logger.info(
                f"Audit logged (immediate): {action} on "
                f"{table_name}#{record_id} by user#{changed_by}"
            )
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            # Don't raise - audit failures shouldn't block business operations

    @staticmethod
    def log_booking_decision(
        db: Session,
        booking_id: int,
        action: str,
        user_id: int,
        old_status: str | None = None,
        new_status: str | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log a booking decision (confirmation, cancellation, completion).

        This captures the critical moment when a user makes a decision about a session.
        """
        AuditLogger.log_action(
            db=db,
            table_name="bookings",
            record_id=booking_id,
            action=action,
            old_data={"status": old_status} if old_status else None,
            new_data={"status": new_status, "reason": reason} if new_status else None,
            changed_by=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_profile_approval_decision(
        db: Session,
        tutor_profile_id: int,
        action: str,
        admin_id: int,
        old_status: str,
        new_status: str,
        rejection_reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Log tutor profile approval/rejection decisions.

        Critical for accountability: records WHO approved/rejected a tutor and WHY.
        """
        AuditLogger.log_action(
            db=db,
            table_name="tutor_profiles",
            record_id=tutor_profile_id,
            action=action,
            old_data={"status": old_status},
            new_data={
                "old_status": old_status,
                "new_status": new_status,
                "rejection_reason": rejection_reason,
                "decided_at": datetime.utcnow().isoformat(),
            },
            changed_by=admin_id,
            ip_address=ip_address,
        )

    @staticmethod
    def log_payment_decision(
        db: Session,
        package_id: int,
        user_id: int,
        amount: float,
        currency: str,
        payment_intent_id: str | None = None,
        status: str = "completed",
        ip_address: str | None = None,
    ) -> None:
        """
        Log payment transactions - critical financial decisions.

        Captures: WHO paid, HOW MUCH, WHEN, and for WHAT.
        """
        payment_data = {
            "amount": amount,
            "currency": currency,
            "payment_intent_id": payment_intent_id,
            "status": status,
            "paid_at": datetime.utcnow().isoformat(),
        }

        AuditLogger.log_action(
            db=db,
            table_name="student_packages",
            record_id=package_id,
            action="INSERT",
            new_data=payment_data,
            changed_by=user_id,
            ip_address=ip_address,
        )

    @staticmethod
    def log_availability_change(
        db: Session,
        tutor_profile_id: int,
        user_id: int,
        action: str,
        availability_data: dict[str, Any],
        reason: str | None = None,
    ) -> None:
        """
        Log tutor availability changes.

        Tracks WHEN tutors change their schedule and implicitly captures their
        decision about when they're willing to work.
        """
        data_with_context = {
            **availability_data,
            "reason": reason,
            "changed_at": datetime.utcnow().isoformat(),
        }

        AuditLogger.log_action(
            db=db,
            table_name="tutor_availabilities",
            record_id=tutor_profile_id,
            action=action,
            new_data=data_with_context,
            changed_by=user_id,
        )

    @staticmethod
    def log_soft_delete(
        db: Session,
        table_name: str,
        record_id: int,
        user_id: int,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Log soft delete operations.

        Critical for data governance: records WHO deleted WHAT and WHY.
        Never lose track of deletion decisions.
        """
        delete_data = {
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": user_id,
            "reason": reason,
        }

        AuditLogger.log_action(
            db=db,
            table_name=table_name,
            record_id=record_id,
            action="SOFT_DELETE",
            new_data=delete_data,
            changed_by=user_id,
            ip_address=ip_address,
        )

    @staticmethod
    def get_audit_trail(
        db: Session,
        table_name: str | None = None,
        record_id: int | None = None,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list:
        """
        Retrieve audit trail for analysis.

        Enables answering questions like:
        - What decisions did this user make?
        - What happened to this record over time?
        - Who made changes to this table?
        """
        query = db.query(AuditLog)

        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if record_id:
            query = query.filter(AuditLog.record_id == record_id)
        if user_id:
            query = query.filter(AuditLog.changed_by == user_id)

        return query.order_by(AuditLog.changed_at.desc()).limit(limit).all()
