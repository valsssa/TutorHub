"""Notifications API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from models import User
from schemas import NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=List[NotificationResponse])
@limiter.limit("20/minute")
async def list_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's notifications."""
    from models import Notification

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return notifications


@router.patch("/{notification_id}/read")
@limiter.limit("20/minute")
async def mark_notification_read(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notification as read."""
    from models import Notification

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.patch("/mark-all-read")
@limiter.limit("5/minute")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    from models import Notification

    try:
        db.query(Notification).filter(
            Notification.user_id == current_user.id, Notification.is_read.is_(False)
        ).update({"is_read": True})
        db.commit()
        return {"message": "All notifications marked as read"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to mark notifications as read"
        )


@router.delete("/{notification_id}")
@limiter.limit("20/minute")
async def delete_notification(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    from models import Notification

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted"}
