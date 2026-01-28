"""Audit trail API router."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from core.rate_limiting import limiter

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.dependencies import get_current_admin_user
from core.soft_delete import purge_old_soft_deletes, restore_user, soft_delete_user
from database import get_db
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: int
    table_name: str
    record_id: int
    action: str
    old_data: dict | None = None
    new_data: dict | None = None
    changed_by: int | None = None
    changed_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None


class SoftDeleteRequest(BaseModel):
    """Request to soft delete a user."""

    user_id: int
    reason: str | None = None


class RestoreRequest(BaseModel):
    """Request to restore a soft-deleted user."""

    user_id: int


class PurgeRequest(BaseModel):
    """Request to purge old soft-deleted records."""

    days_threshold: int = 90


@router.get("/logs", response_model=list[AuditLogResponse])
@limiter.limit("30/minute")
async def get_audit_logs(
    request: Request,
    table_name: str | None = None,
    record_id: int | None = None,
    action: str | None = None,
    user_id: int | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get audit logs with optional filters (admin only)."""
    logger.info(f"Admin {current_user.email} accessing audit logs")

    # Build query with parameterized conditions (safe from SQL injection)
    query_parts = ["SELECT * FROM audit_log WHERE 1=1"]
    params = {}

    if table_name:
        query_parts.append("AND table_name = :table_name")
        params["table_name"] = table_name

    if record_id:
        query_parts.append("AND record_id = :record_id")
        params["record_id"] = record_id

    if action:
        query_parts.append("AND action = :action")
        params["action"] = action

    if user_id:
        query_parts.append("AND changed_by = :user_id")
        params["user_id"] = user_id

    query_parts.append("ORDER BY changed_at DESC LIMIT :limit OFFSET :offset")
    params["limit"] = limit
    params["offset"] = offset

    # Join parts with spaces (safe - no user input in structure)
    query_string = " ".join(query_parts)

    try:
        result = db.execute(text(query_string), params)
        logs = []
        for row in result:
            logs.append(
                AuditLogResponse(
                    id=row[0],
                    table_name=row[1],
                    record_id=row[2],
                    action=row[3],
                    old_data=row[4],
                    new_data=row[5],
                    changed_by=row[6],
                    changed_at=row[7],
                    ip_address=row[8],
                    user_agent=row[9],
                )
            )
        return logs
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")


@router.post("/soft-delete-user")
@limiter.limit("10/minute")
async def soft_delete_user_endpoint(
    request: Request,
    data: SoftDeleteRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Soft delete a user (admin only)."""
    logger.info(f"Admin {current_user.email} soft deleting user {data.user_id}")

    try:
        soft_delete_user(db, data.user_id, current_user.id)
        return {"message": f"User {data.user_id} soft deleted successfully"}
    except Exception as e:
        logger.error(f"Error soft deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to soft delete user")


@router.post("/restore-user")
@limiter.limit("10/minute")
async def restore_user_endpoint(
    request: Request,
    data: RestoreRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Restore a soft-deleted user (admin only)."""
    logger.info(f"Admin {current_user.email} restoring user {data.user_id}")

    try:
        restore_user(db, data.user_id, current_user.id)
        return {"message": f"User {data.user_id} restored successfully"}
    except Exception as e:
        logger.error(f"Error restoring user: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore user")


@router.get("/deleted-users")
@limiter.limit("30/minute")
async def get_deleted_users(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of soft-deleted users (admin only)."""
    logger.info(f"Admin {current_user.email} accessing deleted users list")

    try:
        query = text(
            """
            SELECT id, email, role, deleted_at, deleted_by
            FROM users
            WHERE deleted_at IS NOT NULL
            ORDER BY deleted_at DESC
            """
        )
        result = db.execute(query)
        users = []
        for row in result:
            users.append(
                {
                    "id": row[0],
                    "email": row[1],
                    "role": row[2],
                    "deleted_at": row[3].isoformat() if row[3] else None,
                    "deleted_by": row[4],
                }
            )
        return users
    except Exception as e:
        logger.error(f"Error fetching deleted users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch deleted users")


@router.post("/purge-old-deletes")
@limiter.limit("5/hour")
async def purge_old_deletes_endpoint(
    request: Request,
    data: PurgeRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Permanently delete old soft-deleted records (admin only, GDPR compliance)."""
    logger.warning(f"Admin {current_user.email} purging soft deletes older than {data.days_threshold} days")

    try:
        results = purge_old_soft_deletes(db, data.days_threshold)
        return {
            "message": f"Purged records older than {data.days_threshold} days",
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error purging old soft deletes: {e}")
        raise HTTPException(status_code=500, detail="Failed to purge old soft deletes")
