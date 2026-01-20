"""Audit logging system for tracking user decisions and data changes."""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """Central audit logging system for tracking all user decisions."""

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
    ) -> None:
        """
        Log an audit action.

        Following the "Store Decisions" philosophy: every log entry captures
        WHAT was decided, WHEN, and WHO made the decision.

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

            logger.info(f"Audit logged: {action} on {table_name}#{record_id} by user#{changed_by}")
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
