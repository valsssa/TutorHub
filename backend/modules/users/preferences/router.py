"""User preferences API router."""

import logging

from core.datetime_utils import utc_now

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.rate_limiting import limiter
from core.timezone import is_valid_timezone
from database import get_db
from models import User
from schemas import UserPreferencesUpdate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/preferences", tags=["user-preferences"])


class TimezoneSync(BaseModel):
    """Request body for timezone sync endpoint."""

    detected_timezone: str

    @field_validator("detected_timezone")
    @classmethod
    def validate_timezone(cls, timezone_value: str) -> str:
        if not is_valid_timezone(timezone_value):
            raise ValueError(f"Invalid IANA timezone: {timezone_value}")
        return timezone_value


class TimezoneSyncResponse(BaseModel):
    """Response for timezone sync endpoint."""

    needs_update: bool
    saved_timezone: str
    detected_timezone: str


@router.patch("", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_preferences(
    request: Request,
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user preferences (timezone)."""
    logger.info(f"Updating preferences for user: {current_user.email}")

    if preferences.timezone:
        current_user.timezone = preferences.timezone
        logger.debug(f"Updated timezone to: {preferences.timezone}")

        # Update timestamp in application code (no DB triggers)
        from datetime import datetime

        current_user.updated_at = utc_now()

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        avatar_url=None,  # Will be fetched separately if needed
        currency=current_user.currency,
        timezone=current_user.timezone,
    )


@router.post("/sync-timezone", response_model=TimezoneSyncResponse)
@limiter.limit("30/minute")
async def sync_timezone(
    request: Request,
    sync_data: TimezoneSync,
    current_user: User = Depends(get_current_user),
):
    """
    Check if user's saved timezone differs from their detected browser timezone.
    Used on login to prompt user to update if timezone has changed.

    Returns whether an update is needed and both timezone values.
    """
    logger.info(
        f"Timezone sync check for user {current_user.email}: "
        f"saved={current_user.timezone}, detected={sync_data.detected_timezone}"
    )

    return TimezoneSyncResponse(
        needs_update=current_user.timezone != sync_data.detected_timezone,
        saved_timezone=current_user.timezone,
        detected_timezone=sync_data.detected_timezone,
    )
