"""
Notifications API Routes

Provides endpoints for:
- Listing user notifications
- Marking notifications as read/dismissed
- Getting unread count
- Managing notification preferences
"""

import logging
from datetime import UTC, datetime, time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.rate_limiting import limiter
from database import get_db
from models import Notification, User

from ..service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# Schemas
# ============================================================================


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: int
    type: str
    title: str
    message: str
    link: str | None = None
    is_read: bool
    category: str | None = None
    priority: int = 3
    action_url: str | None = None
    action_label: str | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    items: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Unread notification count response."""

    count: int


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""

    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    session_reminders_enabled: bool = True
    booking_requests_enabled: bool = True
    learning_nudges_enabled: bool = True
    review_prompts_enabled: bool = True
    achievements_enabled: bool = True
    marketing_enabled: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    preferred_notification_time: str | None = None
    max_daily_notifications: int = 10
    max_weekly_nudges: int = 3

    model_config = {"from_attributes": True}


class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences."""

    email_enabled: bool | None = None
    push_enabled: bool | None = None
    sms_enabled: bool | None = None
    session_reminders_enabled: bool | None = None
    booking_requests_enabled: bool | None = None
    learning_nudges_enabled: bool | None = None
    review_prompts_enabled: bool | None = None
    achievements_enabled: bool | None = None
    marketing_enabled: bool | None = None
    quiet_hours_start: str | None = Field(None, description="HH:MM format")
    quiet_hours_end: str | None = Field(None, description="HH:MM format")
    preferred_notification_time: str | None = Field(None, description="HH:MM format")
    max_daily_notifications: int | None = Field(None, ge=1, le=100)
    max_weekly_nudges: int | None = Field(None, ge=0, le=20)


# ============================================================================
# Notification Endpoints
# ============================================================================


@router.get("", response_model=NotificationListResponse)
@limiter.limit("30/minute")
async def list_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    unread_only: Annotated[bool, Query(description="Only show unread")] = False,
):
    """
    Get user's notifications with pagination.

    Returns notifications sorted by creation date (newest first).
    Dismissed notifications are excluded by default.
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.dismissed_at.is_(None),
    )

    if category:
        query = query.filter(Notification.category == category)

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.count()
    unread_count = notification_service.get_unread_count(db, current_user.id)

    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
@limiter.limit("60/minute")
async def get_unread_count(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get count of unread notifications."""
    count = notification_service.get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read")
@limiter.limit("30/minute")
async def mark_notification_read(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    success = notification_service.mark_as_read(db, notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db.commit()
    return {"message": "Marked as read"}


@router.patch("/mark-all-read")
@limiter.limit("10/minute")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    now = datetime.now(UTC)
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update({"is_read": True, "read_at": now})

    db.commit()
    return {"message": "All notifications marked as read"}


@router.patch("/{notification_id}/dismiss")
@limiter.limit("30/minute")
async def dismiss_notification(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dismiss a notification (hide without deleting).

    Dismissed notifications won't appear in the list but are kept for analytics.
    """
    success = notification_service.dismiss_notification(db, notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db.commit()
    return {"message": "Notification dismissed"}


@router.delete("/{notification_id}")
@limiter.limit("30/minute")
async def delete_notification(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a notification."""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted"}


# ============================================================================
# Preferences Endpoints
# ============================================================================


@router.get("/preferences", response_model=NotificationPreferencesResponse)
@limiter.limit("20/minute")
async def get_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's notification preferences."""
    prefs = notification_service.get_user_preferences(db, current_user.id)
    db.commit()  # Commit if new preferences were created

    # Convert time fields to strings
    response_dict = {
        "email_enabled": prefs.email_enabled,
        "push_enabled": prefs.push_enabled,
        "sms_enabled": prefs.sms_enabled,
        "session_reminders_enabled": prefs.session_reminders_enabled,
        "booking_requests_enabled": prefs.booking_requests_enabled,
        "learning_nudges_enabled": prefs.learning_nudges_enabled,
        "review_prompts_enabled": prefs.review_prompts_enabled,
        "achievements_enabled": prefs.achievements_enabled,
        "marketing_enabled": prefs.marketing_enabled,
        "quiet_hours_start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        "quiet_hours_end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
        "preferred_notification_time": (
            prefs.preferred_notification_time.strftime("%H:%M") if prefs.preferred_notification_time else None
        ),
        "max_daily_notifications": prefs.max_daily_notifications,
        "max_weekly_nudges": prefs.max_weekly_nudges,
    }

    return NotificationPreferencesResponse(**response_dict)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
@limiter.limit("10/minute")
async def update_notification_preferences(
    request: Request,
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's notification preferences."""
    # Parse time strings if provided
    update_data: dict[str, Any] = {}

    for field in [
        "email_enabled",
        "push_enabled",
        "sms_enabled",
        "session_reminders_enabled",
        "booking_requests_enabled",
        "learning_nudges_enabled",
        "review_prompts_enabled",
        "achievements_enabled",
        "marketing_enabled",
        "max_daily_notifications",
        "max_weekly_nudges",
    ]:
        value = getattr(preferences, field)
        if value is not None:
            update_data[field] = value

    # Handle time fields
    for time_field in ["quiet_hours_start", "quiet_hours_end", "preferred_notification_time"]:
        value = getattr(preferences, time_field)
        if value is not None:
            try:
                hours, minutes = map(int, value.split(":"))
                update_data[time_field] = time(hour=hours, minute=minutes)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid time format for {time_field}. Use HH:MM format.",
                )

    prefs = notification_service.update_preferences(db, current_user.id, **update_data)
    db.commit()

    logger.info(f"Updated notification preferences for user {current_user.id}")

    # Return updated preferences
    response_dict = {
        "email_enabled": prefs.email_enabled,
        "push_enabled": prefs.push_enabled,
        "sms_enabled": prefs.sms_enabled,
        "session_reminders_enabled": prefs.session_reminders_enabled,
        "booking_requests_enabled": prefs.booking_requests_enabled,
        "learning_nudges_enabled": prefs.learning_nudges_enabled,
        "review_prompts_enabled": prefs.review_prompts_enabled,
        "achievements_enabled": prefs.achievements_enabled,
        "marketing_enabled": prefs.marketing_enabled,
        "quiet_hours_start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        "quiet_hours_end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
        "preferred_notification_time": (
            prefs.preferred_notification_time.strftime("%H:%M") if prefs.preferred_notification_time else None
        ),
        "max_daily_notifications": prefs.max_daily_notifications,
        "max_weekly_nudges": prefs.max_weekly_nudges,
    }

    return NotificationPreferencesResponse(**response_dict)
